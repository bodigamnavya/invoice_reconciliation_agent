import json
from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, Text, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from backend.models.database import Base

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(100), nullable=False, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id", ondelete="SET NULL"), nullable=True)
    vendor_name = Column(String(200), nullable=False)
    po_id = Column(Integer, ForeignKey("purchase_orders.id", ondelete="SET NULL"), nullable=True)
    po_number = Column(String(100), index=True)
    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date)
    subtotal = Column(Numeric(15, 2), default=0.00)
    tax_amount = Column(Numeric(15, 2), default=0.00)
    total_amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(10), default="INR")
    line_items = Column(Text) # JSON string
    raw_extracted_text = Column(Text)
    file_path = Column(String(255))
    file_name = Column(String(255))
    file_type = Column(String(50))
    upload_status = Column(String(50), default="PROCESSED")
    created_at = Column(DateTime, default=datetime.utcnow)

    vendor = relationship("Vendor", backref="invoices")
    purchase_order = relationship("PurchaseOrder", backref="invoices")

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
            "invoice_number": self.invoice_number,
            "vendor_id": self.vendor_id,
            "vendor_name": self.vendor_name,
            "po_id": self.po_id,
            "po_number": self.po_number,
            "invoice_date": self.invoice_date.isoformat() if self.invoice_date else None,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "subtotal": float(self.subtotal) if self.subtotal is not None else 0.0,
            "tax_amount": float(self.tax_amount) if self.tax_amount is not None else 0.0,
            "total_amount": float(self.total_amount) if self.total_amount is not None else 0.0,
            "currency": self.currency,
            "line_items": self.get_line_items(),
            "file_name": self.file_name,
            "upload_status": self.upload_status,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
