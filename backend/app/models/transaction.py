from sqlalchemy import Column, Integer, String, Boolean, DateTime, Numeric, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from typing import Optional
import enum
from app.db.base import Base

class TransactionType(str, enum.Enum):
    ISSUE = "ISSUE"                            # Raw/alloy gold given to karigar for ornament making
    RECEIPT_ORNAMENT = "RECEIPT_ORNAMENT"      # Finished jewellery returned by karigar
    RECEIPT_SCRAP = "RECEIPT_SCRAP"            # Cuttings/remnants returned by karigar
    RECEIPT_DUST = "RECEIPT_DUST"              # Recovered filing/polishing dust
    WASTAGE_SETTLEMENT = "WASTAGE_SETTLEMENT"  # Legitimate approved craft wastage settled
    LOSS_ADJUSTMENT = "LOSS_ADJUSTMENT"        # Excess wastage loss audit adjustment/recovery
    PURCHASE = "PURCHASE"                      # Bullion purchase added to workshop vault

class GoldTransaction(Base):
    __tablename__ = "gold_transactions"

    id = Column(Integer, primary_key=True, index=True)
    slip_number = Column(String(100), unique=True, index=True, nullable=False)
    idempotency_key = Column(String(100), unique=True, index=True, nullable=True)
    related_slip_number = Column(String(100), nullable=True, index=True)
    transaction_type = Column(String(50), nullable=False)
    
    karigar_id = Column(Integer, ForeignKey("karigars.id"), nullable=True, index=True)
    karigar = relationship("Karigar", back_populates="transactions")

    created_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by_user = relationship("User")

    item_description = Column(String(255), nullable=False)
    
    # Gold measurements with exact Decimal precision
    # Stored weights in grams to 3 decimal places (e.g. 125.450 g)
    gross_weight = Column(Numeric(10, 3), nullable=False)
    stone_weight = Column(Numeric(10, 3), default=0.000, nullable=False)
    net_weight = Column(Numeric(10, 3), nullable=False)
    
    # Purity to 2 decimal places (e.g. 91.60 % for 22K 916 Hallmark)
    purity_percent = Column(Numeric(5, 2), nullable=False)
    
    # Pure 24K equivalent in grams to 3 decimal places
    fine_weight = Column(Numeric(10, 3), nullable=False)

    # Wastage tracking for job settlements
    allowed_wastage_percent = Column(Numeric(5, 2), default=0.00, nullable=False)
    actual_wastage_weight = Column(Numeric(10, 3), default=0.000, nullable=False)
    wastage_variance_weight = Column(Numeric(10, 3), default=0.000, nullable=False)
    is_loss_alert = Column(Boolean, default=False, nullable=False)

    # Scale photo reading confirmation tracking
    scale_reading_confirmed = Column(Boolean, default=True, nullable=False)
    scale_image_url = Column(String(500), nullable=True)

    notes = Column(Text, nullable=True)
    # Match the existing timestamp-without-time-zone column with explicit UTC.
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False, index=True)

    @property
    def karigar_name(self) -> Optional[str]:
        return self.karigar.name if self.karigar else None

    @property
    def karigar_code(self) -> Optional[str]:
        return self.karigar.karigar_code if self.karigar else None

    def __repr__(self):
        return f"<GoldTransaction {self.slip_number} {self.transaction_type} {self.gross_weight}g>"
