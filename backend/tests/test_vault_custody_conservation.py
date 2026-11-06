"""
Comprehensive tests for Vault-to-Karigar Gold Custody Transfer and Physical Gold Conservation.

This test module verifies:
1. Vault-to-karigar transfers conserve total physical gold:
   Closing Vault Fine = Opening Vault Fine - Issued Fine + Returned Fine
2. Controlled 100g 22K Issue -> 95g Ornament Return -> 1.9g Wastage Settlement -> 3.1g Scrap Return
   accurately updates custody and decrements company physical gold strictly by approved craft wastage.
3. Daily Stock Summary API response accurately exposes custody reconciliation.
4. Verification that automated tests NEVER mutate karigarflow_db.
"""

import pytest
from decimal import Decimal
from sqlalchemy import create_engine, text
from app.models.transaction import TransactionType, GoldTransaction
from app.models.karigar import Karigar
from app.models.inventory import GoldInventory
from app.services.inventory_service import compute_vault_custody_position
from app.services.gold_calculations import round_weight, ZERO_WEIGHT


def test_controlled_vault_karigar_wastage_lifecycle(client, clerk_token, finance_token, test_db):
    """
    Controlled scenario execution:
    1. Opening state:
       - Vault Central: 1000.000g 24K (999.000g fine) + 450.000g 22K (412.200g fine) = 1411.200g fine
       - Refinery: 128.450g scrap (113.678g fine)
       - Total Vault + Refinery: 1524.878g fine
       - Karigar 1 (Anand Swamy): Opening balance 45.250g gross, 41.449g fine
       - All 4 Karigars Total: 267.850g gross, 245.351g fine
       - Company Physical Gold Total: 1524.878 + 245.351 = 1770.229g fine

    2. Issue 100.000g of 22K (91.60% purity = 91.600g fine) to Karigar 1:
       - Vault fine -> 1411.200 - 91.600 = 1319.600g
       - Karigar 1 fine -> 41.449 + 91.600 = 133.049g
       - Total Company Physical Gold: 1319.600 + 113.678 + (245.351 + 91.600) = 1770.229g (CONSERVED)

    3. Ornament receipt 95.000g 22K (91.60% = 87.020g fine):
       - Vault fine -> 1319.600 + 87.020 = 1406.620g
       - Karigar 1 fine -> 133.049 - 87.020 = 46.029g
       - Total Company Physical Gold: 1406.620 + 113.678 + (336.951 - 87.020) = 1770.229g (CONSERVED)

    4. Wastage settlement 1.900g 22K (91.60% = 1.740g fine):
       - Karigar 1 fine -> 46.029 - 1.740 = 44.289g
       - Vault fine -> 1406.620g (remains in vault, craft loss is consumed)
       - Total Company Physical Gold: 1406.620 + 113.678 + 247.931 = 1768.489g
       - Exactly equals Opening Company Fine (1770.229) - Settled Wastage Fine (1.740g)

    5. Scrap receipt 3.100g 22K (91.60% = 2.840g fine):
       - Vault fine -> 1406.620 + 2.840 = 1409.460g
       - Karigar 1 fine -> 44.289 - 2.840 = 41.449g (returned exactly to opening balance!)
       - Total Company Physical Gold: 1409.460 + 113.678 + 245.351 = 1768.489g (CONSERVED)
    """
    headers = {"Authorization": f"Bearer {clerk_token}"}
    admin_headers = {"Authorization": f"Bearer {finance_token}"}

    # Step 1: Verify Opening Baseline
    pos_open = compute_vault_custody_position(test_db)
    assert pos_open.opening_central_vault_fine == Decimal("1411.200")
    assert pos_open.opening_refinery_fine == Decimal("113.678")
    assert pos_open.closing_central_vault_fine == Decimal("1411.200")

    k1_init = client.get("/api/karigars/1", headers=headers).json()
    assert Decimal(str(k1_init["current_balance_gross"])) == Decimal("45.250")
    assert Decimal(str(k1_init["current_balance_fine"])) == Decimal("41.449")

    # Step 2: Issue 100.000g 22K to Karigar 1
    issue_payload = {
        "karigar_id": 1,
        "transaction_type": "ISSUE",
        "gross_weight": "100.000",
        "purity_percent": "91.60",
        "item_description": "22K gold grains issued for audit test",
        "idempotency_key": "IDEMP-AUDIT-ISSUE-100G"
    }
    res = client.post("/api/transactions", json=issue_payload, headers=headers)
    assert res.status_code == 201, res.text

    # Verify after Issue
    pos_after_issue = compute_vault_custody_position(test_db)
    assert pos_after_issue.closing_central_vault_fine == Decimal("1319.600")
    assert pos_after_issue.total_issued_fine == Decimal("91.600")

    k1_after_issue = client.get("/api/karigars/1", headers=headers).json()
    assert Decimal(str(k1_after_issue["current_balance_gross"])) == Decimal("145.250")
    assert Decimal(str(k1_after_issue["current_balance_fine"])) == Decimal("133.049")

    # Steps 3–4 save the ornament receipt and generated settlement atomically.
    rcpt_ornament_payload = {
        "karigar_id": 1,
        "transaction_type": "RECEIPT_ORNAMENT",
        "gross_weight": "95.000",
        "purity_percent": "91.60",
        "item_description": "Finished necklace received",
        "allowed_wastage_percent": "2.00",
        "actual_wastage_weight": "1.900",
        "idempotency_key": "IDEMP-AUDIT-RCPT-ORNAMENT-95G"
    }
    res = client.post("/api/transactions", json=rcpt_ornament_payload, headers=headers)
    assert res.status_code == 201, res.text

    # Verify after Ornament Receipt
    pos_after_ornament = compute_vault_custody_position(test_db)
    assert pos_after_ornament.closing_central_vault_fine == Decimal("1406.620")

    # Settlement comes from the receipt, never an arbitrary manual deduction.
    settlements = test_db.query(GoldTransaction).filter(
        GoldTransaction.transaction_type == 'WASTAGE_SETTLEMENT',
        GoldTransaction.related_slip_number == res.json()['slip_number'],
    ).all()
    assert len(settlements) == 1
    assert settlements[0].gross_weight == Decimal('1.900')
    assert settlements[0].fine_weight == Decimal('1.740')
    manual = client.post('/api/transactions', headers=admin_headers, json={
        'transaction_type': 'WASTAGE_SETTLEMENT', 'karigar_id': 1,
        'gross_weight': '1.900', 'purity_percent': '91.60',
        'item_description': 'Manual deduction must be rejected',
    })
    assert manual.status_code == 400

    # Verify after Wastage Settlement
    pos_after_wastage = compute_vault_custody_position(test_db)
    # Vault does NOT gain gold from wastage consumption
    assert pos_after_wastage.closing_central_vault_fine == Decimal("1406.620")

    k1_after_wastage = client.get("/api/karigars/1", headers=headers).json()
    assert Decimal(str(k1_after_wastage["current_balance_gross"])) == Decimal("48.350")
    assert Decimal(str(k1_after_wastage["current_balance_fine"])) == Decimal("44.289")

    # Step 5: Receipt 3.100g scrap
    rcpt_scrap_payload = {
        "karigar_id": 1,
        "transaction_type": "RECEIPT_SCRAP",
        "gross_weight": "3.100",
        "purity_percent": "91.60",
        "item_description": "Remaining melt scrap returned to vault",
        "idempotency_key": "IDEMP-AUDIT-RCPT-SCRAP-3.1G"
    }
    res = client.post("/api/transactions", json=rcpt_scrap_payload, headers=headers)
    assert res.status_code == 201, res.text

    # Verify final custody and conservation
    pos_final = compute_vault_custody_position(test_db)
    assert pos_final.closing_central_vault_fine == Decimal("1409.460")

    k1_final = client.get("/api/karigars/1", headers=headers).json()
    # Karigar balance has returned exactly to original opening balance
    assert Decimal(str(k1_final["current_balance_gross"])) == Decimal("45.250")
    assert Decimal(str(k1_final["current_balance_fine"])) == Decimal("41.449")

    # Verify company physical gold conservation:
    # Opening Vault + Refinery: 1524.878g
    # Opening Karigars: 245.351g
    # Total Opening Company Fine: 1770.229g
    # Total Closing Company Fine: 1409.460 (Vault) + 113.678 (Refinery) + 245.351 (Karigars) = 1768.489g
    # Total Settled Wastage: 1.740g fine
    # 1770.229g - 1.740g = 1768.489g (EXACT ZERO-DRIFT CONSERVATION)
    all_karigars = client.get("/api/karigars", headers=headers).json()
    total_karigar_fine = sum(Decimal(str(k["current_balance_fine"])) for k in all_karigars)
    total_closing_fine = pos_final.closing_central_vault_fine + pos_final.closing_refinery_fine + total_karigar_fine
    assert total_closing_fine == Decimal("1768.489")


