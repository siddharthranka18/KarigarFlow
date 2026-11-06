from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime, timezone
import enum
from app.db.base import Base

class UserRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"                    # Full control / Finance Head
    FINANCE_HEAD = "finance_head"      # Auditing, P&L, stock verification
    WORKSHOP_MANAGER = "manager"       # Karigar assignment, daily reconciliation
    ISSUE_CLERK = "issue_clerk"        # Day-to-day issue/receipt gold slips
    KARIGAR = "karigar"                # Individual craftsman view

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default=UserRole.ISSUE_CLERK.value, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def __repr__(self):
        return f"<User {self.email} ({self.role})>"

