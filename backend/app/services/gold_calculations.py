"""
Gold Calculations Service for KarigarFlow Jewellery ERP.

CRITICAL ENGINEERING RULES:
1. Never use floating-point numbers for weights, purities, or balances.
   Always use Python Decimal with explicit rounding (ROUND_HALF_UP).
   - Weights: 3 decimal places (0.001 g precision, standard in Indian jewellery workshops).
   - Purity: 2 decimal places (e.g., 91.60 for 22K 916 Hallmark, 75.00 for 18K).
   - Percentage: 2 decimal places.
2. Clearly distinguish between Gross Weight (scale physical weight) and Fine Gold (pure 24K equivalent).
3. Validate balance boundaries to prevent unaccounted negative physical balances.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import NamedTuple, Any, List

PRECISION_WEIGHT = Decimal("0.001")
PRECISION_PURITY = Decimal("0.01")
PRECISION_CURRENCY = Decimal("0.01")
ONE_HUNDRED = Decimal("100.00")
ZERO_WEIGHT = Decimal("0.000")

def round_weight(val: Any) -> Decimal:
    """Rounds gold weight to 3 decimal places (milligram precision)."""
    d = Decimal(str(val)) if not isinstance(val, Decimal) else val
    return d.quantize(PRECISION_WEIGHT, rounding=ROUND_HALF_UP)

def round_purity(val: Any) -> Decimal:
    """Rounds gold purity percentage to 2 decimal places."""
    d = Decimal(str(val)) if not isinstance(val, Decimal) else val
    return d.quantize(PRECISION_PURITY, rounding=ROUND_HALF_UP)

def calculate_fine_gold(gross_weight: Any, purity_percent: Any) -> Decimal:
    """
    Calculates pure fine gold (24K equivalent) from gross weight and purity percentage.
    Formula: Fine Gold = (Gross Weight * Purity) / 100
    """
    gross = Decimal(str(gross_weight))
    purity = Decimal(str(purity_percent))
    fine = (gross * purity) / ONE_HUNDRED
    return round_weight(fine)

def calculate_net_weight(gross_weight: Any, stone_weight: Any = Decimal("0.000"), dust_weight: Any = Decimal("0.000")) -> Decimal:
    """
    Calculates net gold weight by subtracting stones, beads, enamel, or dust weight.
    """
    gross = Decimal(str(gross_weight))
    stone = Decimal(str(stone_weight))
    dust = Decimal(str(dust_weight))
    net = gross - (stone + dust)
    return round_weight(net)

class WastageResult(NamedTuple):
    allowed_wastage_grams: Decimal
    actual_wastage_grams: Decimal
    wastage_variance_grams: Decimal
    is_loss_alert: bool
    actual_wastage_percentage: Decimal

def calculate_wastage(
    issued_weight: Any,
    returned_ornament_weight: Any,
    returned_scrap_weight: Any,
    returned_dust_weight: Any,
    allowed_wastage_percent: Any,
    loss_alert_threshold_grams: Any = Decimal("0.100")
) -> WastageResult:
    """
    Wastage Accounting in Jewellery Manufacturing:
    Issued: Total gold issued to karigar for job
    Returned: Finished ornaments + Scrap/Melting cuttings + Filing dust/polish recovered
    Actual Wastage = Issued - (Returned Ornaments + Scrap + Dust)
    Allowed Wastage = (Issued * Allowed Wastage %) / 100
    Variance = Actual Wastage - Allowed Wastage
    If Variance > loss_alert_threshold_grams -> triggers Loss Alert!
    """
    issued = Decimal(str(issued_weight))
    ornament = Decimal(str(returned_ornament_weight))
    scrap = Decimal(str(returned_scrap_weight))
    dust = Decimal(str(returned_dust_weight))
    allowed_pct = Decimal(str(allowed_wastage_percent))
    threshold = Decimal(str(loss_alert_threshold_grams))

    total_recovered = ornament + scrap + dust
    actual_wastage = issued - total_recovered

    allowed_wastage = (issued * allowed_pct) / ONE_HUNDRED
    allowed_wastage_rounded = round_weight(allowed_wastage)
    actual_wastage_rounded = round_weight(actual_wastage)

    variance = round_weight(actual_wastage_rounded - allowed_wastage_rounded)

    if issued > ZERO_WEIGHT:
        actual_pct = round_purity((actual_wastage_rounded / issued) * ONE_HUNDRED)
    else:
        actual_pct = Decimal("0.00")

    is_alert = variance > threshold

    return WastageResult(
        allowed_wastage_grams=allowed_wastage_rounded,
        actual_wastage_grams=actual_wastage_rounded,
        wastage_variance_grams=variance,
        is_loss_alert=is_alert,
        actual_wastage_percentage=actual_pct
    )

class KarigarBalance(NamedTuple):
    opening_balance_gross: Decimal
    opening_balance_fine: Decimal
    total_issued_gross: Decimal
    total_issued_fine: Decimal
    total_returned_gross: Decimal
    total_returned_fine: Decimal
    total_wastage_settled_gross: Decimal
    total_wastage_settled_fine: Decimal
    closing_balance_gross: Decimal
    closing_balance_fine: Decimal

def compute_karigar_balance(
    opening_gross: Any,
    opening_fine: Any,
    issued_transactions: list,
    received_transactions: list,
    account_for_settled_wastage: bool = True
) -> KarigarBalance:
    """
    Computes real-time gross and fine gold balances for a karigar.
    Never hardcode balances: always compute from transactional entries.
    
    Balance Mechanics:
    - Gross Balance represents the physical gold weight (grams) held by the karigar.
    - Fine Balance represents the pure 24K equivalent held.
    - Issued gold INCREASES the karigar's balance.
    - Received gold (ornaments, scrap, dust) DECREASES the karigar's balance.
    - When a job receipt settles verified craft wastage, that wastage weight is also
      relieved from the karigar's physical custody.
    """
    issued_gross = sum((Decimal(str(getattr(tx, 'gross_weight', 0))) for tx in issued_transactions), ZERO_WEIGHT)
    issued_fine = sum((Decimal(str(getattr(tx, 'fine_weight', 0))) for tx in issued_transactions), ZERO_WEIGHT)
    
    received_gross = sum((Decimal(str(getattr(tx, 'gross_weight', 0))) for tx in received_transactions), ZERO_WEIGHT)
    received_fine = sum((Decimal(str(getattr(tx, 'fine_weight', 0))) for tx in received_transactions), ZERO_WEIGHT)

    wastage_gross = ZERO_WEIGHT
    wastage_fine = ZERO_WEIGHT
    if account_for_settled_wastage:
        for tx in received_transactions:
            w_gross = Decimal(str(getattr(tx, 'actual_wastage_weight', 0) or 0))
            if w_gross > ZERO_WEIGHT:
                wastage_gross += w_gross
                purity = Decimal(str(getattr(tx, 'purity_percent', 0) or 0))
                wastage_fine += calculate_fine_gold(w_gross, purity)

    closing_gross = Decimal(str(opening_gross)) + issued_gross - received_gross - wastage_gross
    closing_fine = Decimal(str(opening_fine)) + issued_fine - received_fine - wastage_fine

    return KarigarBalance(
        opening_balance_gross=round_weight(opening_gross),
        opening_balance_fine=round_weight(opening_fine),
        total_issued_gross=round_weight(issued_gross),
        total_issued_fine=round_weight(issued_fine),
        total_returned_gross=round_weight(received_gross),
        total_returned_fine=round_weight(received_fine),
        total_wastage_settled_gross=round_weight(wastage_gross),
        total_wastage_settled_fine=round_weight(wastage_fine),
        closing_balance_gross=round_weight(closing_gross),
        closing_balance_fine=round_weight(closing_fine)
    )

def validate_transaction_balance(
    current_gross_balance: Decimal,
    transaction_type: str,
    transaction_gross_weight: Decimal,
    allow_negative_override: bool = False
) -> None:
    """
    Validates that a receipt transaction does not exceed the karigar's active physical gold balance.
    Prevents erroneous negative balance entries without explicit managerial override.
    """
    if transaction_type in ["RECEIPT_ORNAMENT", "RECEIPT_SCRAP", "RECEIPT_DUST"]:
        if transaction_gross_weight > current_gross_balance and not allow_negative_override:
            raise ValueError(
                f"Insufficient karigar balance: attempted return of {transaction_gross_weight}g "
                f"exceeds current balance of {current_gross_balance}g."
            )
