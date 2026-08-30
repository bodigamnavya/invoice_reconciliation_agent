import os
import logging
from backend.services.pdf_service import extract_text_from_pdf

logger = logging.getLogger("OCRService")

def extract_text_from_file(file_path: str) -> str:
    """
    Extracts text from PDF or image formats (PNG, JPG, JPEG, WEBP).
    For PDF, invokes PDF service. For images, uses PIL + Tesseract OCR.
    """
    if not os.path.exists(file_path):
        return ""
    
    ext = file_path.rsplit(".", 1)[-1].lower() if "." in file_path else ""
    
    if ext == "pdf":
        return extract_text_from_pdf(file_path)
    
    # Image files (png, jpg, jpeg, webp)
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)
        if text and len(text.strip()) > 5:
            return text.strip()
    except Exception as e:
        logger.info(f"Pytesseract not configured or failed on image ({e}).")
    
    return ""
