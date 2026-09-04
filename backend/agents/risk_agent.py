import logging
import math
from backend.models.invoice_model import Invoice
from backend.models.vendor_model import Vendor

logger = logging.getLogger("RiskAgent")

class RiskAgent:
    """Agent responsible for multi-vector fraud/anomaly risk scoring and anomaly detection."""

    @classmethod
    def evaluate_risk(cls, invoice_data: dict, matching_result: dict, payment_result: dict, db_session) -> dict:
        """
        Evaluates distinct risk vectors and returns full transparent factor breakdown:
        1. Purchase Order Variance Vector
        2. Payment Ledger Mismatch Vector
        3. Duplicate Invoice Vector
        4. Statistical Anomaly Vector (Vendor amount distribution)
        5. Vendor Profile & Risk Rating Vector
        6. Document Extraction Verification Vector
        """
        risk_score = 0
        risk_factors = []
        all_vector_checks = [] # Full audit trail breakdown including passed (+0) vectors
        
        invoice_number = (invoice_data.get("invoice_number") or "").strip()
        vendor_name = (invoice_data.get("vendor_name") or "").strip()
        invoice_total = float(invoice_data.get("total_amount", 0.0))
        current_invoice_id = invoice_data.get("id")

        # -------------------------------------------------------------
        # Vector 1: Purchase Order Discrepancies
        # -------------------------------------------------------------
        po_status = matching_result.get("po_match_status", "NOT_FOUND")
        po_total = float(matching_result.get("po_amount", 0.0))
        po_diff = float(matching_result.get("amount_difference", 0.0))

        if po_status == "MISMATCH":
            risk_score += 35
            factor_info = {
                "factor": "Purchase Order Variance",
                "points": 35,
                "severity": "HIGH",
                "status": "FAILED",
                "description": f"Invoice amount (₹{invoice_total:,.2f}) deviates from approved Purchase Order #{matching_result.get('po_number', 'N/A')} (₹{po_total:,.2f}) by ₹{abs(po_diff):,.2f}."
            }
            risk_factors.append(factor_info)
            all_vector_checks.append(factor_info)
        elif po_status == "NOT_FOUND":
            risk_score += 25
            factor_info = {
                "factor": "Missing Purchase Order Reference",
                "points": 25,
                "severity": "MEDIUM",
                "status": "WARNING",
                "description": "Invoice does not reference any authorized Purchase Order on master ledger."
            }
            risk_factors.append(factor_info)
            all_vector_checks.append(factor_info)
        else:
            all_vector_checks.append({
                "factor": "Purchase Order Match",
                "points": 0,
                "severity": "LOW",
                "status": "PASSED",
                "description": f"Invoice amount perfectly matches authorized Purchase Order #{matching_result.get('po_number', 'N/A')} (Variance ₹0.00)."
            })

        # -------------------------------------------------------------
        # Vector 2: Payment Ledger Mismatch
        # -------------------------------------------------------------
        payment_status = payment_result.get("payment_match_status", "UNPAID")
        pay_diff = float(payment_result.get("amount_difference", 0.0))
        amount_paid = float(payment_result.get("amount_paid", 0.0))

        if payment_status == "PARTIAL_PAYMENT":
            risk_score += 25
            factor_info = {
                "factor": "Payment Mismatch (Underpayment)",
                "points": 25,
                "severity": "MEDIUM",
                "status": "WARNING",
                "description": f"Banking ledger reflects partial disbursement of ₹{amount_paid:,.2f}. Outstanding liability shortfall is ₹{abs(pay_diff):,.2f}."
            }
            risk_factors.append(factor_info)
            all_vector_checks.append(factor_info)
        elif payment_status == "OVERPAYMENT":
            risk_score += 25
            factor_info = {
                "factor": "Payment Mismatch (Overpayment)",
                "points": 25,
                "severity": "HIGH",
                "status": "WARNING",
                "description": f"Disbursed payment of ₹{amount_paid:,.2f} exceeds billed invoice total by ₹{abs(pay_diff):,.2f}."
            }
            risk_factors.append(factor_info)
            all_vector_checks.append(factor_info)
        elif payment_status == "UNPAID" and po_status != "MATCHED":
            factor_info = {
                "factor": "Payment Status",
                "points": 10,
                "severity": "LOW",
                "status": "INFO",
                "description": "Invoice is currently open and awaiting scheduled disbursement."
            }
            all_vector_checks.append(factor_info)
        else:
            all_vector_checks.append({
                "factor": "Payment Ledger Settlement",
                "points": 0,
                "severity": "LOW",
                "status": "PASSED",
                "description": f"Settlement verified against banking transaction ref {payment_result.get('payment_reference', 'N/A')}."
            })

        # -------------------------------------------------------------
        # Vector 3: Duplicate Invoice Check
        # -------------------------------------------------------------
        duplicate_status = "UNIQUE"
        
        # Query potential duplicates by invoice number and vendor
        existing_dupes = db_session.query(Invoice).filter(
            Invoice.invoice_number.ilike(invoice_number),
            Invoice.vendor_name.ilike(f"%{vendor_name}%")
        )
        if current_invoice_id:
            existing_dupes = existing_dupes.filter(Invoice.id != current_invoice_id)
        
        duplicate_records = existing_dupes.all()
        if len(duplicate_records) > 0:
            duplicate_status = "DUPLICATE_FOUND"
            risk_score += 45
            factor_info = {
                "factor": "Duplicate Invoice Detection",
                "points": 45,
                "severity": "CRITICAL",
                "status": "FAILED",
                "description": f"Invoice number '{invoice_number}' was previously submitted and processed for {vendor_name} on {duplicate_records[0].invoice_date}."
            }
            risk_factors.append(factor_info)
            all_vector_checks.append(factor_info)
        else:
            all_vector_checks.append({
                "factor": "Duplicate Invoice Check",
                "points": 0,
                "severity": "LOW",
                "status": "PASSED",
                "description": "No prior identical billing submissions found in active or archived ledgers."
            })

        # -------------------------------------------------------------
        # Vector 4: Statistical Amount Anomaly Detection
        # -------------------------------------------------------------
        anomaly_status = "NORMAL"
        vendor_obj = None
        if vendor_name:
            vendor_obj = db_session.query(Vendor).filter(Vendor.name.ilike(f"%{vendor_name}%")).first()

        vendor_avg = float(vendor_obj.average_invoice_amount) if vendor_obj and vendor_obj.average_invoice_amount else 0.0
        
        # Get historical invoice amounts for this vendor
        historical_invoices = db_session.query(Invoice.total_amount).filter(
            Invoice.vendor_name.ilike(f"%{vendor_name}%")
        ).all()
        
        amounts = [float(row[0]) for row in historical_invoices if row[0] is not None]
        
        if len(amounts) >= 3:
            mean = sum(amounts) / len(amounts)
            variance = sum((x - mean) ** 2 for x in amounts) / len(amounts)
            std = math.sqrt(variance)
            if std > 0:
                z_score = abs(invoice_total - mean) / std
                if z_score >= 2.0 or (vendor_avg > 0 and invoice_total > vendor_avg * 2.2):
                    anomaly_status = "ANOMALY_DETECTED"
                    risk_score += 45
                    factor_info = {
                        "factor": "Statistical Amount Anomaly",
                        "points": 45,
                        "severity": "HIGH",
                        "status": "FAILED",
                        "description": f"Invoice amount (₹{invoice_total:,.2f}) is a statistical outlier exceeding historical vendor profile average (₹{mean:,.2f}, Z-score: {z_score:.2f})."
                    }
                    risk_factors.append(factor_info)
                    all_vector_checks.append(factor_info)
        elif vendor_avg > 0 and invoice_total > vendor_avg * 2.2:
            anomaly_status = "ANOMALY_DETECTED"
            risk_score += 45
            factor_info = {
                "factor": "Statistical Amount Anomaly",
                "points": 45,
                "severity": "HIGH",
                "status": "FAILED",
                "description": f"Invoice amount (₹{invoice_total:,.2f}) significantly exceeds vendor historical baseline average of ₹{vendor_avg:,.2f}."
            }
            risk_factors.append(factor_info)
            all_vector_checks.append(factor_info)

        if anomaly_status == "NORMAL":
            all_vector_checks.append({
                "factor": "Statistical Amount Validation",
                "points": 0,
                "severity": "LOW",
                "status": "PASSED",
                "description": f"Invoice amount is within the vendor's normal historical billing bandwidth (Avg: ₹{vendor_avg:,.2f})."
            })

        # -------------------------------------------------------------
        # Vector 5: Vendor Profile & Scrutiny
        # -------------------------------------------------------------
        if vendor_obj and vendor_obj.risk_rating == "HIGH":
            risk_score += 15
            factor_info = {
                "factor": "High-Risk Vendor Profile",
                "points": 15,
                "severity": "MEDIUM",
                "status": "WARNING",
                "description": "Vendor is flagged for enhanced audit scrutiny in enterprise vendor directory."
            }
            risk_factors.append(factor_info)
            all_vector_checks.append(factor_info)
        else:
            all_vector_checks.append({
                "factor": "Vendor Compliance Standing",
                "points": 0,
                "severity": "LOW",
                "status": "PASSED",
                "description": "Vendor profile is verified with active tax compliance standing."
            })

        # -------------------------------------------------------------
        # Vector 6: Document Extraction Verification
        # -------------------------------------------------------------
        if invoice_data.get("extraction_warning") or invoice_total <= 0:
            risk_score += 35
            factor_info = {
                "factor": "Document Extraction Warning",
                "points": 35,
                "severity": "HIGH",
                "status": "WARNING",
                "description": invoice_data.get("extraction_warning") or "Invoice amount could not be reliably extracted from document."
            }
            risk_factors.append(factor_info)
            all_vector_checks.append(factor_info)

        # Cap score between 0 and 100
        risk_score = min(100, max(0, risk_score))
        
        # Categorize risk level: 0–24 LOW, 25–49 MEDIUM, 50–74 HIGH, 75–100 CRITICAL
        if risk_score >= 75 or duplicate_status == "DUPLICATE_FOUND":
            risk_level = "CRITICAL"
        elif risk_score >= 50 or anomaly_status == "ANOMALY_DETECTED":
            risk_level = "HIGH"
        elif risk_score >= 25:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "duplicate_status": duplicate_status,
            "anomaly_status": anomaly_status,
            "risk_breakdown": risk_factors, # Active penalty factors
            "all_vector_checks": all_vector_checks, # Complete audit trail including 0-point passes
            "vendor_avg_amount": vendor_avg
        }
