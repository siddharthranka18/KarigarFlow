from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, ForeignKey, LargeBinary, Numeric, Text, DateTime
from app.db.base import Base


class ScaleReading(Base):
    __tablename__ = 'scale_readings'
    id = Column(String(36), primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    image = Column(LargeBinary, nullable=False)
    status = Column(String(20), nullable=False)
    weight = Column(Numeric(10, 3), nullable=True)
    purity = Column(Numeric(5, 2), nullable=True)
    confidence = Column(Numeric(5, 4), nullable=False)
    raw_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), nullable=False)
