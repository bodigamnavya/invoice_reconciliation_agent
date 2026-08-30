import os
import io
import logging

logger = logging.getLogger("PDFService")

def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extracts text from a PDF file using PyMuPDF (fitz).
    If native text is empty/scanned, renders PDF pages as images and runs Tesseract OCR.
    """
    if not os.path.exists(pdf_path):
        logger.error(f"PDF file does not exist at {pdf_path}")
        return ""
    
    extracted_text = []
    has_sufficient_text = False

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
            
            full_text = "\n".join(extracted_text).strip()
            if len(full_text) >= 20:
                has_sufficient_text = True
                doc.close()
                return full_text
            
            # If native text extraction is empty/insufficient, perform OCR by rendering pages
            logger.info("PDF has insufficient embedded text. Attempting page rendering and OCR.")
            ocr_text = []
            try:
                import pytesseract
                from PIL import Image

                for page_num in range(len(doc)):
                    page = doc.load_page(page_num)
                    # Render page to high-res image (2x scale)
                    pix = page.get_pixmap(dpi=200)
                    img = Image.open(io.BytesIO(pix.tobytes("png")))
                    txt = pytesseract.image_to_string(img)
                    if txt:
                        ocr_text.append(txt)
                
                doc.close()
                if ocr_text:
                    return "\n".join(ocr_text).strip()
            except Exception as ocr_err:
                logger.warning(f"PyMuPDF OCR rendering failed or pytesseract not installed: {ocr_err}")
                doc.close()
        except Exception as e:
            logger.warning(f"PyMuPDF processing failed on {pdf_path}: {e}")

    # Fallback reading ASCII strings directly
    try:
        with open(pdf_path, "r", errors="ignore") as f:
            raw = f.read()
            if len(raw) > 30:
                extracted_text.append(raw)
    except Exception:
        pass

    return "\n".join(extracted_text).strip()
