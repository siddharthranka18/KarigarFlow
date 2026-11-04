# KarigarFlow Architecture & System Design

## 1. Executive Summary

**KarigarFlow** is an operational Enterprise Resource Planning (ERP) and gold inventory ledger system purpose-built for an established jewellery manufacturer in Coimbatore, Tamil Nadu, operating:
- An internal manufacturing workshop with ~40 master karigars (goldsmiths).
- 5 retail showrooms across the region.
- ~180 employees across workshop masters, issue clerks, showroom managers, and finance teams.

KarigarFlow replaces error-prone physical ledger books (*Vellai Thaal* / slip registers) and manual Excel sheets with an auditable, decimal-safe system that tracks raw bullion, alloy grain, work-in-progress on artisan benches, return scrap, polishing dust recovery, and tolerance-based wastage.

---

## 2. Core Architectural Principles & Invariants

### 2.1 Decimal-Safe Gold Arithmetic (Rule 8)
- **Zero Floating-Point Tolerance:** In jewellery manufacturing, 0.001g (1 milligram) discrepancy across 40 karigars and hundreds of daily transactions aggregates into substantial financial loss. Floating-point IEEE-754 approximations (`0.1 + 0.2 != 0.3`) are strictly prohibited in the business logic and database.
- **Precision Conventions:**
  - Gold Weights: `Decimal("0.001")` (3 decimal places, milligram precision).
  - Gold Purity: `Decimal("0.01")` (2 decimal places, e.g., `91.60%` for 22K 916 BIS Hallmark, `75.00%` for 18K, `99.90%` for 24K bullion).
  - Rounding Mode: `ROUND_HALF_UP` explicit quantize.

### 2.2 Dynamic Balance Computation (Rule 7)
- **No Hardcoded Balances:** Current karigar outstanding balances and vault balances are computed from verified transaction records:
  $$\text{Closing Balance} = \text{Opening Balance} + \sum \text{Issues} - \sum \text{Receipts}$$
- **Fine-Gold Normalization:**
  $$\text{Fine Gold Equivalent} = \frac{\text{Net Weight} \times \text{Purity Percentage}}{100}$$

### 2.3 Wastage Governance & Loss Alerts
- Each jewellery job has an allowed wastage benchmark (typically `1.80% - 2.50%` based on craftsmanship complexity: casting, filigree, stamping, or stone-setting).
- Upon return of finished ornaments, scrap, and filings:
  $$\text{Actual Wastage} = \text{Issued Weight} - (\text{Ornaments} + \text{Scrap} + \text{Recovered Dust})$$
  $$\text{Allowed Wastage} = \frac{\text{Issued Weight} \times \text{Allowed Wastage } \%}{100}$$
  $$\text{Variance} = \text{Actual Wastage} - \text{Allowed Wastage}$$
- If $\text{Variance} > 0.100\text{g}$ (100 milligrams), a **Loss Alert** is triggered and flagged across the ERP.

---

## 3. Technology Stack & Component Separation

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                  │
│  - Tailwind CSS (Warm Parchment & Muted Brass Design System) │
│  - TanStack Query v5 (Server State & Auto-Revalidation)     │
│  - React Router v6 (Role-Protected Views)                   │
│  - Lucide Icons & Tabular Numeric Displays                  │
└──────────────────────────────┬──────────────────────────────┘
                               │ JSON over HTTP (REST)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI Engine)                 │
│  - Python 3.12 + Pydantic v2 Schema Validation              │
│  - Decimal-Safe Gold Calculation Engine                     │
│  - JWT Bearer Authentication & Role-Based Access Control    │
│  - Automatic Seed & Schema Management                       │
└──────────────────────────────┬──────────────────────────────┘
                               │ SQLAlchemy 2.0 (psycopg2)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                 PostgreSQL Relational Storage               │
│  - Strict Numeric(10, 3) Column Typing for Weights          │
│  - Numeric(5, 2) for Purity & Percentages                   │
│  - Alembic Schema Migration Versioning                      │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Database Schema Design

