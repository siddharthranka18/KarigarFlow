import pytest
from decimal import Decimal
from app.services.gold_calculations import (
    calculate_fine_gold,
    calculate_net_weight,
    calculate_wastage,
    compute_karigar_balance,
    round_weight
)

def test_calculate_fine_gold_22k():
    # 100.000g of 22K (91.60% purity) should yield exactly 91.600g pure fine gold
    gross = Decimal("100.000")
    purity = Decimal("91.60")
    fine = calculate_fine_gold(gross, purity)
    assert fine == Decimal("91.600")

def test_calculate_fine_gold_precision_half_up():
    # 12.345g of 91.60% -> 12.345 * 91.60 / 100 = 11.30802 -> 11.308g
    gross = Decimal("12.345")
    purity = Decimal("91.60")
    fine = calculate_fine_gold(gross, purity)
    assert fine == Decimal("11.308")

def test_calculate_net_weight():
    # Gross 50.500g with 2.250g stones and 0.100g dust
    gross = Decimal("50.500")
    stones = Decimal("2.250")
    dust = Decimal("0.100")
    net = calculate_net_weight(gross, stones, dust)
    assert net == Decimal("48.150")

def test_wastage_calculation_normal():
    # Issued: 100.000g, Returned: 95.000g ornaments + 3.000g scrap + 0.100g dust = 98.100g
    # Actual wastage = 100.000 - 98.100 = 1.900g
    # Allowed wastage @ 2.00% = 2.000g
    # Variance = 1.900 - 2.000 = -0.100g (within allowance, NO loss alert)
    res = calculate_wastage(
        issued_weight=Decimal("100.000"),
        returned_ornament_weight=Decimal("95.000"),
        returned_scrap_weight=Decimal("3.000"),
        returned_dust_weight=Decimal("0.100"),
        allowed_wastage_percent=Decimal("2.00"),
        loss_alert_threshold_grams=Decimal("0.100")
    )
    assert res.actual_wastage_grams == Decimal("1.900")
    assert res.allowed_wastage_grams == Decimal("2.000")
    assert res.wastage_variance_grams == Decimal("-0.100")
    assert res.is_loss_alert is False

def test_wastage_calculation_loss_alert():
    # Issued: 100.000g, Returned: 94.000g ornaments + 3.000g scrap = 97.000g
    # Actual wastage = 3.000g
    # Allowed wastage @ 2.00% = 2.000g
    # Variance = +1.000g (> 0.100g threshold -> triggers Loss Alert!)
    res = calculate_wastage(
        issued_weight=Decimal("100.000"),
        returned_ornament_weight=Decimal("94.000"),
        returned_scrap_weight=Decimal("3.000"),
        returned_dust_weight=Decimal("0.000"),
        allowed_wastage_percent=Decimal("2.00"),
        loss_alert_threshold_grams=Decimal("0.100")
    )
    assert res.actual_wastage_grams == Decimal("3.000")
    assert res.allowed_wastage_grams == Decimal("2.000")
    assert res.wastage_variance_grams == Decimal("1.000")
    assert res.is_loss_alert is True

class MockTx:
    def __init__(self, gross, fine):
        self.gross_weight = Decimal(str(gross))
        self.fine_weight = Decimal(str(fine))

def test_compute_karigar_balance():
    # Opening balance: 10.000g gross, 9.160g fine
    # Issued: 50.000g gross, 45.800g fine
    # Returned: 40.000g gross, 36.640g fine
    # Closing expected: 20.000g gross, 18.320g fine
    opening_gross = Decimal("10.000")
    opening_fine = Decimal("9.160")
    issued = [MockTx("50.000", "45.800")]
    returned = [MockTx("40.000", "36.640")]

    balance = compute_karigar_balance(opening_gross, opening_fine, issued, returned)
    assert balance.closing_balance_gross == Decimal("20.000")
    assert balance.closing_balance_fine == Decimal("18.320")

