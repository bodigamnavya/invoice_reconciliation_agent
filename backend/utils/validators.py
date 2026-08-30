import re
from backend.config import Config

EMAIL_REGEX = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

def is_valid_email(email: str) -> bool:
    """Validate email format."""
    if not email:
        return False
    return bool(re.match(EMAIL_REGEX, email.strip()))

def is_allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    if not filename or "." not in filename:
        return False
    ext = filename.rsplit(".", 1)[1].lower()
    return ext in Config.ALLOWED_EXTENSIONS

def validate_registration(data: dict) -> tuple[bool, str]:
    """Validate user registration inputs."""
    if not data:
        return False, "Request payload is empty."
    
    full_name = data.get("full_name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    
    if not full_name or len(full_name) < 2:
        return False, "Full name must be at least 2 characters."
    
    if not is_valid_email(email):
        return False, "Please enter a valid email address."
    
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters."
    
    return True, ""

def validate_invoice_upload(file_obj) -> tuple[bool, str]:
    """Validate uploaded invoice file."""
    if not file_obj or file_obj.filename == "":
        return False, "No file was selected for upload."
    
    if not is_allowed_file(file_obj.filename):
        allowed = ", ".join(Config.ALLOWED_EXTENSIONS)
        return False, f"File format not supported. Allowed formats: {allowed}"
    
    return True, ""
