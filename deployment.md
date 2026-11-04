# KarigarFlow Deployment Guide

## 1. Prerequisites

- **Python:** 3.11 or 3.12
- **Node.js:** v18+ (tested with v22)
- **PostgreSQL:** 14+ (local instance running on port `5432` or `5433`)
- **Process Manager:** Systemd, Supervisor, or Docker

---

## 2. Environment Variables

Configure the following environment variables in `backend/.env`:

| Variable | Description | Example Value |
|---|---|---|
| `PROJECT_NAME` | Name of the ERP application | `KarigarFlow` |
| `ENVIRONMENT` | Deployment environment | `production` or `development` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg2://karigar_admin:secret@localhost:5432/karigarflow_db` |
| `SECRET_KEY` | Cryptographic secret for signing JWTs | `generate-a-secure-random-key-with-openssl` |
| `ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Session validity duration | `480` (8 hours / workshop shift) |
| `ALLOWED_ORIGINS` | Permitted CORS origins (comma-separated) | `https://karigarflow.internal.domain,http://localhost:5173` |
| `DEFAULT_PURITY_PURCHASE` | Benchmark purity for bullion ingots | `99.90` |
| `DEFAULT_PURITY_ORNAMENT_22K` | Standard 22K 916 Hallmark purity | `91.60` |
| `MAX_ALLOWED_WASTAGE_PERCENT` | Workshop wastage ceiling | `2.50` |
| `LOSS_ALERT_THRESHOLD_GRAMS` | Tolerance variance before loss alert | `0.100` |

---

## 3. Database Initialization & Migration

Ensure PostgreSQL is running and create the production database:

```sql
CREATE DATABASE karigarflow_db;
CREATE USER karigar_user WITH ENCRYPTED PASSWORD 'StrongPass123!';
GRANT ALL PRIVILEGES ON DATABASE karigarflow_db TO karigar_user;
```

Run Alembic to apply schema migrations:

```bash
cd backend
venv/bin/alembic upgrade head
```

---

## 4. Production Build & Deployment

### 4.1 Backend Service (Systemd / Uvicorn)

Create `/etc/systemd/system/karigarflow-backend.service`:

```ini
[Unit]
Description=KarigarFlow FastAPI Backend ERP
After=network.target postgresql.service

[Service]
User=karigar
WorkingDirectory=/opt/karigarflow/backend
ExecStart=/opt/karigarflow/backend/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 4
Restart=always

[Install]
WantedBy=multi-user.target
```

### 4.2 Frontend Production Build

```bash
cd frontend
npm install
npm run build
```
The compiled static assets are generated in `frontend/dist/`.

### 4.3 Reverse Proxy (Nginx Configuration)

```nginx
server {
    listen 80;
    server_name karigarflow.internal.domain;

    # Static frontend assets
    location / {
        root /opt/karigarflow/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API Proxy to FastAPI backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 5. Pre-Configured Demo Accounts

| Role | Email | Password | Access Scope |
|---|---|---|---|
| **Finance Head (Admin)** | `finance@karigarflow.com` | `Finance@123` | Full access: vault stock statements, karigars, loss alert audits |
| **Issue Clerk** | `clerk@karigarflow.com` | `Clerk@123` | Frontline operations: issuing & receiving gold slips, scale confirmation |
| **Workshop Manager** | `manager@karigarflow.com` | `Manager@123` | Bench management, karigar assignment, daily reconciliation |
| **Master Karigar** | `karigar1@karigarflow.com` | `Karigar@123` | Restricted view: personal slip history and active balance only |
