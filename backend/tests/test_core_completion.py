from decimal import Decimal
from app.models.user import User
from app.models.karigar import Karigar
from app.models.transaction import GoldTransaction
from app.core.security import create_access_token
from database.seed.reference_demo import seed_reference_demo


def auth(token):
    return {'Authorization': f'Bearer {token}'}


def slip(**updates):
    return dict(transaction_type='ISSUE', karigar_id=1, item_description='Synthetic job test',
        job_number='JOB-ONE', item_category='necklace', gross_weight='20.000',
        purity_percent='91.60', scale_reading_confirmed=True, **updates)


def test_owner_stock_finance_reviews_and_clerk_scope(client, finance_token, clerk_token, test_db):
    finance = test_db.get(User, 1)
    owner = User(email='owner@test.example', full_name='Synthetic Owner', role='owner', hashed_password=finance.hashed_password, is_active=True)
    test_db.add(owner)
    finance.role = 'finance_head'
    test_db.commit()
    owner_token = create_access_token({'sub': owner.email})
    for url in ('/api/inventory', '/api/transactions/daily-summary', '/api/stock-statement'):
        assert client.get(url, headers=auth(finance_token)).status_code == 403
        assert client.get(url, headers=auth(clerk_token)).status_code == 403
        assert client.get(url, headers=auth(owner_token)).status_code == 200
    for url in ('/api/loss-alerts', '/api/loss-alerts/drift', '/api/loss-alerts/summary', '/api/transactions?loss_alerts_only=true'):
        assert client.get(url, headers=auth(clerk_token)).status_code == 403
        assert client.get(url, headers=auth(finance_token)).status_code == 200
        assert client.get(url, headers=auth(owner_token)).status_code == 200


def test_agreement_snapshot_and_job_bounds(client, finance_token, clerk_token, test_db):
    agreement = {'wastage_by_category': {'general': '2.00', 'necklace': '3.00'}}
    assert client.put('/api/karigars/1/agreements', headers=auth(clerk_token), json=agreement).status_code == 403
    assert client.put('/api/karigars/1/agreements', headers=auth(finance_token), json=agreement).status_code == 200
    issued = client.post('/api/transactions', headers=auth(clerk_token), json=slip())
    assert issued.status_code == 201, issued.text
    assert issued.json()['allowed_wastage_percent'] == '3.00'
    assert client.put('/api/karigars/1/agreements', headers=auth(finance_token), json={'wastage_by_category': {'necklace': '2.00'}}).status_code == 200
    receipt = {**slip(), 'transaction_type': 'RECEIPT_ORNAMENT', 'gross_weight': '10.000', 'actual_wastage_weight': '0.300', 'allowed_wastage_percent': '3.00', 'huid': 'AB1234'}
    saved = client.post('/api/transactions', headers=auth(clerk_token), json=receipt)
    assert saved.status_code == 201, saved.text
    assert saved.json()['allowed_wastage_percent'] == '3.00'
    assert saved.json()['related_slip_number'] == issued.json()['slip_number']
    assert saved.json()['huid'] == 'AB1234'
    assert client.post('/api/transactions', headers=auth(clerk_token), json={**receipt, 'gross_weight': '15.000'}).status_code == 400
    assert client.post('/api/transactions', headers=auth(clerk_token), json={**receipt, 'allowed_wastage_percent': '9.00'}).status_code == 400
    assert client.post('/api/transactions', headers=auth(clerk_token), json={**receipt, 'job_number': 'UNKNOWN-JOB'}).status_code == 400


def test_job_and_confirmation_required_and_vault_guard(client, clerk_token):
    base = {**slip(), 'job_number': 'OPENING', 'item_category': 'general'}
    for missing in ('job_number', 'item_category'):
        payload = {k: v for k, v in base.items() if k != missing}
        assert client.post('/api/transactions', headers=auth(clerk_token), json=payload).status_code == 422
    for value in (False, None):
        payload = {**base, 'scale_reading_confirmed': value} if value is not None else {k:v for k,v in base.items() if k != 'scale_reading_confirmed'}
        assert client.post('/api/transactions', headers=auth(clerk_token), json=payload).status_code == 400
    assert client.post('/api/transactions', headers=auth(clerk_token), json={**base, 'gross_weight': '5000.000'}).status_code == 400


def test_submission_key_cannot_hide_a_changed_or_other_users_slip(client, clerk_token, finance_token):
    payload = {**slip(), 'item_category': 'general', 'idempotency_key': 'strict-retry'}
    result = client.post('/api/transactions', headers=auth(clerk_token), json=payload)
    assert result.status_code == 201
    assert client.post('/api/transactions', headers=auth(clerk_token), json=payload).json()['id'] == result.json()['id']
    assert client.post('/api/transactions', headers=auth(clerk_token), json={**payload, 'gross_weight': '21.000'}).status_code == 409
    assert client.post('/api/transactions', headers=auth(finance_token), json=payload).status_code == 409


def test_reference_demo_is_additive_repeatable_and_drift_is_private(client, finance_token, clerk_token, test_db):
    seed_reference_demo(test_db)
    count = test_db.query(GoldTransaction).count()
    seed_reference_demo(test_db)
    assert test_db.query(GoldTransaction).count() == count
    reference = test_db.query(Karigar).filter_by(karigar_code='KG-REFERENCE').one()
    data = client.get(f'/api/karigars/{reference.id}', headers=auth(finance_token)).json()
    assert Decimal(data['current_balance_fine']) == Decimal('3.893')
    drift = client.get('/api/loss-alerts/drift', headers=auth(finance_token)).json()
    assert len(drift) == 1
    assert drift[0]['baseline_percent'] == '1.00'
    assert drift[0]['recent_percent'] == '2.00'
    assert drift[0]['increase_points'] == '1.00'
    assert 'not a finding' in drift[0]['message']
