import datetime
from functools import wraps
import jwt
import bcrypt
from flask import request, jsonify
from backend.config import Config
from backend.models.database import SessionLocal
from backend.models.user_model import User

def hash_password(password: str) -> str:
    """Hashes plain password using bcrypt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")

def check_password(password: str, hashed_password: str) -> bool:
    """Verifies plain password against hashed string."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def generate_jwt_token(user_id: int, email: str, role: str) -> str:
    """Generates a JWT token for the user."""
    payload = {
        "user_id": user_id,
        "email": email,
        "role": role,
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=Config.JWT_EXPIRATION_HOURS),
        "iat": datetime.datetime.utcnow()
    }
    token = jwt.encode(payload, Config.SECRET_KEY, algorithm="HS256")
    return token

def decode_jwt_token(token: str):
    """Decodes and validates a JWT token."""
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def token_required(f):
    """Decorator to require JWT authentication on API endpoints."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        # Check Authorization header
        if "Authorization" in request.headers:
            auth_header = request.headers["Authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]
            else:
                token = auth_header
        
        if not token:
            return jsonify({"success": False, "message": "Authentication token is missing."}), 401
        
        payload = decode_jwt_token(token)
        if not payload:
            return jsonify({"success": False, "message": "Token is invalid or expired."}), 401
        
        # Load user from db
        db = SessionLocal()
        try:
            current_user = db.query(User).filter(User.id == payload["user_id"], User.is_active == True).first()
            if not current_user:
                return jsonify({"success": False, "message": "User not found or inactive."}), 401
            # Pass user to function if accepted
            return f(current_user, *args, **kwargs)
        finally:
            db.close()

    return decorated
