import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.models.database import Base

class ReconciliationResult(Base):
    __tablename__ = "reconciliation_results"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True)
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="SET NULL"), nullable=True)
    
    # Decisions & States
    status = Column(String(50), nullable=False, index=True) # MATCHED, REVIEW_REQUIRED, HIGH_RISK, REJECT
    po_match_status = Column(String(50), nullable=False) # MATCHED, MISMATCH, NOT_FOUND
    payment_match_status = Column(String(50), nullable=False) # FULL_PAYMENT, PARTIAL_PAYMENT, OVERPAYMENT, UNPAID
    duplicate_status = Column(String(50), default="UNIQUE") # UNIQUE, DUPLICATE_FOUND
    anomaly_status = Column(String(50), default="NORMAL") # NORMAL, ANOMALY_DETECTED
    
    # Numerical metrics
    risk_score = Column(Integer, nullable=False) # 0 to 100
    risk_level = Column(String(30), nullable=False, index=True) # LOW, MEDIUM, HIGH, CRITICAL
    confidence_score = Column(Numeric(5, 2), default=95.00)
    
    # Variances
    amount_difference_po = Column(Numeric(15, 2), default=0.00)
    amount_difference_payment = Column(Numeric(15, 2), default=0.00)
    risk_breakdown = Column(Text) # JSON structure
    
    # AI generated explanations
    ai_reason = Column(Text)
    ai_explanation = Column(Text, nullable=False)
    ai_recommendation = Column(Text, nullable=False)
    
    # Human in the loop action
    human_action = Column(String(50), default="PENDING") # PENDING, APPROVED, REVIEWED, REJECTED
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reviewed_at = Column(DateTime)
    reviewer_notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    invoice = relationship("Invoice", backref="reconciliation_results")
    purchase_order = relationship("PurchaseOrder", backref="reconciliation_results")
    payment = relationship("Payment", backref="reconciliation_results")
    reviewer = relationship("User", backref="reconciliations_reviewed")

    def get_risk_breakdown(self):
        if not self.risk_breakdown:
            return []
        try:
            return json.loads(self.risk_breakdown)
        except Exception:
            return []

    def to_dict(self):
        return {
            "id": self.id,
            "invoice_id": self.invoice_id,
            "po_id": self.po_id,
            "payment_id": self.payment_id,
            "status": self.status,
            "po_match_status": self.po_match_status,
            "payment_match_status": self.payment_match_status,
            "duplicate_status": self.duplicate_status,
            "anomaly_status": self.anomaly_status,
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "confidence_score": float(self.confidence_score) if self.confidence_score is not None else 95.0,
            "amount_difference_po": float(self.amount_difference_po) if self.amount_difference_po is not None else 0.0,
            "amount_difference_payment": float(self.amount_difference_payment) if self.amount_difference_payment is not None else 0.0,
            "risk_breakdown": self.get_risk_breakdown(),
            "ai_reason": self.ai_reason,
            "ai_explanation": self.ai_explanation,
            "ai_recommendation": self.ai_recommendation,
            "human_action": self.human_action,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "reviewer_notes": self.reviewer_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "invoice": self.invoice.to_dict() if self.invoice else None,
            "purchase_order": self.purchase_order.to_dict() if self.purchase_order else None,
            "payment": self.payment.to_dict() if self.payment else None
        }
