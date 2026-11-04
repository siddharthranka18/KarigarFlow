import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
import uuid

from app.main import app
from app.core.security import create_access_token

client = TestClient(app)

@pytest.fixture
def clerk_token():
    return create_access_token({"sub": "clerk@karigarflow.com", "role": "issue_clerk", "user_id": 2})

@pytest.fixture
def finance_token():
    return create_access_token({"sub": "finance@karigarflow.com", "role": "admin", "user_id": 1})

# 1. Complete Workflow: Issue -> Jewellery Receipt -> Auditable Wastage Settlement -> Scrap Reconciliation
def test_complete_issue_receipt_wastage_settlement_workflow(clerk_token):
    headers = {"Authorization": f"Bearer {clerk_token}"}
    
    # Step 0: Record Karigar 2's starting baseline balance
    k_init_res = client.get("/api/karigars/2", headers=headers)
    assert k_init_res.status_code == 200
    init_gross = Decimal(str(k_init_res.json()["current_balance_gross"]))
    init_fine = Decimal(str(k_init_res.json()["current_balance_fine"]))

    # Step 1: Issue 100.000g of 22K (91.60% = 91.600g fine) to Karigar 2 (Murugesan)
    issue_payload = {
        "transaction_type": "ISSUE",
        "karigar_id": 2,
        "item_description": "22K Traditional Coimbatore Kada Batch #401",
        "gross_weight": 100.000,
        "stone_weight": 0.000,
        "purity_percent": 91.60,
        "allowed_wastage_percent": 2.00,
        "idempotency_key": f"test-issue-{uuid.uuid4()}"
    }
    issue_res = client.post("/api/transactions", json=issue_payload, headers=headers)
    assert issue_res.status_code == 201
    issue_slip = issue_res.json()["slip_number"]
    assert issue_res.json()["fine_weight"] == "91.600"

    # Step 2: Receive finished jewellery with reported legitimate craft wastage
    # Finished ornament: 95.000g (fine gold = 95 * 0.916 = 87.020g)
    # Allowed wastage @ 2.00% on 95g = 1.900g
    # Actual wastage reported = 1.900g (legitimate, <= 2.000g)
    receipt_payload = {
        "transaction_type": "RECEIPT_ORNAMENT",
        "karigar_id": 2,
        "item_description": "Finished 22K Solid Kadas - Settling Batch #401",
        "gross_weight": 95.000,
        "stone_weight": 0.000,
        "purity_percent": 91.60,
        "allowed_wastage_percent": 2.00,
        "actual_wastage_weight": 1.900,
        "related_slip_number": issue_slip,
        "idempotency_key": f"test-receipt-{uuid.uuid4()}"
    }
    rec_res = client.post("/api/transactions", json=receipt_payload, headers=headers)
    assert rec_res.status_code == 201
    rec_slip = rec_res.json()["slip_number"]
    assert rec_res.json()["is_loss_alert"] is False

    # Step 3: Verify that an explicit WASTAGE_SETTLEMENT transaction was generated in history
    txs_res = client.get("/api/transactions?karigar_id=2", headers=headers)
    assert txs_res.status_code == 200
    all_txs = txs_res.json()
    
    # Locate the linked wastage settlement slip
    wst_slip = next(
        (t for t in all_txs if t["transaction_type"] == "WASTAGE_SETTLEMENT" and t["related_slip_number"] == rec_slip),
        None
    )
    assert wst_slip is not None
    assert Decimal(str(wst_slip["gross_weight"])) == Decimal("1.900")
    # Fine weight of wastage: 1.900 * 91.60 / 100 = 1.740g
    assert Decimal(str(wst_slip["fine_weight"])) == Decimal("1.740")
    assert wst_slip["is_loss_alert"] is False

    # Step 4: Strict Balance Audit: Verify the remaining 3.100g gross / 2.840g fine
    # Math:
    # Issued: 100.000g gross (91.600g fine)
    # Ornament Returned: 95.000g gross (87.020g fine)
    # Wastage Settled: 1.900g gross (1.740g fine)
    # Accounted so far: 96.900g gross (88.760g fine)
    # Remaining Outstanding on artisan bench = 100.000 - 96.900 = 3.100g gross (2.840g fine)
    k_mid_res = client.get("/api/karigars/2", headers=headers)
    assert k_mid_res.status_code == 200
    mid_gross = Decimal(str(k_mid_res.json()["current_balance_gross"]))
    mid_fine = Decimal(str(k_mid_res.json()["current_balance_fine"]))

    assert mid_gross == init_gross + Decimal("3.100")
    assert mid_fine == init_fine + Decimal("2.840")

    # Step 5: Complete the Physical Reconciliation: Return remaining 3.100g as scrap cuttings
    scrap_payload = {
        "transaction_type": "RECEIPT_SCRAP",
        "karigar_id": 2,
        "item_description": "22K Scrap Cuttings & Wire Ends - Batch #401 Closure",
        "gross_weight": 3.100,
        "stone_weight": 0.000,
        "purity_percent": 91.60,
        "related_slip_number": issue_slip,
        "idempotency_key": f"test-scrap-{uuid.uuid4()}"
    }
    scrap_res = client.post("/api/transactions", json=scrap_payload, headers=headers)
    assert scrap_res.status_code == 201

    # Step 6: Final Verification: The batch is 100% reconciled to 0.000g outstanding
    # Total Accounted: 95.000 (ornament) + 3.100 (scrap) + 1.900 (wastage) = 100.000g!
    k_final_res = client.get("/api/karigars/2", headers=headers)
    assert k_final_res.status_code == 200
    final_gross = Decimal(str(k_final_res.json()["current_balance_gross"]))
    final_fine = Decimal(str(k_final_res.json()["current_balance_fine"]))

    assert final_gross == init_gross
    assert final_fine == init_fine

