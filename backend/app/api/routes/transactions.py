from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timezone, date
from decimal import Decimal
import uuid

from app.db.session import get_db
from app.models.transaction import GoldTransaction, TransactionType
from app.models.karigar import Karigar
from app.models.inventory import GoldInventory
from app.models.user import User, UserRole
from app.schemas.transaction import TransactionCreate, TransactionResponse, DailyStockSummary
from app.api.dependencies import get_current_user, require_roles
from app.services.gold_calculations import (
    calculate_fine_gold,
    calculate_net_weight,
    calculate_wastage,
    round_weight
)
from app.core.config import settings

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.get("", response_model=List[TransactionResponse])
def list_transactions(
    karigar_id: Optional[int] = Query(None),
    transaction_type: Optional[str] = Query(None),
    loss_alerts_only: Optional[bool] = Query(False),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = db.query(GoldTransaction)

    # Karigar role can only see their own transactions
    if current_user.role == UserRole.KARIGAR.value:
        karigar = db.query(Karigar).filter(Karigar.user_id == current_user.id).first()
        if not karigar:
            return []
        query = query.filter(GoldTransaction.karigar_id == karigar.id)
    elif karigar_id is not None:
        query = query.filter(GoldTransaction.karigar_id == karigar_id)

    if transaction_type:
        query = query.filter(GoldTransaction.transaction_type == transaction_type)

    if loss_alerts_only:
        query = query.filter(GoldTransaction.is_loss_alert == True)

    return query.order_by(GoldTransaction.created_at.desc()).limit(limit).all()

@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        UserRole.ADMIN.value,
        UserRole.FINANCE_HEAD.value,
        UserRole.WORKSHOP_MANAGER.value,
        UserRole.ISSUE_CLERK.value
    ]))
):
    # Validate karigar if transaction involves one
    if payload.transaction_type in [TransactionType.ISSUE.value, TransactionType.RECEIPT_ORNAMENT.value, TransactionType.RECEIPT_SCRAP.value, TransactionType.RECEIPT_DUST.value]:
        if not payload.karigar_id:
            raise HTTPException(status_code=400, detail="karigar_id is required for issue/receipt slips")
        karigar = db.query(Karigar).filter(Karigar.id == payload.karigar_id).first()
        if not karigar:
            raise HTTPException(status_code=404, detail="Karigar not found")

    # Safe decimal calculations
    net_weight = calculate_net_weight(payload.gross_weight, payload.stone_weight)
    if net_weight <= Decimal("0.000"):
        raise HTTPException(status_code=400, detail="Net gold weight must be strictly greater than 0")

    fine_weight = calculate_fine_gold(net_weight, payload.purity_percent)

    # Wastage and loss alert logic
    allowed_pct = payload.allowed_wastage_percent or Decimal("0.00")
    actual_wastage = payload.actual_wastage_weight or Decimal("0.000")
    
    # Calculate allowed wastage weight based on gross weight
    allowed_wastage_weight = round_weight((payload.gross_weight * allowed_pct) / Decimal("100.00"))
    wastage_variance = round_weight(actual_wastage - allowed_wastage_weight)

    is_alert = False
    if payload.transaction_type == TransactionType.RECEIPT_ORNAMENT.value:
        # Check against workshop loss alert threshold (default 0.100g)
        if wastage_variance > settings.LOSS_ALERT_THRESHOLD_GRAMS:
            is_alert = True

    # Generate sequential unique slip code
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y%m%d")
    short_uuid = str(uuid.uuid4())[:5].upper()
    prefix = "ISS" if payload.transaction_type == TransactionType.ISSUE.value else "REC"
    slip_number = f"{prefix}-{date_str}-{short_uuid}"

    tx = GoldTransaction(
        slip_number=slip_number,
        transaction_type=payload.transaction_type,
        karigar_id=payload.karigar_id,
        created_by_user_id=current_user.id,
        item_description=payload.item_description,
        gross_weight=payload.gross_weight,
        stone_weight=payload.stone_weight,
        net_weight=net_weight,
        purity_percent=payload.purity_percent,
        fine_weight=fine_weight,
        allowed_wastage_percent=allowed_pct,
        actual_wastage_weight=actual_wastage,
        wastage_variance_weight=wastage_variance,
        is_loss_alert=is_alert,
        scale_reading_confirmed=payload.scale_reading_confirmed,
        scale_image_url=payload.scale_image_url,
        notes=payload.notes
    )

    db.add(tx)
    db.commit()
    db.refresh(tx)
    return tx

