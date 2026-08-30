import json
import logging
from datetime import datetime, timezone
from backend.models.invoice_model import Invoice
from backend.models.reconciliation_model import ReconciliationResult
from backend.agents.matching_agent import MatchingAgent
from backend.agents.payment_agent import PaymentAgent
from backend.agents.risk_agent import RiskAgent
from backend.agents.decision_agent import DecisionAgent

logger = logging.getLogger("ReconciliationService")

class ReconciliationService:
    """Multi-Agent Orchestrator for full end-to-end reconciliation lifecycle."""

    @classmethod
    def run_reconciliation(cls, invoice_id: int, db_session) -> ReconciliationResult:
        """
        Executes the agentic pipeline for a given invoice:
        Invoice Record -> Matching Agent -> Payment Agent -> Risk Agent -> Decision Agent -> Save in DB
        """
        invoice = db_session.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise ValueError(f"Invoice with ID {invoice_id} not found.")

        invoice_dict = invoice.to_dict()

        # Step 1: Matching Agent (PO reconciliation)
        matching_res = MatchingAgent.match_invoice_with_po(invoice_dict, db_session)
        
        # Link PO to invoice if discovered
        if matching_res.get("po_id") and not invoice.po_id:
            invoice.po_id = matching_res["po_id"]
            invoice.po_number = matching_res["po_number"]
            db_session.commit()

        # Step 2: Payment Agent (Banking ledger reconciliation)
        payment_res = PaymentAgent.match_invoice_with_payment(invoice_dict, matching_res.get("po_id"), db_session)

        # Step 3: Risk Agent (Multi-factor risk analysis & anomaly scoring)
        risk_res = RiskAgent.evaluate_risk(invoice_dict, matching_res, payment_res, db_session)

        # Step 4: Decision Agent (State matrix + Natural language synthesis)
        decision_res = DecisionAgent.make_decision(invoice_dict, matching_res, payment_res, risk_res)

        # Step 5: Persist / Update Reconciliation Result in PostgreSQL
        existing_result = db_session.query(ReconciliationResult).filter(
            ReconciliationResult.invoice_id == invoice_id
        ).first()

        risk_payload = {
            "factors": decision_res.get("risk_breakdown", []),
            "all_vector_checks": decision_res.get("all_vector_checks", [])
        }

        now_utc = datetime.now(timezone.utc)

        if not existing_result:
            recon_record = ReconciliationResult(
                invoice_id=invoice.id,
                po_id=matching_res.get("po_id"),
                payment_id=payment_res.get("payment_id"),
                status=decision_res["status"],
                po_match_status=decision_res["po_match_status"],
                payment_match_status=decision_res["payment_match_status"],
                duplicate_status=decision_res["duplicate_status"],
                anomaly_status=decision_res["anomaly_status"],
                risk_score=decision_res["risk_score"],
                risk_level=decision_res["risk_level"],
                confidence_score=decision_res["confidence_score"],
                amount_difference_po=matching_res.get("amount_difference", 0.0),
                amount_difference_payment=payment_res.get("amount_difference", 0.0),
                risk_breakdown=json.dumps(risk_payload),
                ai_reason=decision_res["ai_reason"],
                ai_explanation=decision_res["ai_explanation"],
                ai_recommendation=decision_res["ai_recommendation"],
                human_action="PENDING",
                created_at=now_utc,
                updated_at=now_utc
            )
            db_session.add(recon_record)
        else:
            recon_record = existing_result
            recon_record.po_id = matching_res.get("po_id")
            recon_record.payment_id = payment_res.get("payment_id")
            recon_record.status = decision_res["status"]
            recon_record.po_match_status = decision_res["po_match_status"]
            recon_record.payment_match_status = decision_res["payment_match_status"]
            recon_record.duplicate_status = decision_res["duplicate_status"]
            recon_record.anomaly_status = decision_res["anomaly_status"]
            recon_record.risk_score = decision_res["risk_score"]
            recon_record.risk_level = decision_res["risk_level"]
            recon_record.confidence_score = decision_res["confidence_score"]
            recon_record.amount_difference_po = matching_res.get("amount_difference", 0.0)
            recon_record.amount_difference_payment = payment_res.get("amount_difference", 0.0)
            recon_record.risk_breakdown = json.dumps(risk_payload)
            recon_record.ai_reason = decision_res["ai_reason"]
            recon_record.ai_explanation = decision_res["ai_explanation"]
            recon_record.ai_recommendation = decision_res["ai_recommendation"]
            recon_record.updated_at = now_utc

        db_session.commit()
        db_session.refresh(recon_record)
        return recon_record

    @classmethod
    def get_explainable_audit_trail(cls, recon: ReconciliationResult) -> dict:
        """Constructs detailed explainable audit trail and timeline breakdown from real database records."""
        invoice = recon.invoice
        po = recon.purchase_order
        payment = recon.payment

        inv_amt = float(invoice.total_amount) if invoice and invoice.total_amount is not None else 0.0
        po_amt = float(po.total_amount) if po and po.total_amount is not None else 0.0
        pay_amt = float(payment.amount_paid) if payment and payment.amount_paid is not None else 0.0
        
        po_diff = float(recon.amount_difference_po) if recon.amount_difference_po is not None else 0.0
        pay_diff = float(recon.amount_difference_payment) if recon.amount_difference_payment is not None else 0.0
        
        po_variance_percent = round((abs(po_diff) / po_amt * 100), 2) if po_amt > 0 else 0.0

        # Unpack stored risk payload
        stored_factors = recon.get_risk_breakdown()
        all_checks = []
        if isinstance(stored_factors, dict):
            all_checks = stored_factors.get("all_vector_checks", [])
            factors_list = stored_factors.get("factors", [])
        elif isinstance(stored_factors, list):
            all_checks = stored_factors
            factors_list = stored_factors
        else:
            factors_list = []

        # If all_checks is empty, build default checks from reconciliation fields
        if not all_checks:
            all_checks = [
                {
                    "factor": "Purchase Order Variance",
                    "points": 35 if recon.po_match_status == "MISMATCH" else (25 if recon.po_match_status == "NOT_FOUND" else 0),
                    "severity": "HIGH" if recon.po_match_status == "MISMATCH" else "LOW",
                    "status": "FAILED" if recon.po_match_status == "MISMATCH" else "PASSED",
                    "description": f"PO Status: {recon.po_match_status} (Variance: ₹{abs(po_diff):,.2f})"
                },
                {
                    "factor": "Payment Mismatch",
                    "points": 25 if recon.payment_match_status in ["PARTIAL_PAYMENT", "OVERPAYMENT"] else 0,
                    "severity": "MEDIUM" if recon.payment_match_status in ["PARTIAL_PAYMENT", "OVERPAYMENT"] else "LOW",
                    "status": "WARNING" if recon.payment_match_status in ["PARTIAL_PAYMENT", "OVERPAYMENT"] else "PASSED",
                    "description": f"Payment Status: {recon.payment_match_status} (Diff: ₹{abs(pay_diff):,.2f})"
                },
                {
                    "factor": "Duplicate Invoice Check",
                    "points": 45 if recon.duplicate_status == "DUPLICATE_FOUND" else 0,
                    "severity": "CRITICAL" if recon.duplicate_status == "DUPLICATE_FOUND" else "LOW",
                    "status": "FAILED" if recon.duplicate_status == "DUPLICATE_FOUND" else "PASSED",
                    "description": "Duplicate detected on record." if recon.duplicate_status == "DUPLICATE_FOUND" else "No duplicate invoice found."
                },
                {
                    "factor": "Statistical Amount Anomaly",
                    "points": 45 if recon.anomaly_status == "ANOMALY_DETECTED" else 0,
                    "severity": "HIGH" if recon.anomaly_status == "ANOMALY_DETECTED" else "LOW",
                    "status": "FAILED" if recon.anomaly_status == "ANOMALY_DETECTED" else "PASSED",
                    "description": "Invoice amount is statistical outlier." if recon.anomaly_status == "ANOMALY_DETECTED" else "Amount is within normal historical baseline."
                }
            ]

        # Build true timestamped audit timeline
        base_time = invoice.created_at if invoice and invoice.created_at else recon.created_at
        timeline = [
            {
                "step": 1,
                "name": "Invoice Document Uploaded",
                "status": "COMPLETED",
                "timestamp": base_time.strftime("%Y-%m-%d %H:%M:%S") if base_time else "2026-08-30 12:00:00",
                "details": f"File '{invoice.file_name if invoice else 'invoice.pdf'}' securely stored and indexed."
            },
            {
                "step": 2,
                "name": "OCR & Structured Field Extraction",
                "status": "COMPLETED",
                "timestamp": base_time.strftime("%Y-%m-%d %H:%M:%S") if base_time else "2026-08-30 12:00:01",
                "details": f"Extracted Invoice #{invoice.invoice_number if invoice else 'N/A'}, Total: ₹{inv_amt:,.2f}, Vendor: {invoice.vendor_name if invoice else 'N/A'}."
            },
            {
                "step": 3,
                "name": "Purchase Order 2-Way Match",
                "status": "COMPLETED" if recon.po_match_status == "MATCHED" else "FLAGGED",
                "timestamp": recon.created_at.strftime("%Y-%m-%d %H:%M:%S") if recon.created_at else "2026-08-30 12:00:02",
                "details": f"Evaluated against PO #{po.po_number if po else (invoice.po_number if invoice else 'N/A')}. Result: {recon.po_match_status} (Variance: ₹{abs(po_diff):,.2f})."
            },
            {
                "step": 4,
                "name": "Banking Ledger Settlement Match",
                "status": "COMPLETED" if recon.payment_match_status == "FULL_PAYMENT" else "FLAGGED",
                "timestamp": recon.created_at.strftime("%Y-%m-%d %H:%M:%S") if recon.created_at else "2026-08-30 12:00:03",
                "details": f"Ledger scan matched ref '{payment.payment_reference if payment else 'N/A'}'. Result: {recon.payment_match_status} (Disbursed: ₹{pay_amt:,.2f})."
            },
            {
                "step": 5,
                "name": "Duplicate & Fraud Pattern Check",
                "status": "COMPLETED" if recon.duplicate_status == "UNIQUE" else "FLAGGED",
                "timestamp": recon.created_at.strftime("%Y-%m-%d %H:%M:%S") if recon.created_at else "2026-08-30 12:00:04",
                "details": f"Cross-referenced historical database. Status: {recon.duplicate_status}."
            },
            {
                "step": 6,
                "name": "Multi-Vector Risk & Anomaly Scoring",
                "status": "COMPLETED",
                "timestamp": recon.created_at.strftime("%Y-%m-%d %H:%M:%S") if recon.created_at else "2026-08-30 12:00:05",
                "details": f"Calculated deterministic Risk Score: {recon.risk_score}/100 ({recon.risk_level} Risk)."
            },
            {
                "step": 7,
                "name": "Autonomous Decision Synthesis",
                "status": "COMPLETED",
                "timestamp": recon.created_at.strftime("%Y-%m-%d %H:%M:%S") if recon.created_at else "2026-08-30 12:00:06",
                "details": f"Final synthesized status: {recon.status} (Confidence: {float(recon.confidence_score):.1f}%)."
            },
            {
                "step": 8,
                "name": "Human-in-the-Loop Governance",
                "status": "COMPLETED" if recon.human_action != "PENDING" else "PENDING",
                "timestamp": recon.reviewed_at.strftime("%Y-%m-%d %H:%M:%S") if recon.reviewed_at else None,
                "details": f"Sign-off state: {recon.human_action}" + (f" by Auditor (Notes: '{recon.reviewer_notes}')" if recon.reviewed_at else " — Awaiting finance reviewer action.")
            }
        ]

        return {
            "variance_summary": {
                "invoice_amount": inv_amt,
                "po_amount": po_amt,
                "po_number": po.po_number if po else (invoice.po_number if invoice else "N/A"),
                "po_variance": po_diff,
                "po_variance_percent": po_variance_percent,
                "payment_amount": pay_amt,
                "payment_reference": payment.payment_reference if payment else "N/A",
                "payment_variance": pay_diff
            },
            "risk_score": recon.risk_score,
            "risk_level": recon.risk_level,
            "all_vector_checks": all_checks,
            "ai_reason": recon.ai_reason,
            "ai_explanation": recon.ai_explanation,
            "ai_recommendation": recon.ai_recommendation,
            "timeline": timeline
        }

    @classmethod
    def apply_human_action(cls, invoice_id: int, action: str, user_id: int, notes: str, db_session) -> ReconciliationResult:
        """Records finance user approval, review, or rejection."""
        recon = db_session.query(ReconciliationResult).filter(
            ReconciliationResult.invoice_id == invoice_id
        ).first()

        if not recon:
            raise ValueError(f"Reconciliation result for invoice {invoice_id} not found.")

        valid_actions = {"APPROVED", "REVIEWED", "REJECTED"}
        action_upper = action.upper()
        if action_upper not in valid_actions:
            raise ValueError(f"Invalid human action: {action}. Expected one of {valid_actions}")

        now_utc = datetime.now(timezone.utc)
        recon.human_action = action_upper
        recon.reviewed_by = user_id
        recon.reviewed_at = now_utc
        recon.reviewer_notes = notes
        recon.updated_at = now_utc

        db_session.commit()
        db_session.refresh(recon)
        return recon
