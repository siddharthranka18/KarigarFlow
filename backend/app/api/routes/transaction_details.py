"""Read-only slip inspection; every linked record obeys the same custody scope."""
from fastapi import APIRouter, Depends, HTTPException, Path
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.karigar import Karigar
from app.models.transaction import GoldTransaction
from app.models.user import User, UserRole
from app.schemas.transaction import TransactionDetail

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("/{transaction_id}", response_model=TransactionDetail)
def inspect_transaction(
    transaction_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(GoldTransaction).options(joinedload(GoldTransaction.karigar))
    if current_user.role == UserRole.KARIGAR.value:
        own_ids = db.query(Karigar.id).filter(Karigar.user_id == current_user.id)
        query = query.filter(GoldTransaction.karigar_id.in_(own_ids))
    elif current_user.role not in {
        UserRole.ADMIN.value, UserRole.FINANCE_HEAD.value,
        UserRole.WORKSHOP_MANAGER.value, UserRole.ISSUE_CLERK.value,
    }:
        raise HTTPException(status_code=403, detail="Operation not permitted")

    tx = query.filter(GoldTransaction.id == transaction_id).first()
    # Do not reveal whether another craftsman's slip exists.
    if tx is None:
        raise HTTPException(status_code=404, detail="Slip not found or unavailable")

    # A bad legacy link must never disclose a different craftsman's record.
    related_query = query.filter(GoldTransaction.karigar_id == tx.karigar_id)
    parent = None
    if tx.related_slip_number:
        parent = related_query.filter(
            GoldTransaction.slip_number == tx.related_slip_number
        ).first()
    children = related_query.filter(
        GoldTransaction.related_slip_number == tx.slip_number,
        GoldTransaction.id != tx.id,
    ).order_by(GoldTransaction.created_at, GoldTransaction.id).all()
    return TransactionDetail(
        transaction=tx,
        recorded_by_name=tx.created_by_user.full_name if tx.created_by_user else None,
        parent=parent,
        linked_entries=children,
    )
