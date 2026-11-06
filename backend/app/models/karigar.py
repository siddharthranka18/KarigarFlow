from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.base import Base
from sqlalchemy import JSON

class Karigar(Base):
    __tablename__ = "karigars"

    id = Column(Integer, primary_key=True, index=True)
    karigar_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    phone = Column(String(50), nullable=True)
    specialization = Column(String(100), default="General Jewellery")
    benchmark_wastage_percent = Column(Numeric(5, 2), default=2.00, nullable=False)
    wastage_by_category = Column(JSON, default=dict, nullable=False)
    opening_balance_gross = Column(Numeric(10, 3), default=0.000, nullable=False)
    opening_balance_fine = Column(Numeric(10, 3), default=0.000, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    # Optional 1-1 link with a login user
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, unique=True)
    user = relationship("User", backref="karigar_profile")

    # Relationship to transactions
    transactions = relationship("GoldTransaction", back_populates="karigar", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Karigar {self.karigar_code} - {self.name}>"

