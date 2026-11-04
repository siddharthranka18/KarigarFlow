from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from typing import Optional
from datetime import datetime

class KarigarBase(BaseModel):
    karigar_code: str
    name: str
    phone: Optional[str] = None
    specialization: str = "General Jewellery"
    benchmark_wastage_percent: Decimal = Field(default=Decimal("2.00"), ge=0, le=10)

class KarigarCreate(KarigarBase):
    opening_balance_gross: Decimal = Decimal("0.000")
    opening_balance_fine: Decimal = Decimal("0.000")

class KarigarUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    specialization: Optional[str] = None
    benchmark_wastage_percent: Optional[Decimal] = None
    is_active: Optional[bool] = None

class KarigarResponse(KarigarBase):
    id: int
    opening_balance_gross: Decimal
    opening_balance_fine: Decimal
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class KarigarWithBalance(KarigarResponse):
    current_balance_gross: Decimal
    current_balance_fine: Decimal
    total_issued_gross: Decimal
    total_returned_gross: Decimal
    active_jobs_count: int
    loss_alerts_count: int

