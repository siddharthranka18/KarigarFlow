from datetime import datetime
from decimal import Decimal
import pytest

from app.models.transaction import GoldTransaction
from app.models.karigar import Karigar

DAY = '2026-10-05'


def auth(token):
    return {'Authorization': f'Bearer {token}'}


def record(db, slip, kind, gross, fine, when):
    db.add(GoldTransaction(
        slip_number=slip, transaction_type=kind, karigar_id=1,
        created_by_user_id=1, item_description='Synthetic stock statement test',
        gross_weight=Decimal(gross), stone_weight=0, net_weight=Decimal(gross),
        purity_percent=Decimal('91.60'), fine_weight=Decimal(fine),
        created_at=datetime.fromisoformat(when),
    ))
    db.commit()


def row(data, location, unit='fine'):
    return next(r for r in data['rows'] if r['location'] == location and r['unit'] == unit)


def test_opening_movements_and_closing_reconcile(client, finance_token, test_db):
    record(test_db, 'PRIOR-ISS', 'ISSUE', '100.000', '91.600', '2026-10-04T10:00:00')
    record(test_db, 'DAY-REC', 'RECEIPT_ORNAMENT', '95.000', '87.020', '2026-10-05T08:00:00')
    record(test_db, 'DAY-WST', 'WASTAGE_SETTLEMENT', '1.900', '1.740', '2026-10-05T08:00:00')
    record(test_db, 'DAY-SCP', 'RECEIPT_SCRAP', '3.100', '2.840', '2026-10-05T09:00:00')
    record(test_db, 'LATER', 'PURCHASE', '10.000', '9.160', '2026-10-06T08:00:00')
    response = client.get(f'/api/stock-statement?statement_date={DAY}', headers=auth(finance_token))
    assert response.status_code == 200
    data = response.json()
    assert data['timezone'] == 'Asia/Kolkata'
    assert data['transaction_count'] == 3
    assert row(data, 'Central vault')['opening'] == '1319.600'
    assert row(data, 'Central vault')['closing'] == '1409.460'
    assert row(data, 'Karigar custody')['closing'] == '245.351'
    company = row(data, 'Company total')
    assert company['opening'] == '1770.229'
    assert company['closing'] == '1768.489'
    assert company['receipts'] == '0.000'
    assert company['wastage'] == '-1.740'
    for r in data['rows']:
        assert Decimal(r['closing']) == sum((Decimal(r[k]) for k in (
            'opening', 'issues', 'receipts', 'purchases', 'wastage', 'loss_adjustments')), Decimal(0))


def test_india_midnight_boundaries(client, finance_token, test_db):
    record(test_db, 'BEFORE', 'PURCHASE', '1.000', '0.916', '2026-10-04T18:29:59')
    record(test_db, 'START', 'PURCHASE', '2.000', '1.832', '2026-10-04T18:30:00')
    record(test_db, 'LAST', 'PURCHASE', '3.000', '2.748', '2026-10-05T18:29:59')
    record(test_db, 'AFTER', 'PURCHASE', '4.000', '3.664', '2026-10-05T18:30:00')
    data = client.get(f'/api/stock-statement?statement_date={DAY}', headers=auth(finance_token)).json()
    vault = row(data, 'Central vault')
    assert data['transaction_count'] == 2
    assert vault['opening'] == '1412.116'
    assert vault['purchases'] == '4.580'
    assert vault['closing'] == '1416.696'


def test_no_movements_and_inactive_custody(client, finance_token, test_db):
    test_db.get(Karigar, 1).is_active = False
    test_db.commit()
    data = client.get(f'/api/stock-statement?statement_date={DAY}', headers=auth(finance_token)).json()
    assert data['transaction_count'] == 0
    assert row(data, 'Karigar custody')['closing'] == '245.351'
    for r in data['rows']:
        assert r['opening'] == r['closing']


def test_statement_access(client, finance_token, clerk_token, karigar_token):
    url = f'/api/stock-statement?statement_date={DAY}'
    assert client.get(url).status_code == 401
    assert client.get(url, headers=auth(karigar_token)).status_code == 403
    assert client.get(url, headers=auth(clerk_token)).status_code == 403
    assert client.get('/api/stock-statement', headers=auth(finance_token)).status_code == 200


@pytest.mark.parametrize('date', ['invalid', '2026-02-30', '9999-01-01'])
def test_invalid_or_future_date(client, finance_token, date):
    result = client.get(f'/api/stock-statement?statement_date={date}', headers=auth(finance_token))
    assert result.status_code == (400 if date == '9999-01-01' else 422)
