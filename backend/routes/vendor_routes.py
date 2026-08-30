import numpy as np
from flask import Blueprint, jsonify, request
from sqlalchemy import func
from backend.models.database import SessionLocal
from backend.models.vendor_model import Vendor
from backend.models.invoice_model import Invoice
from backend.models.reconciliation_model import ReconciliationResult

vendor_bp = Blueprint("vendors", __name__, url_prefix="/api/vendors")

def calculate_vendor_metrics(vendor: Vendor, db_session) -> dict:
    """Calculates live deterministic risk score and breakdown metrics for a vendor from PostgreSQL records."""
    invoices = db_session.query(Invoice).filter(
        (Invoice.vendor_id == vendor.id) | (Invoice.vendor_name.ilike(f"%{vendor.name}%"))
    ).all()

    total_invoices = len(invoices)
    invoice_ids = [inv.id for inv in invoices]

    reconciliations = []
    if invoice_ids:
        reconciliations = db_session.query(ReconciliationResult).filter(
            ReconciliationResult.invoice_id.in_(invoice_ids)
        ).all()

    matched_count = 0
    review_count = 0
    high_risk_count = 0
    reject_count = 0
    duplicate_count = 0
    anomaly_count = 0
    mismatch_count = 0

    for r in reconciliations:
        if r.status == "MATCHED":
            matched_count += 1
        elif r.status == "REVIEW_REQUIRED":
            review_count += 1
        elif r.status == "HIGH_RISK":
            high_risk_count += 1
        elif r.status == "REJECT":
            reject_count += 1

        if r.duplicate_status == "DUPLICATE_FOUND":
            duplicate_count += 1
        if r.anomaly_status == "ANOMALY_DETECTED":
            anomaly_count += 1
        if r.po_match_status == "MISMATCH" or r.payment_match_status in ["PARTIAL_PAYMENT", "OVERPAYMENT"]:
            mismatch_count += 1

    amounts = [float(inv.total_amount) for inv in invoices if inv.total_amount is not None]
    total_value = round(sum(amounts), 2)
    average_value = round(float(np.mean(amounts)), 2) if amounts else 0.0

    # Deterministic Vendor Risk Score Calculation (0-100)
    # Weights: High-Risk Invoices (+35), Duplicates (+45), Anomalies (+35), PO/Payment Mismatches (+20)
    if total_invoices > 0:
        penalty_points = (
            (high_risk_count * 35) +
            (reject_count * 45) +
            (duplicate_count * 45) +
            (anomaly_count * 35) +
            (mismatch_count * 20)
        )
        calculated_score = min(100, max(0, int(round(penalty_points / total_invoices))))
    else:
        calculated_score = 0

    # If vendor has High Risk base rating in directory, ensure minimum baseline of 25
    if vendor.risk_rating == "HIGH" and calculated_score < 25:
        calculated_score = 25

    # Categorize Risk Level: 0–24 LOW, 25–49 MEDIUM, 50–74 HIGH, 75–100 CRITICAL
    if calculated_score >= 75:
        risk_level = "CRITICAL"
    elif calculated_score >= 50:
        risk_level = "HIGH"
    elif calculated_score >= 25:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "total_invoices": total_invoices,
        "matched_count": matched_count,
        "review_count": review_count,
        "high_risk_count": high_risk_count,
        "reject_count": reject_count,
        "duplicate_count": duplicate_count,
        "anomaly_count": anomaly_count,
        "mismatch_count": mismatch_count,
        "total_value": total_value,
        "average_value": average_value,
        "vendor_risk_score": calculated_score,
        "risk_level": risk_level
    }

@vendor_bp.route("", methods=["GET"])
def list_vendors():
    """Lists all vendors with live dynamically calculated risk scores and invoice statistics."""
    db = SessionLocal()
    try:
        vendors = db.query(Vendor).all()
        vendor_list = []
        for v in vendors:
            metrics = calculate_vendor_metrics(v, db)
            v_dict = v.to_dict()
            v_dict.update(metrics)
            vendor_list.append(v_dict)

        return jsonify({
            "success": True,
            "count": len(vendor_list),
            "vendors": vendor_list
        }), 200
    finally:
        db.close()

@vendor_bp.route("/<int:vendor_id>/profile", methods=["GET"])
def get_vendor_profile(vendor_id: int):
    """Returns comprehensive Vendor Risk Profile with historical metrics and compliance standing."""
    db = SessionLocal()
    try:
        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            return jsonify({"success": False, "error": "Vendor not found."}), 404

        metrics = calculate_vendor_metrics(vendor, db)
        profile_data = vendor.to_dict()
        profile_data.update(metrics)

        return jsonify({
            "success": True,
            "vendor": profile_data
        }), 200
    finally:
        db.close()

@vendor_bp.route("/<int:vendor_id>/history", methods=["GET"])
def get_vendor_history(vendor_id: int):
    """Returns full historical invoices and reconciliation results for a vendor."""
    db = SessionLocal()
    try:
        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            return jsonify({"success": False, "error": "Vendor not found."}), 404

        invoices = db.query(Invoice).filter(
            (Invoice.vendor_id == vendor.id) | (Invoice.vendor_name.ilike(f"%{vendor.name}%"))
        ).order_by(Invoice.created_at.desc()).all()

        history_items = []
        for inv in invoices:
            recon = db.query(ReconciliationResult).filter(ReconciliationResult.invoice_id == inv.id).first()
            item = inv.to_dict()
            item["reconciliation"] = recon.to_dict() if recon else None
            history_items.append(item)

        return jsonify({
            "success": True,
            "vendor_name": vendor.name,
            "count": len(history_items),
            "invoices": history_items
        }), 200
    finally:
        db.close()

@vendor_bp.route("/<int:vendor_id>/analytics", methods=["GET"])
def get_vendor_analytics(vendor_id: int):
    """Returns analytics distribution counts for Chart.js visualization."""
    db = SessionLocal()
    try:
        vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
        if not vendor:
            return jsonify({"success": False, "error": "Vendor not found."}), 404

        metrics = calculate_vendor_metrics(vendor, db)
        
        return jsonify({
            "success": True,
            "analytics": {
                "matched": metrics["matched_count"],
                "review_required": metrics["review_count"],
                "high_risk": metrics["high_risk_count"],
                "rejected": metrics["reject_count"],
                "total_invoices": metrics["total_invoices"],
                "total_value": metrics["total_value"],
                "average_value": metrics["average_value"],
                "risk_score": metrics["vendor_risk_score"],
                "risk_level": metrics["risk_level"]
            }
        }), 200
    finally:
        db.close()
