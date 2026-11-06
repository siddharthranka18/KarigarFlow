"""Inspect persisted slips and enforce ownership, including linked records."""
import pytest
from app.models.transaction import GoldTransaction


def headers(token):
    return {"Authorization": f"Bearer {token}"}


def receipt(client, token, karigar_id=1):
    response = client.post('/api/transactions', headers=headers(token), json={'job_number': 'OPENING', 'item_category': 'general', 'scale_reading_confirmed': True,
        'transaction_type': 'RECEIPT_ORNAMENT', 'karigar_id': karigar_id,
        'item_description': 'Synthetic inspection sample',
        'gross_weight': '10.000', 'purity_percent': '91.60',
        'allowed_wastage_percent': '2.00', 'actual_wastage_weight': '0.200',
        'notes': 'Reviewer sample note',
    })
    assert response.status_code == 201, response.text
    return response.json()


def test_inspection_includes_settlement_and_parent(client, finance_token):
    tx = receipt(client, finance_token)
    response = client.get(f'/api/transactions/{tx["id"]}', headers=headers(finance_token))
    assert response.status_code == 200
    detail = response.json()
    assert detail['transaction']['notes'] == 'Reviewer sample note'
    assert detail['transaction']['fine_weight'] == '9.160'
    assert detail['recorded_by_name']
    assert detail['parent'] is None
    assert len(detail['linked_entries']) == 1
    child = detail['linked_entries'][0]
    assert child['transaction_type'] == 'WASTAGE_SETTLEMENT'
    assert child['fine_weight'] == '0.183'
    back = client.get(f'/api/transactions/{child["id"]}', headers=headers(finance_token)).json()
    assert back['parent']['id'] == tx['id']


def test_inspection_ownership_and_auth(client, finance_token, karigar_token):
    own = receipt(client, finance_token)
    other = receipt(client, finance_token, karigar_id=2)
    assert client.get(f'/api/transactions/{own["id"]}').status_code == 401
    assert client.get(f'/api/transactions/{own["id"]}', headers=headers(karigar_token)).status_code == 200
    assert client.get(f'/api/transactions/{other["id"]}', headers=headers(karigar_token)).status_code == 404
    assert client.get('/api/transactions/999999', headers=headers(finance_token)).status_code == 404


def test_cross_karigar_links_never_disclosed(client, finance_token, karigar_token, test_db):
    own = receipt(client, finance_token)
    other = receipt(client, finance_token, karigar_id=2)
    foreign = test_db.get(GoldTransaction, other['id'])
    foreign.related_slip_number = own['slip_number']
    test_db.commit()
    for token in (finance_token, karigar_token):
        detail = client.get(f'/api/transactions/{own["id"]}', headers=headers(token)).json()
        assert other['id'] not in [entry['id'] for entry in detail['linked_entries']]
    detail = client.get(f'/api/transactions/{other["id"]}', headers=headers(finance_token)).json()
    assert detail['parent'] is None


@pytest.mark.parametrize('transaction_id', [0, -1, 'invalid'])
def test_invalid_inspection_id(client, finance_token, transaction_id):
    assert client.get(f'/api/transactions/{transaction_id}', headers=headers(finance_token)).status_code == 422


def test_daily_summary_route_still_resolves(client, finance_token):
    assert client.get('/api/transactions/daily-summary', headers=headers(finance_token)).status_code == 200
