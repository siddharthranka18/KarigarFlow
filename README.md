# KarigarFlow

> **Jewellery Workshop Operations & Gold Inventory ERP**  
> Tailored for jewellery manufacturing businesses (5 showrooms, internal workshop, ~40 karigars, ~180 employees).

---

## Overview

KarigarFlow replaces paper ledgers and manual Excel sheets with an auditable, precision ERP designed for jewellery craftsmanship:
- **Gold Issue and Receipt Slips:** Track gold issued to karigars, returned finished ornaments, and scrap cuttings.
- **Fine-Gold Accounting:** Normalize multi-purity alloys (24K, 22K 916 Hallmark, 18K) into 24K pure fine gold equivalents using decimal-safe arithmetic.
- **Live Karigar Balances:** Real-time dynamic calculation of gold held by every craftsman.
- **Tolerance-Based Wastage Auditing:** Automatic comparison of allowed vs actual wastage with high-priority **Loss Alerts** (> 0.100g variance).
- **Daily Gold Stock Statement:** Full reconciliation between Central Strongroom Vault, artisan workbenches, and recovered filing dust.
- **AI-Assisted Scale Verification:** Support for calibrated precision scales with mandatory human confirmation.

---

## Technology Stack

### Frontend
- **Framework:** React 18 + TypeScript + Vite
- **Styling & Design System:** Tailwind CSS
  - Bespoke palette inspired by jewellery materials: warm parchment backgrounds (`#F9F6F0`), graphite text (`#1C1917`), and muted antique brass accents (`#B88730`).
  - Strict tabular numbers (`font-mono`) for weights and purities.
- **State & Routing:** TanStack Query v5 + React Router v6
- **Forms & Validation:** React Hook Form + Zod
- **Icons:** Lucide React

### Backend
- **Framework:** Python 3.12 + FastAPI
- **Database:** PostgreSQL (with SQLite automatic fallback)
- **ORM & Migrations:** SQLAlchemy 2.0 + Alembic
- **Validation:** Pydantic v2 (`pydantic-settings`, `email-validator`)
- **Authentication:** JWT Bearer tokens + Bcrypt password hashing
- **Testing:** Pytest

---

## Project Structure

```
KarigarFlow/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/          # auth, karigars, transactions, inventory, health
│   │   │   └── dependencies.py  # get_db, get_current_user, RBAC require_roles
│   │   ├── core/
│   │   │   ├── config.py        # Settings with Pydantic BaseSettings
│   │   │   └── security.py      # JWT creation, Bcrypt hashing
│   │   ├── db/
│   │   │   ├── base.py          # Declarative Base
│   │   │   └── session.py       # Engine & SessionLocal
│   │   ├── models/              # User, Karigar, GoldTransaction, GoldInventory
│   │   ├── schemas/             # Pydantic request/response schemas
│   │   ├── services/
│   │   │   └── gold_calculations.py # Decimal-safe arithmetic (0.001g precision)
│   │   └── main.py              # FastAPI application & auto-seed lifespan
│   ├── migrations/              # Alembic versioned migrations
│   ├── tests/                   # Pytest calculation verification suite
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── components/ui/       # Button, Badge, StatCard, Input, Table, Modal, AlertBanner
│   │   ├── features/auth/       # AuthContext, ProtectedRoute
│   │   ├── layouts/             # MainLayout with Coimbatore Workshop sidebar & topbar
│   │   ├── pages/               # Login, Dashboard, Karigars, Transactions, DailyStock, LossAlerts
│   │   ├── services/            # Typed ApiClient with Bearer token interceptor
│   │   ├── types/               # TypeScript interfaces
│   │   ├── utils/               # 3-decimal weight and 2-decimal purity formatters
│   │   ├── App.tsx              # Router & QueryProvider
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── tailwind.config.js
│
├── docs/
│   ├── architecture.md          # In-depth system design & invariants
│   └── assumptions.md           # Client assumptions & requirements
├── deployment.md                # Production & local deployment instructions
└── README.md
```

---

## Quick Start Guide

### 1. Backend Setup

```bash
cd backend

# Create & activate Python virtual environment
python -m venv venv
venv\Scripts\activate       # On Windows
# source venv/bin/activate  # On Linux/macOS

# Install dependencies
pip install -r requirements.txt

# Start FastAPI backend (runs on http://127.0.0.1:8000)
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
*Note: On initial startup, the backend automatically seeds the database with baseline Coimbatore workshop demonstration data and accounts.*

### 2. Frontend Setup

```bash
cd frontend

# Install npm dependencies
npm install

# Start Vite dev server (runs on http://127.0.0.1:5173)
npm run dev
```

### 3. Running Unit Tests

```bash
# Run backend calculation test suite
cd backend
venv\Scripts\pytest tests
```

---

## Pre-Seeded Demonstration Accounts

For ease of evaluation, the login page features a one-click demo switcher with credentials:

| Role | Email | Password | Access Scope |
|---|---|---|---|
| **Finance Head (Admin)** | `finance@karigarflow.com` | `Finance@123` | Full access: vault stock statements, karigars, loss alert audits |
| **Issue Clerk** | `clerk@karigarflow.com` | `Clerk@123` | Frontline operations: issuing & receiving gold slips, scale confirmation |
| **Workshop Manager** | `manager@karigarflow.com` | `Manager@123` | Bench management, karigar assignment, daily reconciliation |
| **Master Karigar** | `karigar1@karigarflow.com` | `Karigar@123` | Restricted view: personal slip history and active balance only |

---

## Architectural Guarantees

1. **Decimal-Safe Precision (Rule 8):** Python's `Decimal` with explicit `ROUND_HALF_UP` is used for all calculations:
   - Weights: `0.001g` (milligrams).
   - Purities: `0.01%`.
2. **Never Hardcoded Balances (Rule 7):** Karigar balances are dynamically aggregated from transaction logs.
3. **Loss Alert Threshold:** Actual wastage exceeding benchmark allowance by > 0.100g automatically flags an audit alert.
