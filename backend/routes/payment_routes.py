from flask import Blueprint, jsonify
from backend.models.database import SessionLocal
from backend.models.payment_model import Payment
from backend.models.purchase_order_model import PurchaseOrder

payment_bp = Blueprint("payments_vendors", __name__, url_prefix="/api")

@payment_bp.route("/payments", methods=["GET"])
def list_payments():
    """Retrieve all payment records from ledger."""
    db = SessionLocal()
    try:
        payments = db.query(Payment).order_by(Payment.payment_date.desc()).all()
        return jsonify({
            "success": True,
            "count": len(payments),
            "payments": [p.to_dict() for p in payments]
        }), 200
    finally:
        db.close()


@payment_bp.route("/purchase-orders", methods=["GET"])
def list_purchase_orders():
    """Retrieve all registered purchase orders."""
    db = SessionLocal()
    try:
        pos = db.query(PurchaseOrder).order_by(PurchaseOrder.po_date.desc()).all()
        return jsonify({
            "success": True,
            "count": len(pos),
            "purchase_orders": [po.to_dict() for po in pos]
        }), 200
    finally:
        db.close()
