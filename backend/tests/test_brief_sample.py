from decimal import Decimal
from app.models.karigar import Karigar


def test_client_sample_balances_are_not_silently_written_off(client, clerk_token, test_db):
    k = test_db.get(Karigar, 2)
    k.wastage_by_category = {'general': '3.00'}
    k.opening_balance_gross = Decimal('0.000')
    k.opening_balance_fine = Decimal('0.000')
    test_db.commit()
    headers = {'Authorization': f'Bearer {clerk_token}'}
    samples = [
        ('TX-30411', 'ISSUE', '120.000', '109.920', '109.920'),
        ('TX-30437', 'RECEIPT_ORNAMENT', '112.450', '103.004', '6.916'),
        ('TX-30438', 'RECEIPT_SCRAP', '3.300', '3.023', '3.893'),
    ]
    for reference, kind, gross, fine, expected_balance in samples:
        result = client.post('/api/transactions', headers=headers, json={'job_number': 'OPENING', 'item_category': 'general',
            'karigar_id': 2, 'transaction_type': kind, 'item_description': reference,
            'gross_weight': gross, 'purity_percent': '91.60', 'allowed_wastage_percent': '3.00',
            'actual_wastage_weight': '0.000', 'scale_reading_confirmed': True,
        })
        assert result.status_code == 201, result.text
        assert result.json()['fine_weight'] == fine
        balance = client.get('/api/karigars/2', headers=headers).json()
        assert balance['current_balance_fine'] == expected_balance
