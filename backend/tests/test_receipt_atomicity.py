"""Receipts and their generated wastage must form a single custody change."""
from decimal import Decimal

import pytest
from sqlalchemy import event

from app.models.transaction import GoldTransaction


def payload(**changes):
    return {
        'transaction_type': 'RECEIPT_ORNAMENT', 'karigar_id': 1,
        'item_description': 'Synthetic receipt atomicity sample',
        'gross_weight': '10.000', 'purity_percent': '91.60',
        'allowed_wastage_percent': '2.00', 'actual_wastage_weight': '0.200',
        'idempotency_key': 'atomic-receipt', **changes,
    }


def test_settlement_failure_rolls_back_receipt_and_allows_retry(client, clerk_token, test_db):
    auth = {'Authorization': f'Bearer {clerk_token}'}
    before = client.get('/api/karigars/1', headers=auth).json()

    def fail_settlement(mapper, connection, target):
        if target.transaction_type == 'WASTAGE_SETTLEMENT':
            raise RuntimeError('Simulated settlement write failure')

    event.listen(GoldTransaction, 'before_insert', fail_settlement)
    try:
        with pytest.raises(RuntimeError, match='Simulated settlement write failure'):
            client.post('/api/transactions', json=payload(), headers=auth)
    finally:
        event.remove(GoldTransaction, 'before_insert', fail_settlement)

    assert test_db.query(GoldTransaction).count() == 0
    after = client.get('/api/karigars/1', headers=auth).json()
    assert after['current_balance_gross'] == before['current_balance_gross']
    assert after['current_balance_fine'] == before['current_balance_fine']

    saved = client.post('/api/transactions', json=payload(), headers=auth)
    assert saved.status_code == 201
    replay = client.post('/api/transactions', json=payload(), headers=auth)
    assert replay.status_code == 201
    assert saved.json()['id'] == replay.json()['id']
    assert test_db.query(GoldTransaction).count() == 2


def test_receipt_plus_wastage_cannot_overdraw_gross_balance(client, clerk_token, test_db):
    auth = {'Authorization': f'Bearer {clerk_token}'}
    # Opening gross is 45.250g: receipt alone fits but its 0.900g wastage does not.
    response = client.post('/api/transactions', headers=auth, json=payload(
        gross_weight='45.000', actual_wastage_weight='0.900'))
    assert response.status_code == 400
    assert test_db.query(GoldTransaction).count() == 0


def test_receipt_cannot_overdraw_fine_balance(client, clerk_token, test_db):
    auth = {'Authorization': f'Bearer {clerk_token}'}
    # Gross fits, but this purity would consume more than 41.449g fine held.
    response = client.post('/api/transactions', headers=auth, json=payload(
        gross_weight='42.000', purity_percent='99.90', actual_wastage_weight='0.000'))
    assert response.status_code == 400
    assert 'fine gold balance' in response.json()['detail']
    assert test_db.query(GoldTransaction).count() == 0


def test_combined_receipt_at_exact_balance_is_accepted(client, clerk_token, test_db):
    from app.models.karigar import Karigar
    karigar = test_db.get(Karigar, 1)
    karigar.opening_balance_gross = Decimal('10.200')
    karigar.opening_balance_fine = Decimal('9.343')
    test_db.commit()
    auth = {'Authorization': f'Bearer {clerk_token}'}
    response = client.post('/api/transactions', headers=auth, json=payload())
    assert response.status_code == 201
    balance = client.get('/api/karigars/1', headers=auth).json()
    assert Decimal(balance['current_balance_gross']) == 0
    assert Decimal(balance['current_balance_fine']) == 0


def test_competing_receipts_cannot_spend_the_same_balance(client, clerk_token, test_db):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    ready = Barrier(2)
    auth = {'Authorization': f'Bearer {clerk_token}'}

    def receive(key):
        ready.wait(timeout=10)
        return client.post('/api/transactions', headers=auth, json=payload(
            gross_weight='30.000', actual_wastage_weight='0.000',
            idempotency_key=key)).status_code

    with ThreadPoolExecutor(max_workers=2) as workers:
        statuses = list(workers.map(receive, ['competing-a', 'competing-b']))
    assert sorted(statuses) == [201, 400]
    assert test_db.query(GoldTransaction).count() == 1
    balance = client.get('/api/karigars/1', headers=auth).json()
    assert Decimal(balance['current_balance_gross']) == Decimal('15.250')
