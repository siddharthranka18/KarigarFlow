import base64
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_roles
from app.db.session import get_db
from app.models.scale_reading import ScaleReading
from app.models.transaction import GoldTransaction
from app.models.karigar import Karigar
from app.models.user import User
from app.services.scale_ocr import normalize_image, extract_reading

router = APIRouter(prefix='/scale-readings', tags=['Scale verification'])


def response(reading):
    return dict(id=reading.id, status=reading.status,
        weight=f'{reading.weight:.3f}' if reading.weight is not None else None,
        purity=f'{reading.purity:.2f}' if reading.purity is not None else None,
        confidence=float(reading.confidence), raw_text=reading.raw_text,
        image_url='data:image/jpeg;base64,' + base64.b64encode(reading.image).decode('ascii'))


@router.post('')
def read_scale(
    photo: UploadFile = File(...), db: Session = Depends(get_db),
    user: User = Depends(require_roles(['admin', 'finance_head', 'issue_clerk'])),
):
    content = photo.file.read(5 * 1024 * 1024 + 1)
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=413, detail='Photo must be 5 MB or smaller')
    try:
        image = normalize_image(content)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    try:
        extracted = extract_reading(image)
    except Exception:
        raise HTTPException(status_code=503, detail='Scale reader unavailable. Retake or retry; no reading has been confirmed.')
    reading = ScaleReading(id=str(uuid4()), user_id=user.id, image=image, **extracted)
    db.add(reading)
    db.commit()
    return response(reading)


@router.get('/{reading_id}')
def get_reading(reading_id: str, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    reading = db.get(ScaleReading, reading_id)
    if not reading:
        raise HTTPException(status_code=404, detail='Photo not found')
    allowed = user.role in {'admin', 'owner', 'finance_head'} or reading.user_id == user.id
    if user.role == 'karigar':
        allowed = db.query(GoldTransaction).join(Karigar).filter(
            Karigar.user_id == user.id,
            GoldTransaction.scale_image_url == f'/api/scale-readings/{reading.id}',
        ).first() is not None
    if not allowed:
        raise HTTPException(status_code=404, detail='Photo not found')
    return response(reading)
