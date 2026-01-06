import re
from io import BytesIO

def clean_ocr_text(text: str) -> str:
    """
    Basic post-processing to improve OCR output quality.
    Drop weird characters, normalize spaces, remove repeated underscores.
    """
    if not text:
        return ""
    text = text.replace("_", " ")
    text = re.sub(r"[^\x00-\x7F]+", " ", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"-\s*\n\s*", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = "\n".join(line.strip() for line in text.splitlines())
    return text.strip()

def extract_text_from_pdf_bytes(raw_bytes: bytes, use_pdfminer=False, ocr_dpi=300, ocr_psm=6):
    """
    Try PyPDF2 text extraction first; if resulting length is low, caller may choose OCR.
    Returns list of pages dicts: {"page": int, "text": str}
    Note: OCR requires poppler (pdftoppm) and tesseract installed on the host or available in PATH.
    """
    pages = []
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(BytesIO(raw_bytes))
        for i, page in enumerate(reader.pages):
            try:
                t = page.extract_text() or ""
            except Exception:
                t = ""
            if t and t.strip():
                pages.append({"page": i+1, "text": t})
    except Exception:
        return []

    return pages

def ocr_pdf_bytes(raw_bytes: bytes, dpi=300, psm=6):
    """
    Uses pdf2image + pytesseract to OCR each page.
    Returns list of pages dicts: {"page": int, "text": str}
    """
    try:
        from pdf2image import convert_from_bytes
        import pytesseract
    except Exception as e:
        raise RuntimeError("pdf2image/pytesseract required for OCR: " + str(e))

    images = convert_from_bytes(raw_bytes, dpi=dpi)
    pages = []
    for i, img in enumerate(images):
        txt = pytesseract.image_to_string(img, config=f"--psm {psm}")
        txt = clean_ocr_text(txt)
        if txt and txt.strip():
            pages.append({"page": i+1, "text": txt})
    return pages
