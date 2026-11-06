"""Local OCR proposals only. Accounting never trusts client-supplied OCR values."""
from decimal import Decimal
from functools import lru_cache
from io import BytesIO
import re
from threading import Lock

from PIL import Image, ImageOps, UnidentifiedImageError

OCR_LOCK = Lock()
Image.MAX_IMAGE_PIXELS = 12_000_000


def normalize_image(content: bytes) -> bytes:
    try:
        with Image.open(BytesIO(content)) as source:
            if source.format not in {'JPEG', 'PNG', 'WEBP'}:
                raise ValueError('Use a JPEG, PNG or WebP image')
            if source.width * source.height > 12_000_000:
                raise ValueError('Image exceeds 12 megapixels')
            image = ImageOps.exif_transpose(source).convert('RGB')
            image.thumbnail((1800, 1800))
            output = BytesIO()
            image.save(output, format='JPEG', quality=90)
            return output.getvalue()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError('Image is invalid or too large') from exc


@lru_cache(maxsize=1)
def engine():
    from rapidocr_onnxruntime import RapidOCR
    return RapidOCR(intra_op_num_threads=2, inter_op_num_threads=1)


def extract_reading(image: bytes) -> dict:
    with OCR_LOCK:
        result, _ = engine()(image)
    return parse_reading([(str(line[1]), float(line[2])) for line in (result or [])])


def parse_reading(lines: list[tuple[str, float]]) -> dict:
    text = '\n'.join(line[0] for line in lines)[:4000]
    confidence = min((line[1] for line in lines), default=0.0)
    # Require an explicit gram unit; never infer kg, carats or a missing decimal.
    weights = {Decimal(value) for value in re.findall(
        r'(?<![\w.])([-+]?\d+(?:\.\d{1,3})?)\s*(?:g|grams?)\b', text, re.I)}
    purities = {Decimal(value) for value in re.findall(
        r'(?<![\w.])([-+]?\d+(?:\.\d{1,2})?)\s*%', text)}
    weight = next(iter(weights)) if len(weights) == 1 else None
    purity = next(iter(purities)) if len(purities) == 1 else None
    valid = weight is not None and 0 < weight < Decimal('10000000') and not re.search(r'\d,\d', text)
    valid = valid and len(purities) <= 1 and (purity is None or 0 < purity <= 100)
    ready = valid and confidence >= 0.90
    return dict(status='ready' if ready else 'uncertain',
        weight=weight.quantize(Decimal('0.001')) if ready else None,
        purity=purity.quantize(Decimal('0.01')) if ready and purity is not None else None,
        confidence=round(max(0.0, min(confidence, 1.0)), 4), raw_text=text)
