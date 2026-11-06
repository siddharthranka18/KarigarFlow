import pytest
from fastapi.testclient import TestClient
from decimal import Decimal
from app.main import app
from app.core.security import create_access_token

client = TestClient(app)

@pytest.fixture
def finance_token():
    return create_access_token({"sub": "finance@karigarflow.com", "role": "admin", "user_id": 1})

@pytest.fixture
def clerk_token():
    return create_access_token({"sub": "clerk@karigarflow.com", "role": "issue_clerk", "user_id": 2})

@pytest.fixture
def karigar_token():
    return create_access_token({"sub": "karigar1@karigarflow.com", "role": "karigar", "user_id": 4})

# 1. Unauthenticated Protection
def test_unauthenticated_access_denied():
    res = client.get("/api/karigars")
    assert res.status_code == 401
    res = client.get("/api/transactions")
    assert res.status_code == 401
    res = client.get("/api/inventory")
    assert res.status_code == 401
    res = client.get("/api/transactions/daily-summary")
    assert res.status_code == 401

# 2. Karigar Boundary: Cannot access other karigar details (ID tampering)
def test_karigar_cannot_access_other_karigar_profile(karigar_token):
    headers = {"Authorization": f"Bearer {karigar_token}"}
    # Karigar 1 belongs to this user; Karigar 2 belongs to P. Murugesan
    res = client.get("/api/karigars/2", headers=headers)
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]

    # Karigar 1 can access their own profile
    res_own = client.get("/api/karigars/1", headers=headers)
    assert res_own.status_code == 200
    assert res_own.json()["karigar_code"] == "KG-CBE-001"

# 3. Karigar Boundary: Cannot view vault inventory
def test_karigar_cannot_access_vault_inventory(karigar_token):
    headers = {"Authorization": f"Bearer {karigar_token}"}
    res = client.get("/api/inventory", headers=headers)
    assert res.status_code == 403
    assert "Operation not permitted" in res.json()["detail"]

# 4. Karigar Boundary: Cannot view daily stock statement
def test_karigar_cannot_access_daily_stock_summary(karigar_token):
    headers = {"Authorization": f"Bearer {karigar_token}"}
    res = client.get("/api/transactions/daily-summary", headers=headers)
    assert res.status_code == 403
    assert "Operation not permitted" in res.json()["detail"]

# 5. Karigar Boundary: Cannot create gold slips
def test_karigar_cannot_create_transaction_slip(karigar_token):
    headers = {"Authorization": f"Bearer {karigar_token}"}
    payload = {'job_number': 'OPENING', 'item_category': 'general', 'scale_reading_confirmed': True,
        "transaction_type": "ISSUE",
        "karigar_id": 1,
        "item_description": "Attempted self-issue",
        "gross_weight": 10.000,
        "purity_percent": 91.60
    }
    res = client.post("/api/transactions", json=payload, headers=headers)
    assert res.status_code == 403

# 6. Finance Head and Issue Clerk Permitted Access
def test_finance_head_full_access(finance_token):
    headers = {"Authorization": f"Bearer {finance_token}"}
    assert client.get("/api/karigars", headers=headers).status_code == 200
    assert client.get("/api/inventory", headers=headers).status_code == 200
    assert client.get("/api/transactions/daily-summary", headers=headers).status_code == 200

# 7. Duplicate Submission & Idempotency Key Handling
def test_duplicate_submission_idempotent(clerk_token):
    headers = {"Authorization": f"Bearer {clerk_token}"}
    idemp_key = "test-sec-idemp-101"
    payload = {'job_number': 'OPENING', 'item_category': 'general', 'scale_reading_confirmed': True,
        "transaction_type": "ISSUE",
        "karigar_id": 3,
        "item_description": "22K Idempotency Guard Test Lot",
        "gross_weight": 14.250,
        "stone_weight": 0.000,
        "purity_percent": 91.60,
        "allowed_wastage_percent": 2.00,
        "idempotency_key": idemp_key
    }
    # First submission -> 201 Created
    res1 = client.post("/api/transactions", json=payload, headers=headers)
    assert res1.status_code == 201
    slip_number = res1.json()["slip_number"]

    # Retried submission with identical idempotency_key -> returns existing transaction
    res2 = client.post("/api/transactions", json=payload, headers=headers)
    assert res2.status_code in [200, 201]
    assert res2.json()["slip_number"] == slip_number

# 8. Insufficient Balance Check on Receipt
def test_receipt_exceeding_balance_blocked(clerk_token):
    headers = {"Authorization": f"Bearer {clerk_token}"}
    # Karigar 4 has around 30.5g opening balance. Attempting to return 500g must fail
    payload = {'job_number': 'OPENING', 'item_category': 'general', 'scale_reading_confirmed': True,
        "transaction_type": "RECEIPT_ORNAMENT",
        "karigar_id": 4,
        "item_description": "Impossible excessive return",
        "gross_weight": 500.000,
        "purity_percent": 91.60
    }
    res = client.post("/api/transactions", json=payload, headers=headers)
    assert res.status_code == 400
    assert "Insufficient karigar balance" in res.json()["detail"]

