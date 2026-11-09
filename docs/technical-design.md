GitHub: https://github.com/siddharthranka18/KarigarFlow

Live application: https://karigarflow-demo.onrender.com/

Prepared for the Company A internship core build.

# KarigarFlow technical design

## Scope and outcome

The product tracks gold from vault issue to karigar return, agreed craft loss
and explicit Finance adjustment. Its core is karigar/category agreements,
issue/receipt slips, exact running fine balances, local scale-photo OCR,
loss/drift review and a daily custody statement. Core screens are sign-in,
role-specific overview, karigar master, slip register/entry/inspection, review
desk, daily statement and the Tamil karigar portal. Inventory lots are an
owner-only baseline reference screen.

The project does not replace showroom billing. Old-gold desk, PAN/payment
capture, Tally-specific export, loans, savings schemes and customer apps are
excluded from this core build. Messages and outside systems are represented by
local slips and exports; no external messages or financial payments are sent.

## Architecture and choices

React/TypeScript provides responsive forms, routing and query states. Tailwind
keeps a restrained parchment/brass palette and consistent spacing. Vite builds
static assets. FastAPI/Pydantic validates inputs and enforces access on the
server. SQLAlchemy and PostgreSQL provide transactions, numeric storage, unique
retry keys and custody row locks. Alembic is the schema authority, including in
backend tests. FastAPI can serve the built SPA and /api from one origin, reducing
CORS/deployment complexity. Docker and a Render Blueprint describe hosting.

Python Decimal with ROUND_HALF_UP is the authoritative arithmetic. Numeric
weights use three decimal places; purity uses two. Frontend previews are labelled
as previews and do not determine saved balances. No balance is manually updated
after a transaction: balances are derived from the immutable ledger.

Local RapidOCR/ONNX was chosen to avoid a paid API key and external photo transfer.
Generic OCR plus conservative parsing is narrower than a general vision agent,
but reproducible offline on the server. Human verification remains mandatory.

## Data model

Users hold hashed passwords, role and active status. A karigar optionally links
to one login and holds opening gross/fine balances plus category-to-wastage
agreements. Gold transactions hold slip identity, idempotency key, karigar,
creator, job number/category, optional HUID, measurements, the snapshotted
allowance, reported wastage, variance, photo evidence and parent slip link.
Inventory lots are opening stock grouped into vault/refinery custody. Scale
readings retain normalized image bytes, uploader, OCR text, proposed decimals,
status, score and timestamp. Review history is an explicit linked
LOSS_ADJUSTMENT ledger entry with approver and investigation notes.

Agreements live as a validated JSON map because the core has five named
categories and no category workflow. Job identity is the (karigar, job number)
pair; all receipts must match an issued category. The first issue snapshots the
allowance for that job. A dedicated Job table would be the next step if job
closure, due dates or multi-karigar production routing are added.

## Main flow and numerical rules

1. Finance records category agreements. The clerk issues a measured quantity
   against a job/category. Vault and karigar locks protect available custody.
2. On return, enter gross weight, stones, tested purity and optional HUID.
   net = gross - stones; fine = round(net * purity / 100, 3).
3. Actual wastage is reported, not inferred from every unreturned gram. The
   backend calculates the allowance and creates a separate settlement for the
   allowed portion. Receipt and settlement commit together or both roll back.
4. Both per-job and total karigar gross/fine balances must cover a receipt and
   its settlement. Excess remains a review item. Only Finance/owner may create
   a write-off, with notes and explicit confirmation; original evidence remains.
5. The daily statement reconstructs opening custody from earlier ledger entries,
   applies signed movements for an India calendar day, and shows closing vault,
   refinery, karigar and company stock. Internal transfers cancel company-wide.
   Wastage and approved loss reduce company gold; they never increase the vault.

Reference sample: issue 120.000g at 91.60% gives 109.920g fine. Return 112.450g
gives 103.004g fine, leaving 6.916g. Scrap 3.300g gives 3.023g fine, leaving
3.893g. The remaining balance is outstanding custody, not automatic loss.

## OCR, uncertainty and drift

The authenticated clerk uploads JPEG/PNG/WebP, at most 5 MB and 12 megapixels.
The server validates content, applies orientation, strips metadata and resizes
to 1800 pixels. It persists the same JPEG used for OCR. Parsing accepts one
explicit gram reading and an explicit purity percentage if present. Multiple
values, unsupported units/notation, out-of-range values or score below 0.90
produce uncertainty. No missing decimal or karat conversion is invented.

The photo appears beside the proposal. Confirmation starts unchecked and resets
after edits. Saving checks the evidence's uploader, ready status, explicit human
confirmation, and decimal equality with typed gross weight and detected purity.
An uncertain/mismatched photo requires a retake; an explicit manual-entry fallback
removes the photo-verification claim. Engine failures return a clear retry state
and do not create slips. Photos remain available through scoped inspection.

Drift compares weighted reported-wastage rates for the most recent three ornament
receipts and the previous three in the same category. A rise of at least 0.50
percentage points produces a Finance/owner review. Fewer than six comparable
receipts is insufficient history. It is not a fraud score, accusation, automatic
write-off or proof of loss. The separate synthetic history demonstrates the rule.

## Roles, resilience and security

