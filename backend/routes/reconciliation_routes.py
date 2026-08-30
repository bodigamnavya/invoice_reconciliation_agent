from flask import Blueprint, request, jsonify, Response
from backend.models.database import SessionLocal
from backend.models.reconciliation_model import ReconciliationResult
from backend.models.invoice_model import Invoice
from backend.services.reconciliation_service import ReconciliationService
from backend.services.report_service import ReportService
from backend.utils.security import decode_jwt_token

reconciliation_bp = Blueprint("reconciliation", __name__, url_prefix="/api")

def _get_user_id_from_request(req):
    auth_header = req.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        payload = decode_jwt_token(token)
        if payload:
            return payload.get("user_id")
    return None

@reconciliation_bp.route("/reconciliation/<int:invoice_id>/run", methods=["POST"])
def trigger_reconciliation(invoice_id: int):
    """Triggers the full multi-agent reconciliation pipeline for an invoice."""
    db = SessionLocal()
    try:
        recon_result = ReconciliationService.run_reconciliation(invoice_id, db)
        return jsonify({
            "success": True,
            "message": "Reconciliation completed.",
            "reconciliation": recon_result.to_dict()
        }), 200
    except ValueError as ve:
        return jsonify({"success": False, "message": str(ve)}), 404
    except Exception as e:
        return jsonify({"success": False, "message": f"Pipeline execution failed: {str(e)}"}), 500
    finally:
        db.close()

@reconciliation_bp.route("/reconciliation/<int:invoice_id>", methods=["GET"])
def get_reconciliation_result(invoice_id: int):
    """Fetches reconciliation analysis, risk metrics, and AI recommendations."""
    db = SessionLocal()
    try:
        recon = db.query(ReconciliationResult).filter(
            ReconciliationResult.invoice_id == invoice_id
        ).first()

        if not recon:
            # If no result exists yet, automatically run it
            try:
                recon = ReconciliationService.run_reconciliation(invoice_id, db)
            except Exception:
                return jsonify({"success": False, "message": "Reconciliation record not found."}), 404

        recon_dict = recon.to_dict()
        recon_dict["audit_trail"] = ReconciliationService.get_explainable_audit_trail(recon)

        return jsonify({
            "success": True,
            "reconciliation": recon_dict
        }), 200
    finally:
        db.close()

@reconciliation_bp.route("/reconciliation/<int:invoice_id>/audit-trail", methods=["GET"])
def get_reconciliation_audit_trail(invoice_id: int):
    """Returns the dedicated explainable AI audit trail and event timeline."""
    db = SessionLocal()
    try:
        recon = db.query(ReconciliationResult).filter(
            ReconciliationResult.invoice_id == invoice_id
        ).first()

        if not recon:
            try:
                recon = ReconciliationService.run_reconciliation(invoice_id, db)
            except Exception:
                return jsonify({"success": False, "message": "Reconciliation record not found."}), 404

        audit_trail = ReconciliationService.get_explainable_audit_trail(recon)
        return jsonify({
            "success": True,
            "invoice_id": invoice_id,
            "audit_trail": audit_trail
        }), 200
    finally:
        db.close()

@reconciliation_bp.route("/reconciliation/<int:invoice_id>/report", methods=["GET"])
def generate_reconciliation_report(invoice_id: int):
    """Generates and downloads a professional reconciliation audit report in PDF format."""
    db = SessionLocal()
    try:
        recon = db.query(ReconciliationResult).filter(
            ReconciliationResult.invoice_id == invoice_id
        ).first()

        if not recon:
            try:
                recon = ReconciliationService.run_reconciliation(invoice_id, db)
            except Exception:
                return jsonify({"success": False, "message": "Reconciliation record not found."}), 404

        pdf_bytes = ReportService.generate_audit_report_pdf(recon)
        inv_num = recon.invoice.invoice_number if recon.invoice else f"INV-{invoice_id}"
        clean_inv_num = "".join(c for c in inv_num if c.isalnum() or c in "-_")
        filename = f"reconciliation_audit_report_{clean_inv_num}.pdf"

        return Response(
            pdf_bytes,
            mimetype="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "application/pdf"
            }
        )
    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to generate audit report: {str(e)}"}), 500
    finally:
        db.close()

@reconciliation_bp.route("/reconciliation/<int:invoice_id>/approve", methods=["POST"])
def approve_reconciliation(invoice_id: int):
    """Approve invoice reconciliation and mark closed."""
    data = request.get_json() or {}
    notes = data.get("notes", "Approved by finance officer.")
    user_id = _get_user_id_from_request(request)

    db = SessionLocal()
    try:
        recon = ReconciliationService.apply_human_action(invoice_id, "APPROVED", user_id, notes, db)
        return jsonify({
            "success": True,
            "message": "Invoice reconciliation marked as APPROVED.",
            "reconciliation": recon.to_dict()
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400
    finally:
        db.close()

@reconciliation_bp.route("/reconciliation/<int:invoice_id>/review", methods=["POST"])
def flag_review_reconciliation(invoice_id: int):
    """Flags invoice for senior finance controller review."""
    data = request.get_json() or {}
    notes = data.get("notes", "Escalated for detailed manual audit.")
    user_id = _get_user_id_from_request(request)

    db = SessionLocal()
    try:
        recon = ReconciliationService.apply_human_action(invoice_id, "REVIEWED", user_id, notes, db)
        return jsonify({
            "success": True,
            "message": "Invoice reconciliation marked for REVIEW.",
            "reconciliation": recon.to_dict()
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400
    finally:
        db.close()

@reconciliation_bp.route("/reconciliation/<int:invoice_id>/reject", methods=["POST"])
def reject_reconciliation(invoice_id: int):
    """Rejects invoice due to discrepancies, duplicate detection, or anomaly."""
    data = request.get_json() or {}
    notes = data.get("notes", "Rejected due to policy non-compliance / duplicate detection.")
    user_id = _get_user_id_from_request(request)

    db = SessionLocal()
    try:
        recon = ReconciliationService.apply_human_action(invoice_id, "REJECTED", user_id, notes, db)
        return jsonify({
            "success": True,
            "message": "Invoice reconciliation REJECTED.",
            "reconciliation": recon.to_dict()
        }), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 400
    finally:
        db.close()

@reconciliation_bp.route("/history", methods=["GET"])
def get_reconciliation_history():
    """Lists reconciliation history with filtering, searching, and status sorting."""
    status_filter = request.args.get("status")
    risk_filter = request.args.get("risk_level")
    search_query = request.args.get("search", "").strip()

    db = SessionLocal()
    try:
        query = db.query(ReconciliationResult).join(Invoice)

        if status_filter and status_filter != "ALL":
            query = query.filter(ReconciliationResult.status == status_filter)

        if risk_filter and risk_filter != "ALL":
            query = query.filter(ReconciliationResult.risk_level == risk_filter)

        if search_query:
            query = query.filter(
                (Invoice.invoice_number.ilike(f"%{search_query}%")) |
                (Invoice.vendor_name.ilike(f"%{search_query}%")) |
                (Invoice.po_number.ilike(f"%{search_query}%"))
            )

        results = query.order_by(ReconciliationResult.created_at.desc()).all()
        return jsonify({
            "success": True,
            "count": len(results),
            "history": [r.to_dict() for r in results]
        }), 200
    finally:
        db.close()
