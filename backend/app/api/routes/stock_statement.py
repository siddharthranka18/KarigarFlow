from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.stock_statement import StockStatement
from app.services.stock_statement import build_stock_statement, WORKSHOP_TZ

router = APIRouter(tags=['Stock statement'])


@router.get('/stock-statement', response_model=StockStatement)
def stock_statement(
    statement_date: date | None = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        UserRole.ADMIN.value, UserRole.FINANCE_HEAD.value,
        UserRole.WORKSHOP_MANAGER.value, UserRole.ISSUE_CLERK.value,
    ])),
):
    today = datetime.now(WORKSHOP_TZ).date()
    selected = statement_date or today
    if selected > today:
        raise HTTPException(status_code=400, detail='Future stock statements are not available')
    return build_stock_statement(db, selected)
