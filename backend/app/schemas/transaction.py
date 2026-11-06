from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from typing import Optional
from datetime import datetime
from app.schemas.agreements import Category

class TransactionCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra='forbid')
    transaction_type: str  # ISSUE, RECEIPT_ORNAMENT, RECEIPT_SCRAP, RECEIPT_DUST, WASTAGE_SETTLEMENT, LOSS_ADJUSTMENT, PURCHASE
    karigar_id: Optional[int] = None
    item_description: str = Field(min_length=1, max_length=255)
    job_number: str = Field(min_length=1, max_length=80, pattern=r'^[A-Za-z0-9][A-Za-z0-9 /_-]*$')
    item_category: Category
    huid: Optional[str] = Field(default=None, pattern=r'^[A-Z0-9]{6}$')
    gross_weight: Decimal = Field(..., gt=0, max_digits=10, decimal_places=3, description="Weight in grams to 3 decimal places")
    stone_weight: Decimal = Field(default=Decimal("0.000"), ge=0, max_digits=10, decimal_places=3)
    purity_percent: Decimal = Field(..., gt=0, le=100, decimal_places=2, description="Gold purity % (e.g. 91.60 for 22K)")
    allowed_wastage_percent: Optional[Decimal] = Field(default=Decimal("0.00"), ge=0, le=10, decimal_places=2)
    actual_wastage_weight: Optional[Decimal] = Field(default=Decimal("0.000"), ge=0, max_digits=10, decimal_places=3)
    scale_reading_confirmed: bool = False
    scale_image_url: Optional[str] = Field(default=None, max_length=500)
    scale_reading_id: Optional[str] = Field(default=None, max_length=36)
    idempotency_key: Optional[str] = Field(default=None, min_length=1, max_length=100)
    related_slip_number: Optional[str] = Field(default=None, max_length=100)
    notes: Optional[str] = Field(default=None, max_length=2000)

class TransactionResponse(BaseModel):
    id: int
    slip_number: str
    idempotency_key: Optional[str] = None
    related_slip_number: Optional[str] = None
    transaction_type: str
    karigar_id: Optional[int]
    karigar_name: Optional[str] = None
    karigar_code: Optional[str] = None
    created_by_user_id: Optional[int]
    item_description: str
    job_number: Optional[str] = None
    item_category: Optional[str] = None
    huid: Optional[str] = None
    gross_weight: Decimal
    stone_weight: Decimal
    net_weight: Decimal
    purity_percent: Decimal
    fine_weight: Decimal
    allowed_wastage_percent: Decimal
    actual_wastage_weight: Decimal
    wastage_variance_weight: Decimal
    is_loss_alert: bool
    scale_reading_confirmed: bool
    scale_image_url: Optional[str]
    notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TransactionDetail(BaseModel):
    transaction: TransactionResponse
    recorded_by_name: Optional[str] = None
    parent: Optional[TransactionResponse] = None
    linked_entries: list[TransactionResponse] = Field(default_factory=list)


class DailyStockSummary(BaseModel):
    date: str
    vault_raw_gold_gross: Decimal
    vault_raw_gold_fine: Decimal
    central_vault_gross: Decimal = Decimal("0.000")
    central_vault_fine: Decimal = Decimal("0.000")
    refiner_stock_gross: Decimal = Decimal("0.000")
    refiner_stock_fine: Decimal = Decimal("0.000")
    karigar_outstanding_gross: Decimal
    karigar_outstanding_fine: Decimal
    total_workshop_gold_fine: Decimal
    total_issues_today_gross: Decimal
    total_receipts_today_gross: Decimal
    total_legitimate_wastage_today_gross: Decimal
    total_legitimate_wastage_today_fine: Decimal
    cumulative_wastage_settled_gross: Decimal = Decimal("0.000")
    cumulative_wastage_settled_fine: Decimal = Decimal("0.000")
    total_wastage_today_gross: Decimal
    total_excess_wastage_today_gross: Decimal = Decimal("0.000")
    loss_alerts_count: int
    active_karigars_with_balance_count: int = 0
    pending_reconciliations_count: int = 0
