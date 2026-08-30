import os
import sys
from pathlib import Path

# Ensure root directory is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import logging
from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
from backend.config import Config
from backend.models.database import init_db, engine, SessionLocal
from backend.routes.auth_routes import auth_bp
from backend.routes.dashboard_routes import dashboard_bp
from backend.routes.invoice_routes import invoice_bp
from backend.routes.reconciliation_routes import reconciliation_bp
from backend.routes.payment_routes import payment_bp
from backend.routes.vendor_routes import vendor_bp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("InvoiceReconciliationApp")

def create_app():
    """Application Factory for Flask Backend."""
    frontend_dir = os.path.join(Config.BASE_DIR, "frontend")
    app = Flask(__name__, static_folder=frontend_dir, static_url_path="")
    app.config.from_object(Config)

    # Enable Cross-Origin Resource Sharing
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    # Initialize Database Schema & Tables
    with app.app_context():
        try:
            init_db()
            db = SessionLocal()
            from backend.models.user_model import User
            if db.query(User).count() == 0:
                logger.info("Empty database detected. Auto-seeding demo scenarios...")
                from database.seed_data import seed_database
                seed_database()
            db.close()
        except Exception as e:
            logger.error(f"Database initialization error: {e}")

    # Register API Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(invoice_bp)
    app.register_blueprint(reconciliation_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(vendor_bp)

    # Health Check Endpoints
    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({
            "status": "healthy",
            "service": "Invoice-to-Payment Reconciliation Agent API",
            "llm_provider": Config.LLM_PROVIDER,
            "version": "1.0.0"
        }), 200

    @app.route("/db-health", methods=["GET"])
    def db_health_check():
        try:
            with engine.connect() as conn:
                db_driver = engine.url.drivername
                return jsonify({
                    "status": "connected",
                    "database_dialect": db_driver,
                    "engine_url": str(engine.url).split("@")[-1] if "@" in str(engine.url) else str(engine.url)
                }), 200
        except Exception as e:
            return jsonify({
                "status": "disconnected",
                "error": str(e)
            }), 500

    # Serve Frontend Single Page App / Static Assets
    @app.route("/")
    def serve_index():
        return send_from_directory(frontend_dir, "index.html")

    @app.route("/<path:path>")
    def serve_static_page(path):
        target_path = os.path.join(frontend_dir, path)
        if os.path.exists(target_path):
            return send_from_directory(frontend_dir, path)
        # Check if .html extension was omitted
        if os.path.exists(f"{target_path}.html"):
            return send_from_directory(frontend_dir, f"{path}.html")
        return send_from_directory(frontend_dir, "index.html")

    # Global Error Handlers
    @app.errorhandler(404)
    def handle_not_found(e):
        if request.path.startswith("/api/"):
            return jsonify({"success": False, "message": "Resource or endpoint not found."}), 404
        return send_from_directory(frontend_dir, "index.html")

    @app.errorhandler(413)
    def handle_large_file(e):
        return jsonify({"success": False, "message": "File exceeds maximum allowable upload size (16MB)."}), 413

    @app.errorhandler(500)
    def handle_server_error(e):
        return jsonify({"success": False, "message": "An internal server error occurred."}), 500

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting Reconciliation Agent Server on http://localhost:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
