import logging
from backend.config import Config
from backend.models.purchase_order_model import PurchaseOrder

logger = logging.getLogger("MatchingAgent")

class MatchingAgent:
    """Agent responsible for 2-way / 3-way matching between Invoices and Purchase Orders."""

    @classmethod
    def match_invoice_with_po(cls, invoice_data: dict, db_session) -> dict:
        """
        Executes deterministic matching logic against database Purchase Orders.
        """
        invoice_po_number = (invoice_data.get("po_number") or "").strip()
        vendor_name = (invoice_data.get("vendor_name") or "").strip()
        invoice_total = float(invoice_data.get("total_amount", 0.0))
        
        # 1. Search for PO by exact PO number
        matched_po = None
        if invoice_po_number:
            matched_po = db_session.query(PurchaseOrder).filter(
                PurchaseOrder.po_number.ilike(invoice_po_number)
            ).first()

        # 2. Fallback search by vendor name and close amount if PO# missing
        if not matched_po and vendor_name:
            matched_po = db_session.query(PurchaseOrder).filter(
                PurchaseOrder.vendor_name.ilike(f"%{vendor_name}%")
            ).order_by(PurchaseOrder.created_at.desc()).first()

        if not matched_po:
            return {
                "po_match_status": "NOT_FOUND",
                "matched_po": None,
                "po_id": None,
                "po_number": None,
                "po_amount": 0.0,
                "amount_difference": 0.0,
                "mismatch_details": ["No matching Purchase Order found in system for this vendor/PO number."]
            }

        po_total = float(matched_po.total_amount)
        amount_diff = round(invoice_total - po_total, 2)
        abs_diff = abs(amount_diff)
        
        # Calculate tolerance
        max_allowed_diff = max(
            Config.PRICE_TOLERANCE_ABSOLUTE,
            po_total * Config.PRICE_TOLERANCE_PERCENT
        )

        mismatches = []
        
        # Check Vendor name matching
        if vendor_name and matched_po.vendor_name:
            if vendor_name.lower() not in matched_po.vendor_name.lower() and matched_po.vendor_name.lower() not in vendor_name.lower():
                mismatches.append(f"Vendor mismatch: Invoice quotes '{vendor_name}' but PO #{matched_po.po_number} is registered to '{matched_po.vendor_name}'.")

        # Check Amount tolerance
        if abs_diff > max_allowed_diff:
            direction = "exceeds" if invoice_total > po_total else "is less than"
            mismatches.append(f"Amount mismatch: Invoice total (₹{invoice_total:,.2f}) {direction} PO total (₹{po_total:,.2f}) by ₹{abs_diff:,.2f}.")

        po_match_status = "MISMATCH" if len(mismatches) > 0 else "MATCHED"

        return {
            "po_match_status": po_match_status,
            "matched_po": matched_po,
            "po_id": matched_po.id,
            "po_number": matched_po.po_number,
            "po_amount": po_total,
            "amount_difference": amount_diff,
            "mismatch_details": mismatches
        }