def test_daily_stock_summary_api_reconciliation(client, clerk_token, finance_token):
    """
    Tests that the GET /api/transactions/daily-summary endpoint returns
    reconciled vault custody, karigar custody, and physical company totals.
    """
    headers = {"Authorization": f"Bearer {clerk_token}"}

    res = client.get("/api/transactions/daily-summary", headers=headers)
    assert res.status_code == 200
    data = res.json()

    # Initial test baseline
    assert Decimal(str(data["central_vault_fine"])) == Decimal("1411.200")
    assert Decimal(str(data["refiner_stock_fine"])) == Decimal("113.678")
    assert Decimal(str(data["vault_raw_gold_fine"])) == Decimal("1524.878")
    assert Decimal(str(data["karigar_outstanding_fine"])) == Decimal("245.351")
    assert Decimal(str(data["cumulative_wastage_settled_fine"])) == Decimal("0.000")

    # Total physical company fine equals vault + refinery + karigar
    total_physical = Decimal(str(data["vault_raw_gold_fine"])) + Decimal(str(data["karigar_outstanding_fine"]))
    assert total_physical == Decimal("1770.229")
    assert Decimal(str(data["total_workshop_gold_fine"])) == Decimal("1770.229")

    # Now execute a 50.000g issue
    res_issue = client.post("/api/transactions", json={
        "karigar_id": 2,
        "transaction_type": "ISSUE",
        "gross_weight": "50.000",
        "purity_percent": "91.60",
        "item_description": "50g gold issued",
        "idempotency_key": "IDEMP-AUDIT-API-01"
    }, headers=headers)
    assert res_issue.status_code == 201

    res2 = client.get("/api/transactions/daily-summary", headers=headers)
    assert res2.status_code == 200
    data2 = res2.json()

    # Central Vault fine must have decreased by 45.800g (50 * 0.916)
    assert Decimal(str(data2["central_vault_fine"])) == Decimal("1365.400")
    # Vault total fine (central + refiner) must have decreased by 45.800g (1524.878 - 45.800 = 1479.078)
    assert Decimal(str(data2["vault_raw_gold_fine"])) == Decimal("1479.078")
    # Karigar fine must have increased by 45.800g
    assert Decimal(str(data2["karigar_outstanding_fine"])) == Decimal("291.151")
    # Total workshop fine must remain exactly 1770.229g
    assert Decimal(str(data2["total_workshop_gold_fine"])) == Decimal("1770.229")


