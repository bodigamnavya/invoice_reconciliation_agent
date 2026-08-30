import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Config:
    """Backend Application Configuration."""
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.getenv("SECRET_KEY", "enterprise_finance_reconciliation_super_secret_2026")
    FLASK_ENV = os.getenv("FLASK_ENV", "development")
    PORT = int(os.getenv("PORT", 5000))
    
    IS_SERVERLESS = bool(os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"))
    # Database Configuration
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/invoice_reconciliation")
    # SQLite fallback path for local zero-config development when PostgreSQL is not initialized
    SQLITE_FALLBACK_PATH = Path("/tmp/reconciliation.db") if IS_SERVERLESS else BASE_DIR / "database" / "reconciliation.db"
    
    # LLM Settings
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "rule-based").lower()
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_MODEL = os.getenv("LLM_MODEL", "gemini-1.5-flash")
    
    # Uploads
    UPLOAD_FOLDER = Path("/tmp/uploads") if IS_SERVERLESS else BASE_DIR / os.getenv("UPLOAD_FOLDER", "backend/uploads")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)) # 16 MB
    ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "webp"}
    
    # Matching and tolerance parameters
    PRICE_TOLERANCE_PERCENT = float(os.getenv("PRICE_TOLERANCE_PERCENT", 0.01)) # 1%
    PRICE_TOLERANCE_ABSOLUTE = float(os.getenv("PRICE_TOLERANCE_ABSOLUTE", 5.00)) # ₹5.00
    
    # JWT Settings
    JWT_EXPIRATION_HOURS = 24

# Ensure upload directory exists
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