# 2. Idempotency Key: Retries with same key return original record without duplicate entry
def test_idempotency_retry_returns_same_transaction(clerk_token):
    headers = {"Authorization": f"Bearer {clerk_token}"}
    idemp_key = f"idemp-test-{uuid.uuid4()}"
    
    payload = {
        "transaction_type": "ISSUE",
        "karigar_id": 1,
        "item_description": "22K Idempotent Network Retry Test",
        "gross_weight": 20.000,
        "stone_weight": 0.000,
        "purity_percent": 91.60,
        "allowed_wastage_percent": 2.00,
        "idempotency_key": idemp_key
    }
    
    # First attempt
    res1 = client.post("/api/transactions", json=payload, headers=headers)
    assert res1.status_code == 201
    slip_1 = res1.json()["slip_number"]

    # Retry with identical idempotency_key (simulating client retry or network timeout recovery)
    res2 = client.post("/api/transactions", json=payload, headers=headers)
    assert res2.status_code in [200, 201]
    assert res2.json()["slip_number"] == slip_1
    assert res2.json()["idempotency_key"] == idemp_key

    # Retry using Idempotency-Key HTTP Header
    headers_with_key = {"Authorization": f"Bearer {clerk_token}", "Idempotency-Key": idemp_key}
    payload_without_key = {k: v for k, v in payload.items() if k != "idempotency_key"}
    res3 = client.post("/api/transactions", json=payload_without_key, headers=headers_with_key)
    assert res3.status_code in [200, 201]
    assert res3.json()["slip_number"] == slip_1

# 3. Legitimate Identical Transactions are NOT blocked if idempotency keys differ
def test_legitimate_identical_transactions_accepted_with_different_keys(clerk_token):
    headers = {"Authorization": f"Bearer {clerk_token}"}
    
    # Clerk issues two distinct 10.000g batches back-to-back for two separate job orders
    payload1 = {
        "transaction_type": "ISSUE",
        "karigar_id": 4,
        "item_description": "Batch A: 10g 22K Casting Gold",
        "gross_weight": 10.000,
        "purity_percent": 91.60,
        "idempotency_key": f"batch-a-{uuid.uuid4()}"
    }
    payload2 = {
        "transaction_type": "ISSUE",
        "karigar_id": 4,
        "item_description": "Batch A: 10g 22K Casting Gold",
        "gross_weight": 10.000,
        "purity_percent": 91.60,
        "idempotency_key": f"batch-b-{uuid.uuid4()}"
    }

    res1 = client.post("/api/transactions", json=payload1, headers=headers)
    assert res1.status_code == 201

    res2 = client.post("/api/transactions", json=payload2, headers=headers)
    assert res2.status_code == 201
    assert res1.json()["slip_number"] != res2.json()["slip_number"]

# 4. Excess Wastage Loss Alert Workflow
def test_excess_wastage_loss_alert_and_outstanding_liability(clerk_token):
    headers = {"Authorization": f"Bearer {clerk_token}"}
    
    # Issue 50.000g 22K to Karigar 3
    issue_payload = {
        "transaction_type": "ISSUE",
        "karigar_id": 3,
        "item_description": "22K Filigree Choker Special Order",
        "gross_weight": 50.000,
        "purity_percent": 91.60,
        "allowed_wastage_percent": 2.00,
        "idempotency_key": f"excess-issue-{uuid.uuid4()}"
    }
    issue_res = client.post("/api/transactions", json=issue_payload, headers=headers)
    assert issue_res.status_code == 201

    # Receipt with excessive craft loss:
    # Returned ornament: 46.000g
    # Allowed wastage @ 2.00% = 1.000g
    # Actual reported wastage = 4.000g
    # Excess wastage = 3.000g (> 0.100g threshold -> triggers Loss Alert!)
    rec_payload = {
        "transaction_type": "RECEIPT_ORNAMENT",
        "karigar_id": 3,
        "item_description": "Filigree Choker Finished - High Burn Loss",
        "gross_weight": 46.000,
        "purity_percent": 91.60,
        "allowed_wastage_percent": 2.00,
        "actual_wastage_weight": 4.000,
        "idempotency_key": f"excess-receipt-{uuid.uuid4()}"
    }
    rec_res = client.post("/api/transactions", json=rec_payload, headers=headers)
    assert rec_res.status_code == 201
    assert rec_res.json()["is_loss_alert"] is True
    # Allowed on 46.000g @ 2% is 0.920g. Actual is 4.000g. Variance = 4.000 - 0.920 = 3.080g (> 0.100g threshold)
    assert Decimal(str(rec_res.json()["wastage_variance_weight"])) == Decimal("3.080")

    # The legitimate allowed portion (0.920g) is settled via linked WASTAGE_SETTLEMENT
    txs_res = client.get("/api/transactions?karigar_id=3", headers=headers)
    all_txs = txs_res.json()
    wst_slip = next(
        (t for t in all_txs if t["transaction_type"] == "WASTAGE_SETTLEMENT" and t["related_slip_number"] == rec_res.json()["slip_number"]),
        None
    )
    assert wst_slip is not None
    assert Decimal(str(wst_slip["gross_weight"])) == Decimal("0.920")

# 5. Daily Stock Statement Reconciles Legitimate Wastage
def test_daily_stock_statement_reconciles_wastage(finance_token):
    headers = {"Authorization": f"Bearer {finance_token}"}
    res = client.get("/api/transactions/daily-summary", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "total_legitimate_wastage_today_gross" in data
    assert "total_legitimate_wastage_today_fine" in data
    assert Decimal(str(data["total_legitimate_wastage_today_gross"])) >= Decimal("0.000")
