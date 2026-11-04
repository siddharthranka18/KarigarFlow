from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

# Connect with pool settings for PostgreSQL
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

try:
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        echo=False,
        connect_args=connect_args
    )
except Exception as e:
    logger.warning(f"Could not initialize primary database ({settings.DATABASE_URL}): {e}. Falling back to SQLite.")
    engine = create_engine(
        "sqlite:///./karigarflow_fallback.db",
        pool_pre_ping=True,
        echo=False,
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Dependency that yields an active database session and ensures it closes."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()

