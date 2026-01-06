# RAG Certificate Analyzer

> Quick, messy, and functional  a local RAG (Retrieval-Augmented Generation) tool to analyze Indian-style certificates, ask questions about any uploaded document, and auto-fill form fields.

## What is this
This repo contains:
- `backend/` : FastAPI app that handles PDF/text upload, OCR fallback, vector indexing (sentence-transformers), and document QA endpoints.
- `frontend/` : Next.js app (simple client) to upload docs and call the backend endpoints for:
  - `/upload`
  - `/analyze/certificate`
  - `/query`
  - `/fill-form`

This project uses local LLM workflow logic (Groq / deterministic fallback depending on local config). No hosted paid LLM required out of the box.

### Backend
```
# create venv and install
python -m venv venv
venv\Scripts\activate    # windows
# or: source venv/bin/activate  # mac/linux

pip install -r requirements.txt

# run
uvicorn backend.main:app --reload
# backend listens on http://127.0.0.1:8000 by default

uvicorn backend.main:app --reload
# backend listens on http://127.0.0.1:8000 by default
```

Notes

>If OCR is needed, install pytesseract and Tesseract engine; pdf2image requires poppler.

>If sentence-transformers are used, CPU is fine but it will be slower.

### Frontend
```
cd frontend
npm install
npm run dev
```


## License

MIT — do whatever, but don’t blame me for the bugs.
le .env.example.

Dockerize backend + frontend for a single deploy target.
