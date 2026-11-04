import pytest
from decimal import Decimal
from app.services.gold_calculations import (
    calculate_fine_gold,
    calculate_net_weight,
    calculate_wastage,
    compute_karigar_balance,
    validate_transaction_balance,
    round_weight,
    round_purity
)

class MockTx:
    def __init__(self, gross, fine, tx_type="ISSUE", wastage=Decimal("0.000"), purity=Decimal("91.60")):
        self.gross_weight = Decimal(str(gross))
        self.fine_weight = Decimal(str(fine))
        self.transaction_type = tx_type
        self.actual_wastage_weight = Decimal(str(wastage))
        self.purity_percent = Decimal(str(purity))

# 1. Purity and Fine Gold Conversions
def test_calculate_fine_gold_22k():
    # 100.000g of 22K (91.60% purity) -> 91.600g pure fine gold
    assert calculate_fine_gold("100.000", "91.60") == Decimal("91.600")

def test_calculate_fine_gold_18k():
    # 50.000g of 18K (75.00% purity) -> 37.500g pure fine gold
    assert calculate_fine_gold("50.000", "75.00") == Decimal("37.500")

def test_calculate_fine_gold_24k():
    # 1000.000g of 24K bullion (99.90% purity) -> 999.000g pure fine gold
    assert calculate_fine_gold("1000.000", "99.90") == Decimal("999.000")

# 2. Rounding Edge Cases (Half Up at sub-milligram boundary)
def test_rounding_edge_cases_half_up():
    # 12.3455g -> rounds up to 12.346g
    assert round_weight(Decimal("12.3455")) == Decimal("12.346")
    # 12.3454g -> rounds down to 12.345g
    assert round_weight(Decimal("12.3454")) == Decimal("12.345")
    # Purity rounding: 91.605% -> 91.61%
    assert round_purity(Decimal("91.605")) == Decimal("91.61")
    assert round_purity(Decimal("91.604")) == Decimal("91.60")

# 3. Net Weight Deductions (Stones, Enamel, Dust)
def test_calculate_net_weight():
    # Gross 50.500g with 2.250g stones and 0.100g dust -> 48.150g net gold
    assert calculate_net_weight("50.500", "2.250", "0.100") == Decimal("48.150")

# 4. Wastage Calculations & Loss Alert Threshold
def test_wastage_normal_within_allowance():
    # Issue 100.000g, Return 95.000g ornament + 3.000g scrap + 0.100g dust = 98.100g
    # Actual wastage = 1.900g. Allowed @ 2.00% = 2.000g. Variance = -0.100g.
    res = calculate_wastage(
        issued_weight="100.000",
        returned_ornament_weight="95.000",
        returned_scrap_weight="3.000",
        returned_dust_weight="0.100",
        allowed_wastage_percent="2.00",
        loss_alert_threshold_grams="0.100"
    )
    assert res.actual_wastage_grams == Decimal("1.900")
    assert res.allowed_wastage_grams == Decimal("2.000")
    assert res.wastage_variance_grams == Decimal("-0.100")
    assert res.is_loss_alert is False

def test_wastage_triggers_loss_alert():
    # Issue 100.000g, Return 94.000g ornament + 3.000g scrap = 97.000g
    # Actual wastage = 3.000g. Allowed @ 2.00% = 2.000g. Variance = +1.000g (> 0.100g -> ALERT)
    res = calculate_wastage(
        issued_weight="100.000",
        returned_ornament_weight="94.000",
        returned_scrap_weight="3.000",
        returned_dust_weight="0.000",
        allowed_wastage_percent="2.00",
        loss_alert_threshold_grams="0.100"
    )
    assert res.actual_wastage_grams == Decimal("3.000")
    assert res.wastage_variance_grams == Decimal("1.000")
    assert res.is_loss_alert is True

# 5. Multi-Step Lifecycle: Jewellery, Scrap, and Filings Receipts
def test_jewellery_scrap_filings_receipts_settlement():
    # Opening balance: 0.000g
    # Job Issue: 100.000g 22K (91.600g fine)
    # Receipt 1 (Finished Ornament): 85.000g gross (77.860g fine) + 1.800g actual wastage reported
    # Receipt 2 (Melting Scrap): 10.000g gross (9.160g fine)
    # Receipt 3 (Polishing Dust): 1.200g gross (1.099g fine)
    # Total accounted = 85.000 + 10.000 + 1.200 + 1.800 = 98.000g
    # Remaining on karigar bench = 100.000 - 98.000 = 2.000g gross
    issued = [MockTx("100.000", "91.600", tx_type="ISSUE")]
    received = [
        MockTx("85.000", "77.860", tx_type="RECEIPT_ORNAMENT", wastage="1.800"),
        MockTx("10.000", "9.160", tx_type="RECEIPT_SCRAP"),
        MockTx("1.200", "1.099", tx_type="RECEIPT_DUST")
    ]

    bal = compute_karigar_balance(Decimal("0.000"), Decimal("0.000"), issued, received)
    assert bal.total_issued_gross == Decimal("100.000")
    assert bal.total_returned_gross == Decimal("96.200") # 85 + 10 + 1.2
    assert bal.total_wastage_settled_gross == Decimal("1.800")
    assert bal.closing_balance_gross == Decimal("2.000")

# 6. Gross Balance vs Fine-Gold Balance Separation
def test_gross_and_fine_balance_separation():
    # Ensure gross and fine gold are never confused.
    # Karigar issued 100g of 18K (75.00% purity -> 75.000g fine gold)
    # Karigar returns 50g of 24K (99.90% purity -> 49.950g fine gold)
    # Closing Gross = 100.000 - 50.000 = 50.000g
    # Closing Fine = 75.000 - 49.950 = 25.050g
    issued = [MockTx("100.000", "75.000", purity="75.00")]
    received = [MockTx("50.000", "49.950", purity="99.90")]

    bal = compute_karigar_balance(Decimal("0.000"), Decimal("0.000"), issued, received)
    assert bal.closing_balance_gross == Decimal("50.000")
    assert bal.closing_balance_fine == Decimal("25.050")
    # Gross and Fine are distinct
    assert bal.closing_balance_gross != bal.closing_balance_fine

# 7. Insufficient Balance Validation
def test_insufficient_balance_validation():
    current_gross = Decimal("10.000")
    # Attempting to return 15g when karigar only has 10g must raise ValueError
    with pytest.raises(ValueError, match="Insufficient karigar balance"):
        validate_transaction_balance(
            current_gross_balance=current_gross,
            transaction_type="RECEIPT_ORNAMENT",
            transaction_gross_weight=Decimal("15.000"),
            allow_negative_override=False
        )
    # Attempting to return 10g or less is valid
    validate_transaction_balance(
        current_gross_balance=current_gross,
        transaction_type="RECEIPT_ORNAMENT",
        transaction_gross_weight=Decimal("10.000")
    )

# 8. Reversal & Adjustment Integrity
def test_transaction_reversal_integrity():
    # If a transaction was entered in error (e.g. Issue 25.000g),
    # an equal and opposite adjustment/receipt offsets it to exactly 0.000g
    opening = Decimal("50.000")
    opening_fine = Decimal("45.800")
    issued = [
        MockTx("25.000", "22.900", tx_type="ISSUE")
    ]
    # Reversal receipt
    received = [
        MockTx("25.000", "22.900", tx_type="RECEIPT_ORNAMENT")
    ]

    bal = compute_karigar_balance(opening, opening_fine, issued, received)
    assert bal.closing_balance_gross == Decimal("50.000")
    assert bal.closing_balance_fine == Decimal("45.800")
