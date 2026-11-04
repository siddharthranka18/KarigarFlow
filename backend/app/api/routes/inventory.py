from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal
from app.db.session import get_db
from app.models.inventory import GoldInventory
from app.models.user import User, UserRole
from app.schemas.inventory import InventoryItemCreate, InventoryItemResponse
from app.api.dependencies import get_current_user, require_roles
from app.services.gold_calculations import calculate_fine_gold

router = APIRouter(prefix="/inventory", tags=["Inventory"])

@router.get("", response_model=List[InventoryItemResponse])
def list_inventory(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([
        UserRole.ADMIN.value,
        UserRole.FINANCE_HEAD.value,
        UserRole.WORKSHOP_MANAGER.value,
        UserRole.ISSUE_CLERK.value
    ]))
):
    """
    Lists current vault lots of bullion, alloys, and scrap.
    Protected endpoint: Karigars cannot view company vault holdings (Assumption 3).
    """
    return db.query(GoldInventory).order_by(GoldInventory.category, GoldInventory.lot_code).all()

@router.post("", response_model=InventoryItemResponse, status_code=status.HTTP_201_CREATED)
def create_inventory_lot(
    payload: InventoryItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles([UserRole.ADMIN.value, UserRole.FINANCE_HEAD.value, UserRole.WORKSHOP_MANAGER.value]))
):
    existing = db.query(GoldInventory).filter(GoldInventory.lot_code == payload.lot_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Lot with this code already exists")

    fine_weight = calculate_fine_gold(payload.gross_weight, payload.purity_percent)

    item = GoldInventory(
        lot_code=payload.lot_code,
        category=payload.category,
        description=payload.description,
        gross_weight=payload.gross_weight,
        purity_percent=payload.purity_percent,
        fine_weight=fine_weight,
        location=payload.location
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
