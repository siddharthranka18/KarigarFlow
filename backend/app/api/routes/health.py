from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from datetime import datetime, timezone
from fastapi.responses import JSONResponse
from app.db.session import get_db

router = APIRouter(prefix="/health", tags=["Health"])

@router.get("")
def health_check(db: Session = Depends(get_db)):
    """Health check for service and database connectivity."""
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content={'status': 'degraded', 'database': 'unavailable'})

    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "service": "KarigarFlow ERP Backend",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": db_status
    }

