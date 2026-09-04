import os
import io
import logging

logger = logging.getLogger("PDFService")

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text from a PDF file.
    Strategy:
    1. Try PyMuPDF (fitz) if installed (local dev / Render — lazy import)
    2. Fallback to pypdf (lightweight, works on Vercel serverless)
    3. Raw ASCII fallback
    """
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file does not exist at {pdf_path}")
        return ""

    extracted_text = []

    # --- Strategy 1: PyMuPDF (best quality, only on local/Render) ---
    fitz = None
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            fitz = None

    if fitz:
        try:
            doc = fitz.open(pdf_path)
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                text = page.get_text("text")
                if text and len(text.strip()) > 10:
                    extracted_text.append(text)
            doc.close()
            full_text = "\n".join(extracted_text).strip()
            if len(full_text) >= 20:
                return full_text
        except Exception as e:
            logger.warning(f"PyMuPDF processing failed on {pdf_path}: {e}")
        extracted_text = []  # reset for next strategy

    # --- Strategy 2: pypdf (lightweight, Vercel-safe; PyPI package: pypdf>=4) ---
    try:
        from pypdf import PdfReader  # modern pypdf package (PyPI: pypdf>=4)
    except ImportError:
        try:
            from PyPDF2 import PdfReader
        except ImportError:
            PdfReader = None

    if PdfReader:
        try:
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                text = page.extract_text()
                if text and len(text.strip()) > 10:
                    extracted_text.append(text)
            full_text = "\n".join(extracted_text).strip()
            if len(full_text) >= 20:
                return full_text
        except Exception as e:
            logger.warning(f"pypdf text extraction failed on {pdf_path}: {e}")
        extracted_text = []

    # --- Strategy 3: Raw ASCII fallback ---
    try:
        with open(pdf_path, "r", errors="ignore") as f:
            raw = f.read()
            if len(raw) > 30:
                extracted_text.append(raw)
    except Exception:
        pass

    return "\n".join(extracted_text).strip()
