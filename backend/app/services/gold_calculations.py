"""
Gold Calculations Service for KarigarFlow Jewellery ERP.

CRITICAL ENGINEERING RULES:
1. Never use floating-point numbers for weights, purities, or balances.
   Always use Python Decimal with explicit rounding (ROUND_HALF_UP).
   - Weights: 3 decimal places (0.001 g precision, standard in Indian jewellery workshops).
   - Purity: 2 decimal places (e.g., 91.60 for 22K 916 Hallmark, 75.00 for 18K).
   - Percentage: 2 decimal places.
2. Clearly distinguish between Gross Weight (scale physical weight) and Fine Gold (pure 24K equivalent).
3. Auditable Double-Entry Rule:
   Wastage is accounted for exclusively via explicit WASTAGE_SETTLEMENT transactions.
   Never double-deduct wastage metadata from receipt slips.
"""

from decimal import Decimal, ROUND_HALF_UP
from typing import NamedTuple, Any

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
    total_loss_adjusted_gross: Decimal
    total_loss_adjusted_fine: Decimal
    closing_balance_gross: Decimal
    closing_balance_fine: Decimal

def compute_karigar_balance(
    opening_gross: Any,
    opening_fine: Any,
    issued_transactions: list,
    settled_transactions: list = None,
    received_transactions: list = None
) -> KarigarBalance:
    """
    Computes real-time gross and fine gold balances for a karigar from explicit transactions.
    
    Balance Mechanics:
    - Issued transactions (ISSUE) increase the karigar's bench custody (+).
    - Physical returned transactions (RECEIPT_ORNAMENT, RECEIPT_SCRAP, RECEIPT_DUST) decrease custody (-).
    - Legitimate settled wastage transactions (WASTAGE_SETTLEMENT) relieve custody (-).
    - Excess wastage loss adjustments (LOSS_ADJUSTMENT) relieve custody (-).
    - Each category is strictly aggregated from explicit ledger entries with zero double-counting.
    """
    tx_list = settled_transactions if settled_transactions is not None else (received_transactions or [])
    issued_gross = sum((Decimal(str(getattr(tx, 'gross_weight', 0))) for tx in issued_transactions), ZERO_WEIGHT)
    issued_fine = sum((Decimal(str(getattr(tx, 'fine_weight', 0))) for tx in issued_transactions), ZERO_WEIGHT)
    
    physical_types = {"RECEIPT_ORNAMENT", "RECEIPT_SCRAP", "RECEIPT_DUST"}
    returned_gross = ZERO_WEIGHT
    returned_fine = ZERO_WEIGHT
    wastage_settled_gross = ZERO_WEIGHT
    wastage_settled_fine = ZERO_WEIGHT
    loss_adjusted_gross = ZERO_WEIGHT
    loss_adjusted_fine = ZERO_WEIGHT

    for tx in tx_list:
        tx_type = getattr(tx, 'transaction_type', '')
        g_wt = Decimal(str(getattr(tx, 'gross_weight', 0) or 0))
        f_wt = Decimal(str(getattr(tx, 'fine_weight', 0) or 0))

        if tx_type in physical_types:
            returned_gross += g_wt
            returned_fine += f_wt
        elif tx_type == "WASTAGE_SETTLEMENT":
            wastage_settled_gross += g_wt
            wastage_settled_fine += f_wt
        elif tx_type == "LOSS_ADJUSTMENT":
            loss_adjusted_gross += g_wt
            loss_adjusted_fine += f_wt
        else:
            # Default fallback for untyped or legacy receipts
            returned_gross += g_wt
            returned_fine += f_wt

    total_credits_gross = returned_gross + wastage_settled_gross + loss_adjusted_gross
    total_credits_fine = returned_fine + wastage_settled_fine + loss_adjusted_fine

    closing_gross = Decimal(str(opening_gross)) + issued_gross - total_credits_gross
    closing_fine = Decimal(str(opening_fine)) + issued_fine - total_credits_fine

    return KarigarBalance(
        opening_balance_gross=round_weight(opening_gross),
        opening_balance_fine=round_weight(opening_fine),
        total_issued_gross=round_weight(issued_gross),
        total_issued_fine=round_weight(issued_fine),
        total_returned_gross=round_weight(returned_gross),
        total_returned_fine=round_weight(returned_fine),
        total_wastage_settled_gross=round_weight(wastage_settled_gross),
        total_wastage_settled_fine=round_weight(wastage_settled_fine),
        total_loss_adjusted_gross=round_weight(loss_adjusted_gross),
        total_loss_adjusted_fine=round_weight(loss_adjusted_fine),
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
    Validates that a physical receipt transaction does not exceed the karigar's active physical gold balance.
    Prevents erroneous negative balance entries without explicit managerial override.
    """
    if transaction_type in ["RECEIPT_ORNAMENT", "RECEIPT_SCRAP", "RECEIPT_DUST"]:
        if transaction_gross_weight > current_gross_balance and not allow_negative_override:
            raise ValueError(
                f"Insufficient karigar balance: attempted return of {transaction_gross_weight}g "
                f"exceeds current balance of {current_gross_balance}g."
            )
