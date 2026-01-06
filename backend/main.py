# backend/main.py
import os
from fastapi import FastAPI, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from io import BytesIO
import logging
import json

from backend.rag import build_vector_store, retrieve_chunks
from backend.llm import generate
from backend.ocr import extract_text_from_pdf_bytes, ocr_pdf_bytes, clean_ocr_text
from backend.rate_limit import allow_request
from backend.schemas import QueryPayload, FillFormPayload

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

app = FastAPI(title="RAG Doc-QA (Certificate Analyzer)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

vector_index = None
doc_chunks: List[dict] = []


def _safe_parse_json(raw: str):
    """Try to extract and parse JSON from a possibly noisy model response.

    Returns the parsed Python object on success or None on failure.
    Strategies tried (in order):
    - direct json.loads on the whole string
    - strip surrounding Markdown code fences (```json / ```)
    - find the first JSON object/array in the text (non-greedy)
    - remove trailing commas inside the found JSON and retry
    """
    if not raw:
        return None
    raw = raw.strip()
    import re
    import json as _json

    raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.I)
    raw = re.sub(r"\s*```$", "", raw)

    try:
        return _json.loads(raw)
    except Exception:
        pass

    m = re.search(r"(\{(?:.|\s)*?\}|\[(?:.|\s)*?\])", raw, flags=re.S)
    if m:
        candidate = m.group(1)
        try:
            return _json.loads(candidate)
        except Exception:
            candidate2 = re.sub(r",\s*([}\]])", r"\1", candidate)
            try:
                return _json.loads(candidate2)
            except Exception:
                return None

    return None


@app.get("/")
def root():
    return {"status": "ok", "message": "RAG system running (certificate mode)"}


@app.post("/upload")
async def upload(file: UploadFile):
    """
    Upload PDF or plain text. Returns number of chunks indexed.
    """
    global vector_index, doc_chunks
    raw = await file.read()
    pages = []

    filename = (file.filename or "").lower()
    if filename.endswith(".pdf"):
        pages = extract_text_from_pdf_bytes(raw)
        total_chars = sum(len(p.get("text", "")) for p in pages)
        if total_chars < 200:
            try:
                ocr_pages = ocr_pdf_bytes(raw, dpi=300, psm=6)
                if ocr_pages:
                    pages = ocr_pages
            except Exception as e:
                logger.warning("OCR failed or not available: %s", e)
    else:
        try:
            txt = raw.decode("utf-8", errors="ignore")
            pages = [{"page": 1, "text": txt}]
        except Exception:
            raise HTTPException(status_code=400, detail="Failed to decode text file")

    if not pages:
        raise HTTPException(status_code=400, detail="File empty or unreadable (pdf text + OCR failed)")

    for p in pages:
        p["text"] = clean_ocr_text(p.get("text", ""))

    try:
        vector_index, doc_chunks = build_vector_store(pages)
    except Exception as e:
        logger.exception("Failed to build vector store: %s", e)
        raise HTTPException(status_code=500, detail="Indexing failed")

    return {"message": "document indexed", "num_chunks": len(doc_chunks)}


@app.post("/analyze/certificate")
def analyze_certificate(payload: QueryPayload, request: Request):
    """
    Specialized extraction endpoint for certificates.
    Expects a document already uploaded (so vector_index is present).
    The payload.question can be used to give contextual instructions (optional).
    """
    global vector_index, doc_chunks

    client_ip = request.client.host or "unknown"
    if not allow_request(client_ip):
        raise HTTPException(status_code=429, detail="rate limit exceeded")

    if vector_index is None or not doc_chunks:
        raise HTTPException(status_code=400, detail="Upload a document first")

    retrieved = retrieve_chunks(vector_index, doc_chunks, payload.question or "extract certificate fields", k=payload.top_k)
    context_texts = [r["text"] for r in retrieved]

    context_block = "\n\n".join(context_texts)

    prompt = f"""
    You are a document analyzer specialized in Indian government-style certificates.

    INSTRUCTIONS:
    - Extract the following fields and return STRICT JSON ONLY (no extra text).
    - If a field is not present or not readable, set it to null.
    - If the field is present but ambiguous, return the best guess and add a "confidence" subfield if possible.

    Fields to extract:
    - person_name
    - father_name
    - date_of_birth
    - category_or_caste
    - certificate_type
    - issuing_authority
    - issue_date
    - document_number

    Context:
    {context_block}
    """

    raw_answer = generate(prompt, retrieved_texts=context_texts) or ""

    if not raw_answer.strip():
        return {
            "parsed": None,
            "raw": raw_answer,
            "error": "LLM returned empty response",
            "context": context_texts,
        }

    parsed = _safe_parse_json(raw_answer)

    if parsed is None:
        for line in (ln.strip() for ln in raw_answer.splitlines() if ln.strip()):
            parsed = _safe_parse_json(line)
            if parsed is not None:
                break

    if parsed is None:
        return {"parsed": None, "raw": raw_answer, "context": context_texts}

    return {"parsed": parsed, "raw": raw_answer, "context": context_texts}


@app.post("/query")
def query(payload: QueryPayload, request: Request):
    global vector_index, doc_chunks

    client_ip = request.client.host or "unknown"
    if not allow_request(client_ip):
        raise HTTPException(status_code=429, detail="rate limit exceeded")

    if vector_index is None or not doc_chunks:
        raise HTTPException(status_code=400, detail="Upload a document first")

    retrieved = retrieve_chunks(vector_index, doc_chunks, payload.question, payload.top_k)
    context_texts = [r["text"] for r in retrieved]
    context_block = "\n\n".join(context_texts)

    prompt = f"""
    You are a helpful document assistant. Use only the provided context to answer.
    If the answer is not in the document, say "Not mentioned in document".

    Context:
    {context_block}

    Question:
    {payload.question}
    """

    answer = generate(prompt, retrieved_texts=context_texts)
    answer = answer.replace("\\n", "\n").strip()

    sources = []
    for r in retrieved:
        excerpt = r["text"].replace("\n", " ").strip()
        if len(excerpt) > 300:
            excerpt = excerpt[:300].rsplit(" ", 1)[0] + "..."
        sources.append({"page": r.get("page"), "excerpt": excerpt})

    return {"answer": answer, "sources": sources}


@app.post("/fill-form")
def fill_form(payload: FillFormPayload, request: Request):
    """
    Fill given fields from the currently indexed document.
    """
    global vector_index, doc_chunks
    client_ip = request.client.host or "unknown"
    if not allow_request(client_ip):
        raise HTTPException(status_code=429, detail="rate limit exceeded")

    if vector_index is None or not doc_chunks:
        raise HTTPException(status_code=400, detail="Upload a document first")

    retrieved = retrieve_chunks(vector_index, doc_chunks, " ".join(payload.fields), payload.top_k)
    context_texts = [r["text"] for r in retrieved]
    context_block = "\n\n".join(context_texts)

    fields_block = "\n".join(f"- {f}" for f in payload.fields)

    prompt = f"""
    You are a form-filling assistant. Extract the following fields and return STRICT JSON with these keys:
    {fields_block}

    Context:
    {context_block}

    If a field is missing or unreadable, use null.
    """

    raw = generate(prompt, retrieved_texts=context_texts) or ""

    if not raw.strip():
        return {"result": None, "raw": raw, "error": "LLM returned empty response", "context": context_texts}

    parsed = _safe_parse_json(raw)

    if parsed is None:
        for line in (ln.strip() for ln in raw.splitlines() if ln.strip()):
            parsed = _safe_parse_json(line)
            if parsed is not None:
                break

    return {"result": parsed, "raw": raw, "context": context_texts}
