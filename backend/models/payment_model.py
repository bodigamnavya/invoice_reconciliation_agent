from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.models.database import Base

class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    payment_reference = Column(String(100), unique=True, index=True, nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id", ondelete="SET NULL"), nullable=True)
    invoice_number = Column(String(100), index=True)
    po_id = Column(Integer, ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True)
    po_number = Column(String(100), index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True)
    vendor_name = Column(String(200), nullable=False)
    payment_date = Column(Date, nullable=False)
    amount_paid = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(10), default="INR")
    payment_method = Column(String(50), default="BANK_TRANSFER")
    status = Column(String(50), default="COMPLETED") # COMPLETED, PENDING, FAILED
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    vendor = relationship("Vendor", backref="payments")
    invoice = relationship("Invoice", backref="payments")
    purchase_order = relationship("PurchaseOrder", backref="payments")

    def to_dict(self):
        return {
            "id": self.id,
            "payment_reference": self.payment_reference,
            "invoice_id": self.invoice_id,
            "invoice_number": self.invoice_number,
            "po_id": self.po_id,
            "po_number": self.po_number,
            "vendor_id": self.vendor_id,
            "vendor_name": self.vendor_name,
            "payment_date": self.payment_date.isoformat() if self.payment_date else None,
            "amount_paid": float(self.amount_paid) if self.amount_paid is not None else 0.0,
            "currency": self.currency,
            "payment_method": self.payment_method,
            "status": self.status,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
