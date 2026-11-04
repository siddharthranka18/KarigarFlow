from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional
from datetime import datetime

class InventoryItemBase(BaseModel):
    lot_code: str
    category: str
    description: str
    gross_weight: Decimal = Field(..., gt=0, decimal_places=3)
    purity_percent: Decimal = Field(..., gt=0, le=100, decimal_places=2)
    location: str = "Coimbatore Central Workshop Vault"

class InventoryItemCreate(InventoryItemBase):
    pass

class InventoryItemResponse(InventoryItemBase):
    id: int
    fine_weight: Decimal
    updated_at: datetime

    class Config:
        from_attributes = True

