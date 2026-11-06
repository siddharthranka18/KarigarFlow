from datetime import date
from decimal import Decimal
from pydantic import BaseModel


class StockRow(BaseModel):
    location: str
    unit: str
    opening: Decimal
    issues: Decimal
    receipts: Decimal
    purchases: Decimal
    wastage: Decimal
    loss_adjustments: Decimal
    closing: Decimal


class StockStatement(BaseModel):
    date: date
    timezone: str = "Asia/Kolkata"
    transaction_count: int
    rows: list[StockRow]
