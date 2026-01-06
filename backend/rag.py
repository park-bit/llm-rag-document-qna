
from typing import List, Dict, Union
import numpy as np
import faiss
from backend.embeddings import get_embedding

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50

def chunk_text(text: str, page: Union[int, None], chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    chunks = []
    start = 0
    L = len(text)
    while start < L:
        end = min(start + chunk_size, L)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append({"text": chunk, "page": page})
        start = end - overlap
        if start < 0:
            start = 0
        if end == L:
            break
    return chunks

def build_vector_store(pages: Union[str, List[Dict]]):
    """
    pages: either raw string OR list of dicts {"page": int, "text": str}
    returns (faiss_index, chunks_list)
      - chunks_list: list of {"text":..., "page":...}
    """
    if isinstance(pages, str):
        pages = [{"page": None, "text": pages}]

    all_chunks = []
    for p in pages:
        txt = p.get("text", "")
        page = p.get("page", None)
        if txt and txt.strip():
            all_chunks.extend(chunk_text(txt, page))

    if not all_chunks:
        raise ValueError("No text available to index")

    embeddings = [get_embedding(c["text"]) for c in all_chunks]
    mat = np.vstack(embeddings).astype("float32")
    dim = mat.shape[1]

    index = faiss.IndexFlatL2(dim)
    index.add(mat)

    return index, all_chunks

def retrieve_chunks(index, chunks: List[Dict], query: str, k: int = 3):
    """
    Returns up to k chunk dicts (each has 'text' and 'page') most similar to query.
    """
    if index is None or len(chunks) == 0:
        return []

    qv = get_embedding(query).reshape(1, -1).astype("float32")
    k = min(k, len(chunks))
    distances, indices = index.search(qv, k)
    found = []
    for i in indices[0]:
        if 0 <= i < len(chunks):
            found.append(chunks[i])
    return found
