from pydantic import BaseModel, Field, ConfigDict, model_validator
from decimal import Decimal
from typing import Optional
from datetime import datetime
from app.schemas.agreements import Category, Percent

class KarigarBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    karigar_code: str = Field(min_length=1, max_length=50, pattern=r'^[A-Z0-9-]+$')
    name: str = Field(min_length=1, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    specialization: str = Field(default='General Jewellery', min_length=1, max_length=100)
    benchmark_wastage_percent: Decimal = Field(default=Decimal("2.00"), ge=0, le=10)
    wastage_by_category: dict[Category, Percent] = Field(default_factory=dict)

class KarigarCreate(KarigarBase):
    opening_balance_gross: Decimal = Field(default=Decimal('0.000'), ge=0, decimal_places=3, max_digits=10)
    opening_balance_fine: Decimal = Field(default=Decimal('0.000'), ge=0, decimal_places=3, max_digits=10)

    @model_validator(mode='after')
    def valid_opening(self):
        if self.opening_balance_fine > self.opening_balance_gross:
            raise ValueError('Opening fine gold cannot exceed opening gross weight')
        return self

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

