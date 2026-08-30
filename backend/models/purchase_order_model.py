import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.models.database import Base

class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String(100), unique=True, index=True, nullable=False)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True)
    vendor_name = Column(String(200), nullable=False)
    po_date = Column(Date, nullable=False)
    subtotal = Column(Numeric(15, 2), default=0.00)
    tax_amount = Column(Numeric(15, 2), default=0.00)
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(10), default="INR")
    status = Column(String(50), default="APPROVED") # APPROVED, CLOSED, PENDING, REJECTED
    line_items = Column(Text) # JSON string representation
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    vendor = relationship("Vendor", backref="purchase_orders")

    def get_line_items(self):
        if not self.line_items:
            return []
        try:
            return json.loads(self.line_items)
        except Exception:
            return []

    def to_dict(self):
        return {
            "id": self.id,
            "po_number": self.po_number,
            "vendor_id": self.vendor_id,
            "vendor_name": self.vendor_name,
            "po_date": self.po_date.isoformat() if self.po_date else None,
            "subtotal": float(self.subtotal) if self.subtotal is not None else 0.0,
            "tax_amount": float(self.tax_amount) if self.tax_amount is not None else 0.0,
            "total_amount": float(self.total_amount) if self.total_amount is not None else 0.0,
            "currency": self.currency,
            "status": self.status,
            "line_items": self.get_line_items(),
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