@router.get("/daily-summary", response_model=DailyStockSummary)
def get_daily_stock_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Computes real-time Daily Gold Stock Statement:
    - Vault inventory balance
    - Outstanding gold balance with karigars
    - Total fine gold in workshop
    - Today's issues, receipts, wastage, and loss alerts
    """
    # 1. Vault gold from inventory
    vault_items = db.query(GoldInventory).all()
    vault_gross = sum((Decimal(str(item.gross_weight)) for item in vault_items), Decimal("0.000"))
    vault_fine = sum((Decimal(str(item.fine_weight)) for item in vault_items), Decimal("0.000"))

    # 2. Karigar balances
    karigars = db.query(Karigar).filter(Karigar.is_active == True).all()
    all_issues = db.query(GoldTransaction).filter(GoldTransaction.transaction_type == TransactionType.ISSUE.value).all()
    all_receipts = db.query(GoldTransaction).filter(
        GoldTransaction.transaction_type.in_([
            TransactionType.RECEIPT_ORNAMENT.value,
            TransactionType.RECEIPT_SCRAP.value,
            TransactionType.RECEIPT_DUST.value
        ])
    ).all()

    total_issued_gross = sum((Decimal(str(tx.gross_weight)) for tx in all_issues), Decimal("0.000"))
    total_issued_fine = sum((Decimal(str(tx.fine_weight)) for tx in all_issues), Decimal("0.000"))

    total_received_gross = sum((Decimal(str(tx.gross_weight)) for tx in all_receipts), Decimal("0.000"))
    total_received_fine = sum((Decimal(str(tx.fine_weight)) for tx in all_receipts), Decimal("0.000"))

    opening_gross = sum((Decimal(str(k.opening_balance_gross or 0)) for k in karigars), Decimal("0.000"))
    opening_fine = sum((Decimal(str(k.opening_balance_fine or 0)) for k in karigars), Decimal("0.000"))

    karigar_outstanding_gross = round_weight(opening_gross + total_issued_gross - total_received_gross)
    karigar_outstanding_fine = round_weight(opening_fine + total_issued_fine - total_received_fine)

    total_workshop_fine = round_weight(vault_fine + karigar_outstanding_fine)

    # 3. Today's stats
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_txs = db.query(GoldTransaction).filter(GoldTransaction.created_at >= today_start).all()

    today_issues_gross = sum((Decimal(str(tx.gross_weight)) for tx in today_txs if tx.transaction_type == TransactionType.ISSUE.value), Decimal("0.000"))
    today_receipts_gross = sum((Decimal(str(tx.gross_weight)) for tx in today_txs if tx.transaction_type != TransactionType.ISSUE.value), Decimal("0.000"))
    today_wastage_gross = sum((Decimal(str(tx.actual_wastage_weight or 0)) for tx in today_txs), Decimal("0.000"))
    loss_alerts_count = sum(1 for tx in today_txs if tx.is_loss_alert)

    return DailyStockSummary(
        date=date.today().isoformat(),
        vault_raw_gold_gross=round_weight(vault_gross),
        vault_raw_gold_fine=round_weight(vault_fine),
        karigar_outstanding_gross=karigar_outstanding_gross,
        karigar_outstanding_fine=karigar_outstanding_fine,
        total_workshop_gold_fine=total_workshop_fine,
        total_issues_today_gross=round_weight(today_issues_gross),
        total_receipts_today_gross=round_weight(today_receipts_gross),
        total_wastage_today_gross=round_weight(today_wastage_gross),
        loss_alerts_count=loss_alerts_count
    )

