# KarigarFlow

Jewellery workshop gold custody for Company A's internship core build.

**Issue → return → agreed wastage → Finance review → daily reconciliation.**

The core runs locally with a React/TypeScript frontend, FastAPI backend and
PostgreSQL. It uses Decimal arithmetic, role-scoped access and real local OCR.
All demo profiles, photos and inventory are synthetic; the supplied reference
transactions are seeded separately and retain their exact fine balances.

## What works

- Category-specific karigar agreements, snapshotted per job.
- Issue/ornament/scrap/filing receipts with job numbers, optional HUID and running
  gross/fine balances. Job and vault overdraw checks run on the server.
- Scale-photo proposals beside retained evidence, explicit confirmation and
  server-side mismatch/uncertainty blocking. No OCR API key is needed.
- Finance-only loss and history-drift review. Approved write-offs are linked,
  auditable ledger events; receipts and wastage settlements save atomically.
- Owner-only daily custody statement, CSV export and print styling.
- Own Tamil/English karigar slips and balances on phone-width layouts.
- Per-user drafts and retry keys survive reloads. The production app shell
  loads offline, but gold entries wait for a deliberate online submission.

## Run and review

Follow [deployment.md](deployment.md) for complete local commands, environment
variable names, all demo logins, test isolation and hosting instructions.

The reviewer accounts are **Clerk**, **Finance**, **Owner / Managing Partner**
and **Karigar**. Finance does not have owner stock access. Karigars cannot view
peer slips. No real client data belongs in this demonstration deployment.

The reference craftsman is **KG-REFERENCE / Murugesan S**. The three sample
slips leave **109.920 → 6.916 → 3.893 g fine**. Outstanding stock is never
automatically labelled loss. Use database/seed/scale-demo.png for a synthetic
120.000g / 91.60% OCR demonstration.

## Design and validation

- [Technical design and labelled assumptions](docs/technical-design.md)
- [Current completion and limits](docs/brief-gap-audit.md)
- [OCR evidence contract](docs/scale-photos.md)
- [Finance review policy](docs/loss-review.md)

Validation includes 67 backend tests, four production-build browser flows,
desktop/phone screenshots and a dependency audit. CI configuration repeats the
checks with isolated PostgreSQL databases. [GitHub CI passed](https://github.com/siddharthranka18/KarigarFlow/actions/runs/42276478796)
for implementation commit 5265aba, including the Docker image build. This does
not establish hosted availability.

## Deployment and limits

Dockerfile and render.yaml describe a same-origin deployment with PostgreSQL.
There is no live URL yet. Free hosting limits, database expiry and local Docker
verification limits are documented in deployment.md.

Provisional assumptions include the allowance calculation basis, 0.100g excess
threshold, drift windows/threshold, full write-off policy and opening baselines.
Client workshop-photo trials, native Tamil acceptance and real production
operations remain necessary. Refinery transfers, period-close snapshots, cash
settlement, optional old-gold desk and Tally-specific export are outside this
core implementation. CSV is not advertised as Tally-compatible output.

Source structure: backend/app contains routes, models, schemas and services;
frontend/src contains role-specific screens and UI components; database/seed
holds synthetic data; migrations, tests and deployment files live alongside.