Owner/managing partner has company stock access. Finance has agreements and
review access but no owner stock totals. Clerk/manager have operational slips
and individual balances, not Finance alerts. Karigars see only their own slips,
photo evidence and balances. The extra owner role implements the brief's
owner-only constraint; admin remains an owner-equivalent compatibility role.
JWT authentication loads the active user's current database role. Logout/login
clear the browser query cache. No public image URLs or edit/delete ledger
endpoints are exposed. Production requires a configured strong signing secret;
database initialization fails rather than switching silently to another ledger.

The built SPA caches only static shell assets, never authenticated API responses.
Draft fields and retry keys persist per user on the current device; photographs
are not placed in local storage. A reload restores the draft but resets human
confirmation. Reconnect and submit deliberately; no offline gold transaction is
automatically posted. Evidence that cannot be reloaded must be reattached or
explicitly removed. This is device recovery, not a multi-device offline ledger.

## UI decisions and validation

The redesigned interface uses a light sidebar, warm neutral surfaces, and brass
for primary actions and active navigation. The serif wordmark gives the workshop
an identity while the interface uses sans-serif type. Tabular numerals align
weights. The sign-in page introduces the workflow through the supplied sample
ledger, and the role home pages surface the next task.

The clerk starts a slip from the Workshop desk or opens the Gold ledger. The
form groups job details before photo evidence and measurements, and keeps its
actions visible while scrolling. Finance sees review counts and the evidence for
rising wastage. The owner can go directly to the stock statement and export or
print it. The Tamil mobile view emphasises the user's own balance and slips,
with an English toggle. Inputs have associated labels, and dialogs support
keyboard dismissal and focus management.

Sign-in returns users to the requested page if their role can access it. A clerk
who signs in from a Loss reviews link lands on the Workshop desk. Restricted
pages and APIs enforce their own access rules.

Validation on 7 November 2026: 70 backend tests and four production-build browser
flows passed. The frontend production build passed. npm audit reported zero known
vulnerabilities after updating affected packages. The repository was verified
PUBLIC. GitHub Checks for commit dbd3734 passed on Linux, including backend/browser
checks, Docker build, container startup, migrations and a health check against an
empty database using a hosted-style connection URL:
https://github.com/siddharthranka18/KarigarFlow/actions/runs/42346037070
On 9 November 2026, the redesigned production build passed four local browser
flows. A separate local browser check verified the clerk and Finance sign-in
redirects. The live Render health endpoint reported a connected database, and
the live clerk account signed in successfully.

Backend regression tests cover rounding, sample fidelity, custody conservation,
atomicity, retries, competing requests, job limits, agreement snapshots, privacy,
drift, input validation and real OCR on a synthetic display. Browser QA exercises
the production build at desktop/phone widths, photo mismatch, review, draft
recovery after offline reload, CSV and print. Screenshots are inspected separately
from compilation. A synthetic OCR test is not a workshop-photo accuracy study.

## Assumptions and limits

- A1: Finance and owner are separate roles. The managing partner is represented
  by owner; stock is not shared with Finance by default.
- A2: The five categories are a small demo taxonomy. Only the reference
  necklace's 3.00% comes from the sample; other seeded agreements are synthetic.
- A3: Allowance uses finished receipt gross weight. Actual wastage is explicitly
  reported. The brief does not define this basis or multi-receipt allocation.
- A4: The first issue snapshots a job's allowance. OPENING identifies unallocated
  opening custody; other receipts require an issued job/category.
- A5: Excess threshold greater than 0.100g, drift threshold 0.50 percentage
  points and the two three-receipt windows are provisional review settings.
- A6: Full excess write-off after investigation is a provisional demo policy.
  Partial settlements, cash recovery, rejection/reopening and job reassignment
  are not implemented. Aggregate custody is not proof of a job's recovery.
- A7: Opening inventory/karigar balances precede all ledger history. Editing
  baselines changes historical statements; no signed period-close snapshot exists.
- A8: Existing location/category text identifies refinery lots. Transfers and
  refinery assay differences are not implemented; baseline refinery custody
  carries forward. Gross includes stones where recorded; fine is the gold basis.
- A9: Stored naive timestamps mean UTC. New writes explicitly use UTC. Legacy
  entries written under another server timezone need audit before reliance.
- A10: OCR score threshold and image limits are conservative demo settings.
  Scale photos are gross grams, not stones/net weight. Purity may require manual
  entry. Real-device glare, seven-segment displays and karat printouts need QA.
- A11: Local drafts assume a managed tablet/browser profile. Storage can be
  cleared or unavailable; cross-device sync and guaranteed offline photo upload
  are not provided. Tamil copy needs a native-speaker acceptance review.
- A12: Users, inventory, trend history and test images are synthetic, apart from
  the supplied reference names/values. No real personal data is included.
- A13: Client ROI figures and targets are assumptions, not measured savings.
- A14: Hosting, upload retention/quotas, proxy body limits, backups,
  distributed throttling and real-client hardening require deployment validation.
  The local Docker daemon was unavailable; Docker build and startup passed in CI.
  Hosted app and database health were checked; real-client acceptance remains.

## What was cut and what comes next

Optional old-gold/billing integration and Tally-specific output were cut to keep
the core reliable. CSV is a stock statement, not a claim of Tally compatibility.
Next: client acceptance of allowance/write-off policies, workshop photo trials,
native Tamil review, period snapshots, explicit refinery transfers, job closure
and production operations. Keep the hosted reviewer demo available and preserve
the public repository and commit history through review.
