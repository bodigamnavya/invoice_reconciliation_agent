import logging
from backend.services.llm_service import LLMService

logger = logging.getLogger("DecisionAgent")

class DecisionAgent:
    """Agent responsible for final reconciliation synthesis, status determination, and generating AI insights."""

    @classmethod
    def make_decision(cls, invoice_data: dict, matching_result: dict, payment_result: dict, risk_result: dict) -> dict:
        """
        Synthesizes deterministic decision logic and leverages LLM/Rule engine for human explanation and action.
        """
        risk_score = risk_result.get("risk_score", 0)
        risk_level = risk_result.get("risk_level", "LOW")
        po_status = matching_result.get("po_match_status", "NOT_FOUND")
        payment_status = payment_result.get("payment_match_status", "UNPAID")
        duplicate_status = risk_result.get("duplicate_status", "UNIQUE")
        anomaly_status = risk_result.get("anomaly_status", "NORMAL")

        # -------------------------------------------------------------
        # Deterministic Decision Matrix
        # -------------------------------------------------------------
        if duplicate_status == "DUPLICATE_FOUND":
            status = "REJECT" if risk_score >= 80 else "REVIEW_REQUIRED"
        elif risk_level in ["CRITICAL", "HIGH"] or anomaly_status == "ANOMALY_DETECTED" or po_status == "MISMATCH":
            status = "HIGH_RISK"
        elif payment_status in ["PARTIAL_PAYMENT", "OVERPAYMENT", "UNPAID"] or po_status == "NOT_FOUND" or risk_level == "MEDIUM":
            status = "REVIEW_REQUIRED"
        elif po_status == "MATCHED" and payment_status == "FULL_PAYMENT" and duplicate_status == "UNIQUE" and anomaly_status == "NORMAL":
            status = "MATCHED"
        else:
            status = "REVIEW_REQUIRED"

        # -------------------------------------------------------------
        # Generate Natural Language Insights via LLM or Rule Engine
        # -------------------------------------------------------------
        context = {
            "status": status,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "invoice_number": invoice_data.get("invoice_number"),
            "vendor_name": invoice_data.get("vendor_name"),
            "invoice_amount": float(invoice_data.get("total_amount", 0.0)),
            "po_match_status": po_status,
            "po_number": matching_result.get("po_number"),
            "po_amount": matching_result.get("po_amount", 0.0),
            "payment_match_status": payment_status,
            "payment_amount": payment_result.get("amount_paid", 0.0),
            "payment_ref": payment_result.get("payment_reference"),
            "duplicate_status": duplicate_status,
            "anomaly_status": anomaly_status,
            "vendor_avg_amount": risk_result.get("vendor_avg_amount", 0.0),
            "mismatch_details": matching_result.get("mismatch_details", []),
            "risk_factors": risk_result.get("risk_breakdown", [])
        }

        ai_output = LLMService.generate_ai_insight(context)

        return {
            "status": status,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "po_match_status": po_status,
            "payment_match_status": payment_status,
            "duplicate_status": duplicate_status,
            "anomaly_status": anomaly_status,
            "ai_reason": ai_output.get("reason", ""),
            "ai_explanation": ai_output.get("explanation", ""),
            "ai_recommendation": ai_output.get("recommendation", ""),
            "confidence_score": ai_output.get("confidence", 95.0),
            "risk_breakdown": risk_result.get("risk_breakdown", []),
            "all_vector_checks": risk_result.get("all_vector_checks", [])
        }
