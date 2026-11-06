from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
from threading import Barrier

import pytest
from app.models.karigar import Karigar
from app.models.transaction import GoldTransaction

NOTES = {'investigation_notes': 'Bench sweep complete. No recovery found; Finance approves loss.', 'confirm_write_off': True}


def auth(token):
    return {'Authorization': f'Bearer {token}'}


def flagged(client, token):
    result = client.post('/api/transactions', headers=auth(token), json={'job_number': 'OPENING', 'item_category': 'general', 'scale_reading_confirmed': True,
        'transaction_type': 'RECEIPT_ORNAMENT', 'karigar_id': 1,
        'item_description': 'Synthetic excess wastage review',
        'gross_weight': '10.000', 'purity_percent': '91.60',
        'allowed_wastage_percent': '2.00', 'actual_wastage_weight': '1.000',
    })
    assert result.status_code == 201
    return result.json()


def test_finance_review_preserves_history_and_reconciles(client, finance_token, test_db):
    tx = flagged(client, finance_token)
    headers = auth(finance_token)
    before = client.get('/api/transactions/daily-summary', headers=headers).json()
    assert before['loss_alerts_count'] == 1
    assert len(client.get('/api/loss-alerts', headers=headers).json()) == 1
    review = client.post(f'/api/loss-alerts/{tx["id"]}/write-off', headers=headers, json=NOTES)
    assert review.status_code == 200
    adjustment = review.json()
    assert adjustment['gross_weight'] == '0.800'
    assert adjustment['fine_weight'] == '0.733'
    assert adjustment['related_slip_number'] == tx['slip_number']
    assert adjustment['created_by_user_id'] == 1
    assert adjustment['notes'] == NOTES['investigation_notes']
    assert adjustment['scale_reading_confirmed'] is False
    after = client.get('/api/transactions/daily-summary', headers=headers).json()
    assert after['loss_alerts_count'] == 0
    assert after['central_vault_fine'] == before['central_vault_fine']
    assert Decimal(before['total_workshop_gold_fine']) - Decimal(after['total_workshop_gold_fine']) == Decimal('0.733')
    assert client.get('/api/loss-alerts', headers=headers).json() == []
    resolved = client.get('/api/loss-alerts?status=resolved', headers=headers).json()
    assert resolved[0]['resolution']['id'] == adjustment['id']
    assert test_db.get(GoldTransaction, tx['id']).is_loss_alert is True
    assert client.get('/api/karigars/1', headers=headers).json()['loss_alerts_count'] == 0
    assert client.get('/api/transactions?loss_alerts_only=true', headers=headers).json() == []


def test_repeat_review_does_not_change_decision(client, finance_token, test_db):
    tx = flagged(client, finance_token)
    url = f'/api/loss-alerts/{tx["id"]}/write-off'
    first = client.post(url, headers=auth(finance_token), json=NOTES).json()
    second = client.post(url, headers=auth(finance_token), json={**NOTES, 'investigation_notes': 'Different notes must not overwrite the first approval.'}).json()
    assert second == first
    assert test_db.query(GoldTransaction).filter_by(transaction_type='LOSS_ADJUSTMENT').count() == 1


def test_review_permissions(client, finance_token, clerk_token, karigar_token):
    tx = flagged(client, finance_token)
    url = f'/api/loss-alerts/{tx["id"]}/write-off'
    assert client.post(url, json=NOTES).status_code == 401
    for token in (clerk_token, karigar_token):
        assert client.post(url, headers=auth(token), json=NOTES).status_code == 403
    assert client.get('/api/loss-alerts', headers=auth(karigar_token)).status_code == 403
    assert client.get('/api/loss-alerts', headers=auth(clerk_token)).status_code == 403


@pytest.mark.parametrize('changes', [
    {'investigation_notes': '   '}, {'investigation_notes': 'x' * 2001}, {'confirm_write_off': False},
])
def test_review_requires_notes_and_confirmation(client, finance_token, changes):
    tx = flagged(client, finance_token)
    result = client.post(f'/api/loss-alerts/{tx["id"]}/write-off', headers=auth(finance_token), json={**NOTES, **changes})
    assert result.status_code == 422


def test_insufficient_custody_blocks_review(client, finance_token, test_db):
    tx = flagged(client, finance_token)
    k = test_db.get(Karigar, 1)
    k.opening_balance_gross = Decimal('10.200')
    k.opening_balance_fine = Decimal('9.343')
    test_db.commit()
    result = client.post(f'/api/loss-alerts/{tx["id"]}/write-off', headers=auth(finance_token), json=NOTES)
    assert result.status_code == 409
    assert test_db.query(GoldTransaction).filter_by(transaction_type='LOSS_ADJUSTMENT').count() == 0


@pytest.mark.parametrize('kind', ['LOSS_ADJUSTMENT', 'WASTAGE_SETTLEMENT', 'UNKNOWN'])
def test_generic_slip_endpoint_cannot_bypass_approval(client, clerk_token, kind):
    result = client.post('/api/transactions', headers=auth(clerk_token), json={'job_number': 'OPENING', 'item_category': 'general', 'scale_reading_confirmed': True,
        'transaction_type': kind, 'karigar_id': 1, 'item_description': 'Bypass attempt',
        'gross_weight': '1.000', 'purity_percent': '91.60',
    })
    assert result.status_code == 400


def test_competing_approvals_create_one_adjustment(client, finance_token, test_db):
    tx = flagged(client, finance_token)
    ready = Barrier(2)

    def approve(_):
        ready.wait(timeout=10)
        return client.post(f'/api/loss-alerts/{tx["id"]}/write-off', headers=auth(finance_token), json=NOTES)

    with ThreadPoolExecutor(max_workers=2) as workers:
        results = list(workers.map(approve, range(2)))
    assert all(r.status_code == 200 for r in results)
    assert results[0].json()['id'] == results[1].json()['id']
    assert test_db.query(GoldTransaction).filter_by(transaction_type='LOSS_ADJUSTMENT').count() == 1
