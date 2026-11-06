# KarigarFlow reviewer deployment guide

Repository: https://github.com/siddharthranka18/KarigarFlow

Live app: not deployed yet. The repository includes a Docker image definition
and Render Blueprint; a hosting account must be connected before there is a
reviewer URL. Local production-style serving is tested separately from Docker.

## Run locally on Windows

Prerequisites: Python 3.12, Node.js 22.12 or newer, and PostgreSQL. The local
default uses port 5433. Configure your own database connection in backend/.env
if PostgreSQL uses another port or requires a password.

1. Clone the repository and open its folder.
2. Create the development database in PostgreSQL, named karigarflow_db. Do not
   use real client data. Create karigarflow_test_db for backend tests. The E2E
   preparation script creates its own separate database when permitted.
3. Set up the backend:

   ```powershell
   cd backend
   python -m venv venv
   .\venv\Scripts\python.exe -m pip install -r requirements.txt
   Copy-Item .env.example .env
   ```

4. Edit backend/.env locally: configure DATABASE_URL and generate a fresh
   SECRET_KEY. Never commit this file. The environment-variable names are listed
   below; credentials are not included in this document.
5. Apply migrations and start the API:

   ```powershell
   .\venv\Scripts\python.exe -m alembic upgrade head
   .\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```

6. In another terminal:

   ```powershell
   cd frontend
   npm ci
   npm run dev
   ```

7. Open http://localhost:5173. The frontend proxies /api to the local backend.
   Initial startup seeds synthetic users, stock and karigars, then adds the
   exact reference transactions and a separately labelled drift example. Repeat
   startup does not clear existing records. Do not run multiple seed workers.

## Demo accounts

These published credentials are only for the synthetic reviewer demo. They are
not production credentials for a real workshop.

| Account | Email | Demo password | Scope |
| --- | --- | --- | --- |
| Owner / managing partner | owner@karigarflow.com | Owner@123 | Company stock, statements, Finance review and operations |
| Finance head | finance@karigarflow.com | Finance@123 | Category agreements and loss/drift review; no owner stock |
| Issue clerk | clerk@karigarflow.com | Clerk@123 | Issues, receipts, scale verification and individual balances |
| Workshop manager | manager@karigarflow.com | Manager@123 | Operational ledger; no stock totals or Finance alerts |
| Karigar | karigar1@karigarflow.com | Karigar@123 | Own Tamil/English slips and balances |
| Reference karigar | murugesan@karigarflow.com | Karigar@123 | Exact reference slips and 3.893g remaining fine balance |

## Reviewer walkthrough

1. Sign in as Clerk. Open the register, select a karigar and category, and enter
   a new job number. Upload database/seed/scale-demo.png. Inspect the proposed
   120.000g / 91.60% reading, confirm it and save an issue.
2. Create a receipt for the same job/category. Enter gross weight and stones;
   the backend derives net and fine weights. Optionally record a six-character
   HUID. The job's allowance is read-only; report actual wastage separately.
3. Change a photo-backed weight and attempt to save: the mismatch is blocked.
   Retake the photo or explicitly switch to manual entry. Uncertain readings
   never create a verified slip.
4. Sign in as Finance. Review the separate synthetic rising-wastage history.
   For an excess-loss receipt, inspect its evidence, enter findings and approve
   a write-off only after checking custody. It creates a linked adjustment.
5. Sign in as Owner for daily stock and CSV/print. Search the register/directory
   for KG-REFERENCE / Murugesan S: TX-30411, TX-30437 and TX-30438 preserve the
   supplied 109.920, 6.916 and 3.893g fine balances.
6. Sign in as the reference karigar on a phone-width screen. Own balances/slips default to
   Tamil with an English toggle; company stock and peer slips are inaccessible.

## Build, offline and test

`npm run build` in frontend creates frontend/dist. To serve it from FastAPI,
set FRONTEND_DIST locally to that directory's absolute path, then restart the
backend. FastAPI serves /api and the SPA on one origin. This is also the Docker
layout. Service-worker offline shell caching is enabled in the production build
over HTTPS or localhost; it is not enabled in Vite development mode.

Unsent form fields and retry keys are saved per signed-in user on that device.
After a reload, recheck the scale and confirm again. The application never
automatically posts an offline gold entry. Photos are stored on the server, not
in offline storage. A recovered photo must be reloaded, reattached or explicitly
removed before saving. Drafts contain sensitive operational input: use managed
tablets, sign out between users, and clear drafts on a shared/untrusted device.

Backend tests use only karigarflow_test_db. From the repository root:

```powershell
.\backend\venv\Scripts\python.exe -m pytest backend/tests -q -p no:cacheprovider
```

For browser tests, build the frontend and install Chromium:

```powershell
cd frontend
npm run build
npx playwright install chromium
cd ..
.\backend\venv\Scripts\python.exe scripts/run_e2e.py
```

The runner creates/migrates and resets only karigarflow_e2e_db, starts the built
app on port 8011, runs Playwright and stops its own server. Keep that port free.
E2E_DATABASE_URL can configure the connection, but its database name must stay
karigarflow_e2e_db. The preparation script needs permission to create that
database. Do not put valuable data in the disposable E2E database.
Playwright checks real OCR, role boundaries, Finance review, Tamil phone layout,
offline reload recovery, CSV and print. Screenshots are in frontend/test-results.

## Deploy

The Dockerfile builds React and serves it alongside FastAPI. Startup applies
Alembic migrations before starting one Uvicorn worker. Images persist inside
PostgreSQL, not the web container's temporary filesystem.

Connect this GitHub repository in Render and create a Blueprint from render.yaml.
Review the resource plan before creation. The Blueprint requests a free demo web
service and free PostgreSQL, generates the signing secret and wires the database.
Once deployment is healthy, test every demo role and update the live URL at the
top of this file and in the TDD before submitting.

Render's free web service sleeps after inactivity and free PostgreSQL expires
30 days after creation. Arrange a review window or a persistent plan before
relying on it. See https://render.com/docs/free. No paid resource is created by
the local implementation. The Docker daemon was unavailable during local QA;
the image built successfully in GitHub CI for implementation commit 5265aba:
https://github.com/siddharthranka18/KarigarFlow/actions/runs/42276478796.
This is build validation, not verification of a live hosted runtime.

## Environment variables (names only)

Required for hosted deployment: DATABASE_URL, SECRET_KEY, ENVIRONMENT.

Optional application settings: SEED_DEMO_DATA, FRONTEND_DIST, ALLOWED_ORIGINS,
ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, PROJECT_NAME,
DEFAULT_PURITY_PURCHASE, DEFAULT_PURITY_ORNAMENT_22K,
DEFAULT_PURITY_ORNAMENT_18K, MAX_ALLOWED_WASTAGE_PERCENT,
LOSS_ALERT_THRESHOLD_GRAMS.

Hosting supplies PORT. Browser QA optionally uses E2E_DATABASE_URL and E2E_URL.
There is no OCR API key: RapidOCR runs on CPU using packaged ONNX models.
Per-karigar/category agreements are authoritative; the legacy global wastage
setting is not an override for recorded job allowances.

Before real-client use: disable demo seeding, replace all demo users, use TLS,
configure proxy upload limits, backups, image retention and distributed rate
limits, and confirm provisional wastage/write-off/drift policies with the client.
The local demonstration is not a substitute for those production controls.
