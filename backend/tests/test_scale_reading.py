from io import BytesIO
from decimal import Decimal
from PIL import Image, ImageDraw, ImageFont
from app.services.scale_ocr import parse_reading, extract_reading
from app.models.scale_reading import ScaleReading


def sample_image():
    image = Image.new('RGB', (1000, 360), 'white')
    draw = ImageDraw.Draw(image)
    # Test fixture is synthesized, not a client's scale photograph.
    try:
        font = ImageFont.truetype('arial.ttf', 80)
    except OSError:
        font = ImageFont.load_default(size=80)
    draw.text((70, 45), '120.000 g', font=font, fill='black')
    draw.text((70, 175), '91.60 %', font=font, fill='black')
    buffer = BytesIO()
    image.save(buffer, format='PNG')
    return buffer.getvalue()


def test_real_local_ocr_reads_synthetic_display():
    result = extract_reading(sample_image())
    assert result['status'] == 'ready', result
    assert result['weight'] == Decimal('120.000')
    assert result['purity'] == Decimal('91.60')


def test_uncertainty_and_unit_handling():
    for lines in [[], [('120.000 g', .6)], [('120.000 kg', .99)],
        [('120.000 g 125.000 g', .99)], [('-120.000 g', .99)], [('1,200.000 g', .99)],
        [('120.000 g 91.60% 75.00%', .99)], [('120.0000 g', .99)], [('91.60%', .99)]]:
        assert parse_reading(lines)['status'] == 'uncertain', lines
    assert parse_reading([('120.000', .99), ('g', .99)])['weight'] == Decimal('120.000')


def test_photo_upload_confirmation_mismatch_and_privacy(client, clerk_token, finance_token, karigar_token, monkeypatch):
    from app.api.routes import scale_readings
    monkeypatch.setattr(scale_readings, 'extract_reading', lambda _: parse_reading([('120.000 g 91.60%', .99)]))
    headers = {'Authorization': f'Bearer {clerk_token}'}
    result = client.post('/api/scale-readings', headers=headers, files={'photo': ('scale.png', sample_image(), 'image/png')})
    assert result.status_code == 200, result.text
    reading = result.json()
    assert reading['weight'] == '120.000'
    assert reading['image_url'].startswith('data:image/jpeg;base64,')
    payload = dict(transaction_type='ISSUE', karigar_id=1, item_description='Synthetic verified issue',
        gross_weight='120.000', purity_percent='91.60', scale_reading_id=reading['id'])
    assert client.post('/api/transactions', headers=headers, json=payload).status_code == 400
    payload['scale_reading_confirmed'] = False
    assert client.post('/api/transactions', headers=headers, json=payload).status_code == 400
    payload['scale_reading_confirmed'] = True
    assert client.post('/api/transactions', headers=headers, json={**payload, 'gross_weight': '121.000'}).status_code == 409
    assert client.post('/api/transactions', headers=headers, json={**payload, 'purity_percent': '75.00'}).status_code == 409
    assert client.post('/api/transactions', headers={'Authorization': f'Bearer {finance_token}'}, json=payload).status_code == 404
    photo_url = f'/api/scale-readings/{reading["id"]}'
    assert client.get(photo_url).status_code == 401
    assert client.get(photo_url, headers={'Authorization': f'Bearer {karigar_token}'}).status_code == 404
    saved = client.post('/api/transactions', headers=headers, json=payload)
    assert saved.status_code == 201, saved.text
    assert saved.json()['fine_weight'] == '109.920'
    assert saved.json()['scale_image_url'] == photo_url
    assert client.get(photo_url, headers={'Authorization': f'Bearer {karigar_token}'}).status_code == 200


def test_bad_upload_and_uncertain_reading_blocked(client, clerk_token, monkeypatch, test_db):
    from app.api.routes import scale_readings
    headers = {'Authorization': f'Bearer {clerk_token}'}
    assert client.post('/api/scale-readings', headers=headers, files={'photo': ('fake.png', b'not an image', 'image/png')}).status_code == 422
    assert client.post('/api/scale-readings', headers=headers, files={'photo': ('large.png', b'x' * (5 * 1024 * 1024 + 1), 'image/png')}).status_code == 413
    monkeypatch.setattr(scale_readings, 'extract_reading', lambda _: parse_reading([]))
    result = client.post('/api/scale-readings', headers=headers, files={'photo': ('blank.png', sample_image(), 'image/png')})
    assert result.json()['status'] == 'uncertain'
    assert client.post('/api/transactions', headers=headers, json=dict(
        transaction_type='ISSUE', karigar_id=1, item_description='Cannot approve uncertain OCR',
        gross_weight='120.000', purity_percent='91.60', scale_reading_confirmed=True,
        scale_reading_id=result.json()['id'])).status_code == 400
    def unavailable(_):
        raise RuntimeError('Simulated engine outage')
    monkeypatch.setattr(scale_readings, 'extract_reading', unavailable)
    before = test_db.query(ScaleReading).count()
    assert client.post('/api/scale-readings', headers=headers, files={'photo': ('scale.png', sample_image(), 'image/png')}).status_code == 503
    assert test_db.query(ScaleReading).count() == before
