from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal
from app.db.session import get_db
from app.models.karigar import Karigar
from app.models.transaction import GoldTransaction, TransactionType
from app.models.user import User, UserRole
from app.schemas.karigar import KarigarCreate, KarigarUpdate, KarigarResponse, KarigarWithBalance
from app.api.dependencies import get_current_user, require_roles
from app.services.gold_calculations import compute_karigar_balance, round_weight

router = APIRouter(prefix="/karigars", tags=["Karigars"])

def enrich_karigar_balance(karigar: Karigar, db: Session) -> KarigarWithBalance:
    """Calculates live gross and fine gold balances for a karigar from transaction history."""
    issued_txs = db.query(GoldTransaction).filter(
        GoldTransaction.karigar_id == karigar.id,
        GoldTransaction.transaction_type == TransactionType.ISSUE.value
    ).all()

    received_txs = db.query(GoldTransaction).filter(
        GoldTransaction.karigar_id == karigar.id,
        GoldTransaction.transaction_type.in_([
            TransactionType.RECEIPT_ORNAMENT.value,
            TransactionType.RECEIPT_SCRAP.value,
            TransactionType.RECEIPT_DUST.value,
            TransactionType.WASTAGE_SETTLEMENT.value,
            TransactionType.LOSS_ADJUSTMENT.value
        ])
    ).all()

    loss_alerts_count = db.query(GoldTransaction).filter(
        GoldTransaction.karigar_id == karigar.id,
        GoldTransaction.is_loss_alert == True
    ).count()

    balance = compute_karigar_balance(
        opening_gross=Decimal(str(karigar.opening_balance_gross or 0)),
        opening_fine=Decimal(str(karigar.opening_balance_fine or 0)),
        issued_transactions=issued_txs,
        received_transactions=received_txs
    )

    return KarigarWithBalance(
        id=karigar.id,
        karigar_code=karigar.karigar_code,
        name=karigar.name,
        phone=karigar.phone,
        specialization=karigar.specialization,
        benchmark_wastage_percent=Decimal(str(karigar.benchmark_wastage_percent)),
        opening_balance_gross=Decimal(str(karigar.opening_balance_gross)),
        opening_balance_fine=Decimal(str(karigar.opening_balance_fine)),
        is_active=karigar.is_active,
        created_at=karigar.created_at,
        current_balance_gross=balance.closing_balance_gross,
        current_balance_fine=balance.closing_balance_fine,
        total_issued_gross=balance.total_issued_gross,
        total_returned_gross=balance.total_returned_gross,
        active_jobs_count=len(issued_txs),
        loss_alerts_count=loss_alerts_count
    )

@router.get("", response_model=List[KarigarWithBalance])
def list_karigars(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List karigars.
    - If user is a Karigar, returns only their own profile.
    - Workshop staff see all karigars.
    """
    query = db.query(Karigar).filter(Karigar.is_active == True)
    
    if current_user.role == UserRole.KARIGAR.value:
        query = query.filter(Karigar.user_id == current_user.id)

    karigars = query.order_by(Karigar.karigar_code).all()
    return [enrich_karigar_balance(k, db) for k in karigars]

@router.get("/{karigar_id}", response_model=KarigarWithBalance)
def get_karigar(
    karigar_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    karigar = db.query(Karigar).filter(Karigar.id == karigar_id).first()
    if not karigar:
        raise HTTPException(status_code=404, detail="Karigar not found")

    if current_user.role == UserRole.KARIGAR.value and karigar.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied to other karigar records")

    return enrich_karigar_balance(karigar, db)

@router.post("", response_model=KarigarResponse, status_code=status.HTTP_201_CREATED)
def create_karigar(
    payload: KarigarCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.FINANCE_HEAD.value, UserRole.WORKSHOP_MANAGER.value]))
):
    existing = db.query(Karigar).filter(Karigar.karigar_code == payload.karigar_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Karigar with this code already exists")

    karigar = Karigar(
        karigar_code=payload.karigar_code,
        name=payload.name,
        phone=payload.phone,
        specialization=payload.specialization,
        benchmark_wastage_percent=payload.benchmark_wastage_percent,
        opening_balance_gross=payload.opening_balance_gross,
        opening_balance_fine=payload.opening_balance_fine,
        is_active=True
    )
    db.add(karigar)
    db.commit()
    db.refresh(karigar)
    return karigar