### 4.1 `users`
| Column | Type | Description |
|---|---|---|
| `id` | Integer, PK | Internal surrogate key |
| `email` | String(255), Unique | Staff login email |
| `hashed_password` | String(255) | Bcrypt hash |
| `full_name` | String(255) | Name and designation |
| `role` | String(50) | `admin`, `finance_head`, `manager`, `issue_clerk`, `karigar` |
| `is_active` | Boolean | Account status |
| `created_at` | DateTime | Timestamp (UTC) |

### 4.2 `karigars`
| Column | Type | Description |
|---|---|---|
| `id` | Integer, PK | Internal surrogate key |
| `karigar_code` | String(50), Unique | Unique code (e.g., `KG-CBE-001`) |
| `name` | String(255) | Craftsman full name |
| `phone` | String(50) | Contact number |
| `specialization` | String(100) | Craft (Temple Jewellery, Bangles, Cast Chokers) |
| `benchmark_wastage_percent`| Numeric(5, 2) | Default job wastage tolerance (e.g. 2.00%) |
| `opening_balance_gross` | Numeric(10, 3) | Opening ledger weight (g) |
| `opening_balance_fine` | Numeric(10, 3) | Opening fine-gold weight (g) |
| `user_id` | Integer, FK(users.id) | Optional link to karigar login |

### 4.3 `gold_transactions`
| Column | Type | Description |
|---|---|---|
| `id` | Integer, PK | Internal surrogate key |
| `slip_number` | String(100), Unique | Generated slip code (`ISS-...`, `REC-...`) |
| `transaction_type` | String(50) | `ISSUE`, `RECEIPT_ORNAMENT`, `RECEIPT_SCRAP`, `RECEIPT_DUST`, `PURCHASE` |
| `karigar_id` | Integer, FK(karigars.id) | Associated craftsman |
| `created_by_user_id` | Integer, FK(users.id) | Clerk/Manager who signed slip |
| `item_description` | String(255) | Batch/order item details |
| `gross_weight` | Numeric(10, 3) | Scale reading gross weight (g) |
| `stone_weight` | Numeric(10, 3) | Non-gold deductions (g) |
| `net_weight` | Numeric(10, 3) | Net gold weight (g) |
| `purity_percent` | Numeric(5, 2) | Gold purity (e.g. 91.60%) |
| `fine_weight` | Numeric(10, 3) | Calculated 24K equivalent (g) |
| `allowed_wastage_percent` | Numeric(5, 2) | Benchmark tolerance % |
| `actual_wastage_weight` | Numeric(10, 3) | Reported actual loss (g) |
| `wastage_variance_weight` | Numeric(10, 3) | Discrepancy beyond allowed (g) |
| `is_loss_alert` | Boolean | True if variance > 0.100g |
| `scale_reading_confirmed` | Boolean | Human-verified scale reading |

### 4.4 `gold_inventory`
| Column | Type | Description |
|---|---|---|
| `id` | Integer, PK | Internal surrogate key |
| `lot_code` | String(50), Unique | Vault lot reference |
| `category` | String(100) | Bullion 24K, 22K Grain, Melting Scrap, Finished |
| `gross_weight` | Numeric(10, 3) | Gross weight in vault (g) |
| `purity_percent` | Numeric(5, 2) | Purity % |
| `fine_weight` | Numeric(10, 3) | Pure gold equivalent (g) |
| `location` | String(100) | Vault / Safe location |

---

## 5. Security & Role-Based Access Control (RBAC)

1. **Finance Head (`finance_head` / `admin`):**
   - Full visibility into Daily Gold Stock Statements, Central Vault inventory, Karigar balances, and Loss Alert audits.
   - Authority to approve new karigar registrations and settle loss alerts.
2. **Issue Clerk (`issue_clerk`):**
   - Frontline bench operator.
   - Authorized to generate Issue Slips and Receipt Slips for karigars.
   - Confirms precision scale readings.
3. **Workshop Manager (`manager`):**
   - Oversees karigar assignments, daily bench stock reconciliations, and benchmark wastage calibration.
4. **Karigar (`karigar`):**
   - View-restricted to their own assigned slips and active fine-gold balance only (Assumption 3). Cannot view vault holdings or other karigars' accounts.