def test_dev_database_isolation_safety():
    """
    Directly connects to both karigarflow_db and karigarflow_test_db to verify:
    1. karigarflow_db row count does NOT change when operations occur on karigarflow_test_db.
    2. Test engine is strictly isolated.
    """
    DEV_URL = "postgresql+psycopg2://postgres@localhost:5433/karigarflow_db"
    TEST_URL = "postgresql+psycopg2://postgres@localhost:5433/karigarflow_test_db"

    dev_engine = create_engine(DEV_URL)
    test_engine = create_engine(TEST_URL)

    with dev_engine.connect() as dev_conn:
        initial_dev_tx_count = dev_conn.execute(text("SELECT count(*) FROM gold_transactions;")).scalar()

    # Perform an insert on test_db
    with test_engine.connect() as test_conn:
        test_conn.execute(text("""
            INSERT INTO gold_transactions (
                slip_number, idempotency_key, karigar_id, created_by_user_id, transaction_type,
                item_description, gross_weight, stone_weight, net_weight, purity_percent, fine_weight,
                allowed_wastage_percent, actual_wastage_weight, wastage_variance_weight, is_loss_alert,
                scale_reading_confirmed, created_at
            ) VALUES (
                'SLIP-ISOLATION-01', 'IDEMP-ISOLATION-PROBE-01', 1, 1, 'ISSUE',
                'Isolation probe item', 10.000, 0.000, 10.000, 91.60, 9.160,
                0.00, 0.000, 0.000, false, true, NOW()
            );
        """))
        test_conn.commit()

    # Verify dev_db row count is strictly unchanged
    with dev_engine.connect() as dev_conn:
        final_dev_tx_count = dev_conn.execute(text("SELECT count(*) FROM gold_transactions;")).scalar()

    assert final_dev_tx_count == initial_dev_tx_count, (
        f"CRITICAL VIOLATION: karigarflow_db mutated! Initial={initial_dev_tx_count}, Final={final_dev_tx_count}"
    )
