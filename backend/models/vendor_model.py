from datetime import datetime
from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime
from backend.models.database import Base

class Vendor(Base):
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    tax_id = Column(String(50))
    email = Column(String(150))
    phone = Column(String(50))
    address = Column(Text)
    average_invoice_amount = Column(Numeric(15, 2), default=0.00)
    historical_invoice_count = Column(Integer, default=0)
    risk_rating = Column(String(30), default="LOW") # LOW, MEDIUM, HIGH
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "tax_id": self.tax_id,
            "email": self.email,
            "phone": self.phone,
            "address": self.address,
            "average_invoice_amount": float(self.average_invoice_amount) if self.average_invoice_amount is not None else 0.0,
            "historical_invoice_count": self.historical_invoice_count,
            "risk_rating": self.risk_rating,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
