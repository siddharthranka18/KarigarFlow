# Scale photo verification

Install backend requirements and run `python -m alembic upgrade head` in backend.
The scale_readings table retains normalized JPEG evidence and immutable OCR
proposals. RapidOCR 1.4.4 includes local ONNX models; no API key or new environment
variable is required. Images are not sent to external recognition services.

Upload a JPEG/PNG/WebP of at most 5 MB and 12 megapixels in Create New Slip.
For a reproducible demo, upload `database/seed/scale-demo.png` (a synthetic
120.000g, 91.60% display, not a real workshop photograph).
Image content is validated, oriented and resized to at most 1800 pixels per
side; re-encoding strips metadata. The displayed preview matches retained OCR
input. One explicit gram weight is proposed, with one purity percentage if
present. Kilograms, carats and missing decimals are not inferred.

Assumptions: the display is gross weight, not net/stones weight; crop to one
reading. Scores below 0.90, ambiguous values, missing units or invalid ranges
are uncertain and block photo-backed saving. Scores are not calibrated accuracy
probabilities. Missing purity is entered manually. Karat-only printouts require
manual interpretation. Glare, handwriting and seven-segment display accuracy
have not been measured on workshop photos.

The photo appears beside proposed values. Confirmation starts unchecked and
resets when values or evidence change. The server checks uploader ownership,
stored ready status, explicitly supplied true confirmation and decimal equality
of weight and any detected purity. Client-supplied OCR values and arbitrary
photo URLs are not trusted. Errors do not create slips. Users may retake a photo
or explicitly remove it and use manual entry; that records no photo verification
claim. Legacy API manual-entry defaults remain unchanged; universal explicit
manual confirmation is a remaining hardening task.

POST /api/scale-readings allows clerk/Finance; POST /api/transactions accepts
scale_reading_id. Saved slips retain a reference and inspection retrieves the
photo. GET evidence permits its uploader, Finance or the karigar whose saved
slip references it. There are no public image links. No edit/delete evidence
endpoint is provided. Abandoned uploads need future retention cleanup/quotas.
Deployment must also limit multipart bodies at the proxy; production rate
limiting and durable offline photo drafts remain unfinished. OCR execution is
serialized per process to bound local work.

Tests run actual ONNX inference on a synthesized display and deterministic
mocked inference for API confirmation/mismatch/access/error checks. Other tests
cover malformed and oversized uploads, ambiguity and the supplied fine-gold
sample. Synthetic image accuracy is not a substitute for real workshop photo QA.
