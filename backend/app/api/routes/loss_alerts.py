from decimal import Decimal
from typing import Literal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.orm import Session

from app.api.dependencies import require_roles
from app.db.session import get_db
from app.models.karigar import Karigar
from app.models.transaction import GoldTransaction
from app.models.user import User
from app.schemas.transaction import TransactionResponse
from app.services.gold_calculations import calculate_fine_gold, compute_karigar_balance
from app.services.loss_alerts import unresolved_loss_conditions

router = APIRouter(prefix='/loss-alerts', tags=['Loss review'])
STAFF = ['admin', 'finance_head', 'manager', 'issue_clerk']


class LossReview(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    investigation_notes: str = Field(min_length=10, max_length=2000)
    confirm_write_off: Literal[True]


class LossAlertResponse(BaseModel):
    alert: TransactionResponse
    resolution: TransactionResponse | None = None


def resolution_for(db, tx):
    return db.query(GoldTransaction).filter(
        GoldTransaction.transaction_type == 'LOSS_ADJUSTMENT',
        GoldTransaction.related_slip_number == tx.slip_number,
        GoldTransaction.karigar_id == tx.karigar_id,
    ).order_by(GoldTransaction.id).first()


@router.get('', response_model=list[LossAlertResponse])
def list_loss_alerts(
    status: Literal['open', 'resolved'] = Query('open'),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(STAFF)),
):
    conditions = unresolved_loss_conditions()
    query = db.query(GoldTransaction).filter(*conditions[:2])
    query = query.filter(conditions[2] if status == 'open' else ~conditions[2])
    alerts = query.order_by(GoldTransaction.created_at.desc(), GoldTransaction.id.desc()).limit(limit).all()
    return [LossAlertResponse(alert=tx, resolution=resolution_for(db, tx)) for tx in alerts]


@router.post('/{transaction_id}/write-off', response_model=TransactionResponse)
def write_off_loss(
    payload: LossReview,
    transaction_id: int = Path(..., gt=0),
    db: Session = Depends(get_db),
    user: User = Depends(require_roles(['admin', 'finance_head'])),
):
    tx = db.get(GoldTransaction, transaction_id)
    if tx is None:
        raise HTTPException(status_code=404, detail='Alert not found')
    if tx.transaction_type != 'RECEIPT_ORNAMENT' or not tx.is_loss_alert or not tx.karigar_id:
        raise HTTPException(status_code=400, detail='Only flagged ornament receipts can be reviewed')
    # Same custody lock used by receipts prevents competing deductions.
    karigar = db.query(Karigar).filter(Karigar.id == tx.karigar_id).with_for_update().first()
    if karigar is None:
        raise HTTPException(status_code=409, detail='Karigar custody record is unavailable')
    existing = resolution_for(db, tx)
    if existing:
        return existing  # Repeat approval never changes the original decision.

    gross = Decimal(str(tx.wastage_variance_weight))
    fine = calculate_fine_gold(gross, tx.purity_percent)
    history = db.query(GoldTransaction).filter(GoldTransaction.karigar_id == karigar.id).all()
    balance = compute_karigar_balance(
        karigar.opening_balance_gross, karigar.opening_balance_fine,
        [t for t in history if t.transaction_type == 'ISSUE'],
        [t for t in history if t.transaction_type in {
            'RECEIPT_ORNAMENT', 'RECEIPT_SCRAP', 'RECEIPT_DUST', 'WASTAGE_SETTLEMENT', 'LOSS_ADJUSTMENT'}],
    )
    if gross <= 0 or fine <= 0 or gross > balance.closing_balance_gross or fine > balance.closing_balance_fine:
        raise HTTPException(status_code=409, detail='Excess exceeds available custody. Reconcile returns and prior adjustments before approving.')
    adjustment = GoldTransaction(
        slip_number=f'ADJ-{uuid4().hex[:16].upper()}',
        idempotency_key=f'loss-resolution:{tx.id}',
        related_slip_number=tx.slip_number, transaction_type='LOSS_ADJUSTMENT',
        karigar_id=karigar.id, created_by_user_id=user.id,
        item_description=f'Finance-approved excess loss for {tx.slip_number}',
        gross_weight=gross, stone_weight=Decimal('0.000'), net_weight=gross,
        purity_percent=tx.purity_percent, fine_weight=fine,
        scale_reading_confirmed=False,
        notes=payload.investigation_notes,
    )
    try:
        db.add(adjustment)
        db.commit()
        db.refresh(adjustment)
    except Exception:
        db.rollback()
        raise
    return adjustment
