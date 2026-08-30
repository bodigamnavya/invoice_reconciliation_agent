from flask import Blueprint, request, jsonify
from backend.models.database import SessionLocal
from backend.models.user_model import User
from backend.utils.security import hash_password, check_password, generate_jwt_token, token_required
from backend.utils.validators import validate_registration

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

@auth_bp.route("/register", methods=["POST"])
def register():
    """Register a new finance user."""
    data = request.get_json() or {}
    is_valid, err_msg = validate_registration(data)
    if not is_valid:
        return jsonify({"success": False, "message": err_msg}), 400

    db = SessionLocal()
    try:
        email = data["email"].strip().lower()
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            return jsonify({"success": False, "message": "A user with this email already exists."}), 409

        hashed = hash_password(data["password"])
        new_user = User(
            full_name=data["full_name"].strip(),
            email=email,
            password_hash=hashed,
            role=data.get("role", "Finance Analyst")
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        token = generate_jwt_token(new_user.id, new_user.email, new_user.role)
        return jsonify({
            "success": True,
            "message": "User registered successfully.",
            "token": token,
            "user": new_user.to_dict()
        }), 201
    except Exception as e:
        db.rollback()
        return jsonify({"success": False, "message": f"Server error: {str(e)}"}), 500
    finally:
        db.close()

@auth_bp.route("/login", methods=["POST"])
def login():
    """Authenticate user and return JWT token."""
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required."}), 400

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user or not check_password(password, user.password_hash):
            return jsonify({"success": False, "message": "Invalid email or password."}), 401

        if not user.is_active:
            return jsonify({"success": False, "message": "Account is disabled. Please contact administrator."}), 403

        token = generate_jwt_token(user.id, user.email, user.role)
        return jsonify({
            "success": True,
            "message": "Login successful.",
            "token": token,
            "user": user.to_dict()
        }), 200
    finally:
        db.close()

@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Client-side token invalidate acknowledgement."""
    return jsonify({"success": True, "message": "Logged out successfully."}), 200

@auth_bp.route("/me", methods=["GET"])
@token_required
def get_current_user(current_user):
    """Retrieve logged-in user profile details."""
    return jsonify({
        "success": True,
        "user": current_user.to_dict()
    }), 200
