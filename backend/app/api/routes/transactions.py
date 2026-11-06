from fastapi import APIRouter, Depends, HTTPException, status, Query, Header
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
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
    compute_karigar_balance,
    validate_transaction_balance,
    round_weight
)
from app.services.inventory_service import compute_vault_custody_position
from app.services.loss_alerts import unresolved_loss_conditions
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

    # Karigar role can ONLY see their own transactions (Assumption 3)
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
        query = query.filter(*unresolved_loss_conditions())

    return query.order_by(GoldTransaction.created_at.desc()).limit(limit).all()

@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
def create_transaction(
    payload: TransactionCreate,
    idempotency_key_header: Optional[str] = Header(None, alias="Idempotency-Key"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        UserRole.ADMIN.value,
        UserRole.FINANCE_HEAD.value,
        UserRole.WORKSHOP_MANAGER.value,
        UserRole.ISSUE_CLERK.value
    ]))
):
    if payload.transaction_type not in {'ISSUE', 'RECEIPT_ORNAMENT', 'RECEIPT_SCRAP', 'RECEIPT_DUST', 'PURCHASE'}:
        raise HTTPException(status_code=400, detail='This transaction type requires its dedicated approval workflow')
    if any(key and key.startswith('loss-resolution:') for key in (idempotency_key_header, payload.idempotency_key)):
        raise HTTPException(status_code=400, detail='Reserved idempotency key')

    # 1. Idempotency Check: prevent duplicate accounting entries on retries
    idemp_key = idempotency_key_header or payload.idempotency_key
    if idemp_key:
        existing_tx = db.query(GoldTransaction).filter(GoldTransaction.idempotency_key == idemp_key).first()
        if existing_tx:
            # Idempotent replay: return existing transaction without creating duplicate entry
            return existing_tx

    # 2. Validate Karigar
    karigar = None
    if payload.transaction_type in [
        TransactionType.ISSUE.value,
        TransactionType.RECEIPT_ORNAMENT.value,
        TransactionType.RECEIPT_SCRAP.value,
        TransactionType.RECEIPT_DUST.value,
        TransactionType.WASTAGE_SETTLEMENT.value,
        TransactionType.LOSS_ADJUSTMENT.value
    ]:
        if not payload.karigar_id:
            raise HTTPException(status_code=400, detail="karigar_id is required for workshop slips")
        # Serialize custody changes for the same craftsman until commit/rollback.
        karigar = db.query(Karigar).filter(Karigar.id == payload.karigar_id).with_for_update().first()
        if not karigar:
            raise HTTPException(status_code=404, detail="Karigar not found")

    # A concurrent retry may have finished while we waited for the custody lock.
    if idemp_key:
        existing_tx = db.query(GoldTransaction).filter(GoldTransaction.idempotency_key == idemp_key).first()
        if existing_tx:
            return existing_tx

    # 3. Safe decimal calculations
    net_weight = calculate_net_weight(payload.gross_weight, payload.stone_weight)
    if net_weight <= Decimal("0.000"):
        raise HTTPException(status_code=400, detail="Net gold weight must be strictly greater than 0")

    fine_weight = calculate_fine_gold(net_weight, payload.purity_percent)

    allowed_pct = payload.allowed_wastage_percent or Decimal("0.00")
    actual_wastage = payload.actual_wastage_weight or Decimal("0.000")
    allowed_wastage_weight = round_weight((payload.gross_weight * allowed_pct) / Decimal("100.00"))
    legitimate_wastage = (
        min(actual_wastage, allowed_wastage_weight)
        if payload.transaction_type == TransactionType.RECEIPT_ORNAMENT.value
        else Decimal("0.000")
    )
    wastage_fine = calculate_fine_gold(legitimate_wastage, payload.purity_percent)

    # 4. Validate sufficient balance on receipts
    if karigar and payload.transaction_type in [
        TransactionType.RECEIPT_ORNAMENT.value,
        TransactionType.RECEIPT_SCRAP.value,
        TransactionType.RECEIPT_DUST.value
    ]:
        issued_txs = db.query(GoldTransaction).filter(
            GoldTransaction.karigar_id == karigar.id,
            GoldTransaction.transaction_type == TransactionType.ISSUE.value
        ).all()
        settled_txs = db.query(GoldTransaction).filter(
            GoldTransaction.karigar_id == karigar.id,
            GoldTransaction.transaction_type.in_([
                TransactionType.RECEIPT_ORNAMENT.value,
                TransactionType.RECEIPT_SCRAP.value,
                TransactionType.RECEIPT_DUST.value,
                TransactionType.WASTAGE_SETTLEMENT.value,
                TransactionType.LOSS_ADJUSTMENT.value
            ])
        ).all()
        current_bal = compute_karigar_balance(
            karigar.opening_balance_gross,
            karigar.opening_balance_fine,
            issued_txs,
            settled_txs
        )
        try:
            validate_transaction_balance(
                current_gross_balance=current_bal.closing_balance_gross,
                transaction_type=payload.transaction_type,
                transaction_gross_weight=payload.gross_weight + legitimate_wastage
            )
            if fine_weight + wastage_fine > current_bal.closing_balance_fine:
                raise ValueError("Receipt and approved wastage exceed available fine gold balance")
        except ValueError as err:
            raise HTTPException(status_code=400, detail=str(err))

    # 5. Wastage and loss alert logic
    wastage_variance = round_weight(actual_wastage - allowed_wastage_weight)

    is_alert = False
    if payload.transaction_type == TransactionType.RECEIPT_ORNAMENT.value:
        if wastage_variance > settings.LOSS_ALERT_THRESHOLD_GRAMS:
            is_alert = True

    # 6. Generate sequential unique slip code
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y%m%d")
    short_uuid = str(uuid.uuid4())[:5].upper()
    prefix_map = {
        TransactionType.ISSUE.value: "ISS",
        TransactionType.RECEIPT_ORNAMENT.value: "REC",
        TransactionType.RECEIPT_SCRAP.value: "SCP",
        TransactionType.RECEIPT_DUST.value: "DST",
        TransactionType.WASTAGE_SETTLEMENT.value: "WST",
        TransactionType.LOSS_ADJUSTMENT.value: "ADJ",
        TransactionType.PURCHASE.value: "PUR"
    }
    prefix = prefix_map.get(payload.transaction_type, "SLP")
    slip_number = f"{prefix}-{date_str}-{short_uuid}"

    tx = GoldTransaction(
        slip_number=slip_number,
        idempotency_key=idemp_key,
        related_slip_number=payload.related_slip_number,
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

    # 7. Auditable Wastage Accounting:
    # If this is a finished jewellery receipt reporting legitimate wastage,
    # generate an explicit, linked WASTAGE_SETTLEMENT slip in the transaction history
    if payload.transaction_type == TransactionType.RECEIPT_ORNAMENT.value and actual_wastage > Decimal("0.000"):
        if legitimate_wastage > Decimal("0.000"):
            wst_uuid = str(uuid.uuid4())[:5].upper()
            wst_slip = f"WST-{date_str}-{wst_uuid}"
            wst_fine = calculate_fine_gold(legitimate_wastage, payload.purity_percent)
            wastage_tx = GoldTransaction(
                slip_number=wst_slip,
                related_slip_number=tx.slip_number,
                transaction_type=TransactionType.WASTAGE_SETTLEMENT.value,
                karigar_id=payload.karigar_id,
                created_by_user_id=current_user.id,
                item_description=f"Approved Craft Wastage Allowance for Slip {tx.slip_number}",
                gross_weight=legitimate_wastage,
                stone_weight=Decimal("0.000"),
                net_weight=legitimate_wastage,
                purity_percent=payload.purity_percent,
                fine_weight=wst_fine,
                allowed_wastage_percent=allowed_pct,
                actual_wastage_weight=actual_wastage,
                wastage_variance_weight=wastage_variance,
                is_loss_alert=False,
                scale_reading_confirmed=True,
                notes=f"Auditable craft wastage settlement linked to parent slip {tx.slip_number}"
            )
            db.add(wastage_tx)

    # Receipt and settlement form one accounting operation: both save or neither.
    try:
        db.commit()
        db.refresh(tx)
    except IntegrityError:
        db.rollback()
        if idemp_key:
            existing_tx = db.query(GoldTransaction).filter(GoldTransaction.idempotency_key == idemp_key).first()
            if existing_tx:
                return existing_tx
        raise HTTPException(status_code=400, detail="Database integrity constraint violation")
    except Exception:
        db.rollback()
        raise

    return tx

@router.get("/daily-summary", response_model=DailyStockSummary)
def get_daily_stock_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        UserRole.ADMIN.value,
        UserRole.FINANCE_HEAD.value,
        UserRole.WORKSHOP_MANAGER.value,
        UserRole.ISSUE_CLERK.value
    ]))
):
    """
    Computes real-time Daily Gold Stock Statement.
    Distinguishes:
    - Central Vault Fine Gold
    - Outstanding Karigar Fine Gold (physical bench stock)
    - Legitimate Wastage Consumed Today
    - Excess Wastage Loss Alerts Requiring Investigation
    """
    # 1. Compute perpetual Central Vault & Refinery custody balances
    # Enforces Invariant: Closing Vault Fine = Opening Vault Fine - Fine Issued + Fine Physically Returned + Purchases
    vault_pos = compute_vault_custody_position(db)
    central_gross = vault_pos.closing_central_vault_gross
    central_fine = vault_pos.closing_central_vault_fine
    refiner_gross = vault_pos.closing_refinery_gross
    refiner_fine = vault_pos.closing_refinery_fine
    vault_gross = round_weight(central_gross + refiner_gross)
    vault_fine = round_weight(vault_pos.total_vault_and_refinery_fine)

    # 2. Karigar balances
    karigars = db.query(Karigar).filter(Karigar.is_active == True).all()
    all_issues = db.query(GoldTransaction).filter(GoldTransaction.transaction_type == TransactionType.ISSUE.value).all()
    all_settled = db.query(GoldTransaction).filter(
        GoldTransaction.transaction_type.in_([
            TransactionType.RECEIPT_ORNAMENT.value,
            TransactionType.RECEIPT_SCRAP.value,
            TransactionType.RECEIPT_DUST.value,
            TransactionType.WASTAGE_SETTLEMENT.value,
            TransactionType.LOSS_ADJUSTMENT.value
        ])
    ).all()

    total_issued_gross = sum((Decimal(str(tx.gross_weight)) for tx in all_issues), Decimal("0.000"))
    total_issued_fine = sum((Decimal(str(tx.fine_weight)) for tx in all_issues), Decimal("0.000"))

    total_settled_gross = sum((Decimal(str(tx.gross_weight)) for tx in all_settled), Decimal("0.000"))
    total_settled_fine = sum((Decimal(str(tx.fine_weight)) for tx in all_settled), Decimal("0.000"))

    opening_gross = sum((Decimal(str(k.opening_balance_gross or 0)) for k in karigars), Decimal("0.000"))
    opening_fine = sum((Decimal(str(k.opening_balance_fine or 0)) for k in karigars), Decimal("0.000"))

    karigar_outstanding_gross = round_weight(opening_gross + total_issued_gross - total_settled_gross)
    karigar_outstanding_fine = round_weight(opening_fine + total_issued_fine - total_settled_fine)

    total_workshop_fine = round_weight(vault_fine + karigar_outstanding_fine)

    # Count karigars who currently hold unreturned gold on bench
    active_karigars_with_balance = 0
    for k in karigars:
        k_issues = [t for t in all_issues if t.karigar_id == k.id]
        k_settled = [t for t in all_settled if t.karigar_id == k.id]
        k_bal = compute_karigar_balance(
            k.opening_balance_gross,
            k.opening_balance_fine,
            k_issues,
            k_settled
        )
        if k_bal.closing_balance_gross > Decimal("0.000"):
            active_karigars_with_balance += 1

    # 3. Today's stats
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_txs = db.query(GoldTransaction).filter(GoldTransaction.created_at >= today_start).all()

    today_issues_gross = sum((Decimal(str(tx.gross_weight)) for tx in today_txs if tx.transaction_type == TransactionType.ISSUE.value), Decimal("0.000"))
    today_receipts_gross = sum((Decimal(str(tx.gross_weight)) for tx in today_txs if tx.transaction_type in [
        TransactionType.RECEIPT_ORNAMENT.value,
        TransactionType.RECEIPT_SCRAP.value,
        TransactionType.RECEIPT_DUST.value
    ]), Decimal("0.000"))
    
    today_wastage_settled_gross = sum((Decimal(str(tx.gross_weight)) for tx in today_txs if tx.transaction_type == TransactionType.WASTAGE_SETTLEMENT.value), Decimal("0.000"))
    today_wastage_settled_fine = sum((Decimal(str(tx.fine_weight)) for tx in today_txs if tx.transaction_type == TransactionType.WASTAGE_SETTLEMENT.value), Decimal("0.000"))
    
    cumulative_wastage_settled_gross = sum(
        (Decimal(str(tx.gross_weight)) for tx in all_settled if tx.transaction_type == TransactionType.WASTAGE_SETTLEMENT.value),
        Decimal("0.000")
    )
    cumulative_wastage_settled_fine = sum(
        (Decimal(str(tx.fine_weight)) for tx in all_settled if tx.transaction_type == TransactionType.WASTAGE_SETTLEMENT.value),
        Decimal("0.000")
    )

    today_wastage_reported_gross = sum((Decimal(str(tx.actual_wastage_weight or 0)) for tx in today_txs if tx.transaction_type == TransactionType.RECEIPT_ORNAMENT.value), Decimal("0.000"))
    today_excess_wastage_gross = sum((Decimal(str(tx.wastage_variance_weight or 0)) for tx in today_txs if tx.is_loss_alert and tx.transaction_type == 'RECEIPT_ORNAMENT'), Decimal("0.000"))
    
    total_loss_alerts_count = db.query(GoldTransaction).filter(*unresolved_loss_conditions()).count()

    return DailyStockSummary(
        date=date.today().isoformat(),
        vault_raw_gold_gross=round_weight(vault_gross),
        vault_raw_gold_fine=round_weight(vault_fine),
        central_vault_gross=round_weight(central_gross),
        central_vault_fine=round_weight(central_fine),
        refiner_stock_gross=round_weight(refiner_gross),
        refiner_stock_fine=round_weight(refiner_fine),
        karigar_outstanding_gross=karigar_outstanding_gross,
        karigar_outstanding_fine=karigar_outstanding_fine,
        total_workshop_gold_fine=total_workshop_fine,
        total_issues_today_gross=round_weight(today_issues_gross),
        total_receipts_today_gross=round_weight(today_receipts_gross),
        total_legitimate_wastage_today_gross=round_weight(today_wastage_settled_gross),
        total_legitimate_wastage_today_fine=round_weight(today_wastage_settled_fine),
        cumulative_wastage_settled_gross=round_weight(cumulative_wastage_settled_gross),
        cumulative_wastage_settled_fine=round_weight(cumulative_wastage_settled_fine),
        total_wastage_today_gross=round_weight(today_wastage_reported_gross),
        total_excess_wastage_today_gross=round_weight(today_excess_wastage_gross),
        loss_alerts_count=total_loss_alerts_count,
        active_karigars_with_balance_count=active_karigars_with_balance,
        pending_reconciliations_count=active_karigars_with_balance
    )
