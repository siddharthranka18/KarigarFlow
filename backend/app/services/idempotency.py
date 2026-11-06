from decimal import Decimal
from fastapi import HTTPException
from app.services.visibility import visible_transaction


def replay_transaction(tx, payload, user):
    fields = ('transaction_type', 'karigar_id', 'item_description', 'job_number', 'item_category', 'huid',
        'gross_weight', 'stone_weight', 'purity_percent', 'scale_reading_confirmed')
    same = tx.created_by_user_id == user.id and all(getattr(tx, field) == getattr(payload, field) for field in fields)
    same = same and (tx.notes or '') == (payload.notes or '')
    same = same and tx.actual_wastage_weight == (payload.actual_wastage_weight or Decimal(0))
    expected_photo = f'/api/scale-readings/{payload.scale_reading_id}' if payload.scale_reading_id else None
    same = same and tx.scale_image_url == expected_photo
    if payload.allowed_wastage_percent not in (None, Decimal(0)):
        same = same and tx.allowed_wastage_percent == payload.allowed_wastage_percent
    if not same:
        raise HTTPException(status_code=409, detail='This submission key already belongs to a different slip. Inspect the saved slip before recording another entry.')
    return visible_transaction(tx, user)
