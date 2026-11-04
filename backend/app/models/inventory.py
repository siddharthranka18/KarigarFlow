from sqlalchemy import Column, Integer, String, DateTime, Numeric
from datetime import datetime, timezone
from app.db.base import Base

class GoldInventory(Base):
    __tablename__ = "gold_inventory"

    id = Column(Integer, primary_key=True, index=True)
    lot_code = Column(String(50), unique=True, index=True, nullable=False)
    category = Column(String(100), nullable=False)  # Raw 24K Bar, 22K Grain, Scrap, Finished Stock
    description = Column(String(255), nullable=False)
    gross_weight = Column(Numeric(10, 3), nullable=False)
    purity_percent = Column(Numeric(5, 2), nullable=False)
    fine_weight = Column(Numeric(10, 3), nullable=False)
    location = Column(String(100), default="Coimbatore Central Workshop Vault", nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<GoldInventory {self.lot_code} {self.category} {self.gross_weight}g>"

