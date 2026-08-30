import logging
from backend.config import Config
from backend.models.payment_model import Payment

logger = logging.getLogger("PaymentAgent")

class PaymentAgent:
    """Agent responsible for banking transaction discovery and payment reconciliation."""

    @classmethod
    def match_invoice_with_payment(cls, invoice_data: dict, po_id: int, db_session) -> dict:
        """
        Scans payment ledger to identify matching disbursements and reconciles payment status.
        """
        invoice_number = (invoice_data.get("invoice_number") or "").strip()
        po_number = (invoice_data.get("po_number") or "").strip()
        vendor_name = (invoice_data.get("vendor_name") or "").strip()
        invoice_total = float(invoice_data.get("total_amount", 0.0))

        # 1. Search payment by exact invoice number
        matched_payment = None
        if invoice_number:
            matched_payment = db_session.query(Payment).filter(
                Payment.invoice_number.ilike(invoice_number)
            ).first()

        # 2. Search payment by PO reference
        if not matched_payment and po_number:
            matched_payment = db_session.query(Payment).filter(
                Payment.po_number.ilike(po_number)
            ).first()

        # 3. Search payment by PO ID
        if not matched_payment and po_id:
            matched_payment = db_session.query(Payment).filter(
                Payment.po_id == po_id
            ).first()

        # 4. Search by vendor name and close amount
        if not matched_payment and vendor_name and invoice_total > 0:
            matched_payment = db_session.query(Payment).filter(
                Payment.vendor_name.ilike(f"%{vendor_name}%")
            ).order_by(Payment.payment_date.desc()).first()

        if not matched_payment:
            return {
                "payment_match_status": "UNPAID",
                "matched_payment": None,
                "payment_id": None,
                "payment_reference": None,
                "amount_paid": 0.0,
                "amount_difference": round(invoice_total, 2),
                "details": "No transaction found in payment ledger for this invoice."
            }

        amount_paid = float(matched_payment.amount_paid)

        # If invoice total is 0 due to extraction error, avoid declaring overpayment
        if invoice_total <= 0:
            return {
                "payment_match_status": "UNPAID",
                "matched_payment": matched_payment,
                "payment_id": matched_payment.id,
                "payment_reference": matched_payment.payment_reference,
                "amount_paid": amount_paid,
                "amount_difference": 0.0,
                "details": f"Payment of ₹{amount_paid:,.2f} on file, but invoice amount is unverified (₹0.00)."
            }

        diff = round(amount_paid - invoice_total, 2)
        tolerance = max(Config.PRICE_TOLERANCE_ABSOLUTE, invoice_total * Config.PRICE_TOLERANCE_PERCENT)

        if abs(diff) <= tolerance:
            status = "FULL_PAYMENT"
            details = f"Exact payment verified: ₹{amount_paid:,.2f} disbursed under ref {matched_payment.payment_reference}."
        elif amount_paid < invoice_total:
            status = "PARTIAL_PAYMENT"
            details = f"Partial payment detected: Paid ₹{amount_paid:,.2f}, remaining unpaid balance is ₹{abs(diff):,.2f}."
        else:
            status = "OVERPAYMENT"
            details = f"Overpayment detected: Paid ₹{amount_paid:,.2f}, exceeds invoice by ₹{diff:,.2f}."

        return {
            "payment_match_status": status,
            "matched_payment": matched_payment,
            "payment_id": matched_payment.id,
            "payment_reference": matched_payment.payment_reference,
            "amount_paid": amount_paid,
            "amount_difference": diff,
            "details": details
        }
