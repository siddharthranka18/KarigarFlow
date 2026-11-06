# KarigarFlow Architecture & System Design

## 1. Executive Summary

**KarigarFlow** is an operational Enterprise Resource Planning (ERP) and gold inventory ledger system purpose-built for an established jewellery manufacturer in Coimbatore, Tamil Nadu, operating:
- An internal manufacturing workshop with ~40 master karigars (goldsmiths).
- 5 retail showrooms across the region.
- ~180 employees across workshop masters, issue clerks, showroom managers, and finance teams.

KarigarFlow replaces paper ledger books (*Vellai Thaal* / slip registers) and manual Excel sheets with an auditable, decimal-safe system that tracks raw bullion, alloy grain, work-in-progress on artisan benches, return scrap, polishing dust recovery, and tolerance-based craft wastage.

---

## 2. Core Architectural Principles & Invariants

### 2.1 Decimal-Safe Gold Arithmetic (Rule 8)
- **Zero Floating-Point Tolerance:** In jewellery manufacturing, 0.001g (1 milligram) discrepancy across 40 karigars and hundreds of daily transactions aggregates into substantial financial loss. Floating-point IEEE-754 approximations (`0.1 + 0.2 != 0.3`) are strictly prohibited in the business logic and database.
- **Precision Conventions:**
  - Gold Weights: `Decimal("0.001")` (3 decimal places, milligram precision).
  - Gold Purity: `Decimal("0.01")` (2 decimal places, e.g., `91.60%` for 22K 916 BIS Hallmark, `75.00%` for 18K, `99.90%` for 24K bullion).
  - Rounding Mode: `ROUND_HALF_UP` explicit quantize.

### 2.2 Dynamic Balance Computation (Rule 7)
- **No Hardcoded Balances:** Current karigar outstanding balances and vault balances are computed dynamically from verified transaction records:
  $$\text{Closing Balance} = \text{Opening Balance} + \sum \text{Issues} - (\sum \text{Physical Receipts} + \sum \text{Settled Wastage} + \sum \text{Loss Adjustments})$$
- **Fine-Gold Normalization:**
  $$\text{Fine Gold Equivalent} = \frac{\text{Net Weight} \times \text{Purity Percentage}}{100}$$

---

## 3. Auditable Wastage Accounting Architecture

In jewellery manufacturing, craft loss (vaporization during torch soldering, filing micro-dust, acid pickling, polishing burn-off) is physically unavoidable. However, it must never be silently subtracted without an auditable ledger event.

### 3.1 Five-Pillar Accountability Ledger
The system explicitly distinguishes and tracks:
1. **Fine Gold Issued to Karigar ($\text{Au}_{\text{issued}}$):**
   Raw 24K bar or 22K alloy grains physically transferred from the vault to the artisan's custody (`ISSUE`).
2. **Fine Gold Physically Returned ($\text{Au}_{\text{returned}}$):**
   Gold physically weighed back into the workshop vault across three categories:
   - Finished Ornaments (`RECEIPT_ORNAMENT`)
   - Melting Scrap / Wire Ends / Cuttings (`RECEIPT_SCRAP`)
   - Recovered Polishing & Filing Dust (`RECEIPT_DUST`)
3. **Fine Gold Legitimately Consumed as Wastage ($\text{Au}_{\text{wastage}}$):**
   Approved craft loss within benchmark tolerance. An explicit, auditable accounting entry (`WASTAGE_SETTLEMENT`) is created with its own slip number (`WST-...`) linked to the parent receipt slip.
4. **Excess Wastage Requiring Investigation ($\text{Au}_{\text{excess}}$):**
   Wastage exceeding allowed benchmark tolerance by $> 0.100\text{g}$. Flagged as an active **Loss Alert**. It is NOT automatically settled; it remains an outstanding liability against the karigar pending physical bench sweeps and Finance Head audit.
5. **Remaining Outstanding Fine Gold ($\text{Au}_{\text{balance}}$):**
   $$\text{Au}_{\text{balance}} = \text{Au}_{\text{issued}} - (\text{Au}_{\text{returned}} + \text{Au}_{\text{wastage}})$$

### 3.2 Double-Entry Accounting Treatment
| Event | Karigar Bench Account | Workshop Vault Account | Manufacturing Wastage Expense |
|---|---|---|---|
| **Gold Issue** | **Debit (+)** (Artisan liability increases) | **Credit (-)** (Vault stock decreases) | *No effect* |
| **Ornaments Returned** | **Credit (-)** (Artisan liability decreases) | **Debit (+)** (Vault physical stock increases) | *No effect* |
| **Scrap Returned** | **Credit (-)** (Artisan liability decreases) | **Debit (+)** (Vault scrap stock increases) | *No effect* |
| **Legitimate Wastage Settlement** | **Credit (-)** (Artisan relieved of approved loss) | *No effect* (Gold is unrecoverable) | **Debit (+)** (Recognized workshop craft expense) |
| **Excess Wastage Resolution** | **Credit (-)** (Upon verified audit / cash recovery) | *No effect* (or Cash Account Debit) | **Debit (+)** (Investigated loss write-off) |

### 3.3 Complete Lifecycle Reconciliation Example (100g Order Audit)
Consider a standard batch workflow tracked in `test_complete_issue_receipt_wastage_settlement_workflow`:
1. **Issue:** $100.000\text{g}$ 22K gold @ $91.60\%$ purity is issued to the artisan ($\text{Fine Gold} = 91.600\text{g}$).
2. **Finished Ornament Receipt:** The artisan delivers $95.000\text{g}$ finished ornament @ $91.60\%$ ($\text{Fine Gold} = 87.020\text{g}$) and reports $1.900\text{g}$ craft wastage.
3. **Wastage Settlement:** With allowed tolerance @ $2.00\%$ ($1.900\text{g}$ on $95.000\text{g}$), actual $1.900\text{g}$ is approved. An explicit `WASTAGE_SETTLEMENT` slip ($1.900\text{g}$ gross, $1.740\text{g}$ fine) is created.
4. **Intermediate Balance Audit:**
   - Accounted so far: $95.000\text{g} + 1.900\text{g} = 96.900\text{g}$ gross ($88.760\text{g}$ fine).
   - Remaining balance: $100.000\text{g} - 96.900\text{g} = \mathbf{3.100\text{g}}$ gross ($\mathbf{2.840\text{g}}$ fine).
   - **Accounting Category:** This remaining balance is **Outstanding Physical Gold in Karigar Hands (Bench Scrap / WIP)**. It is **NOT** excess wastage, because actual wastage ($1.900\text{g}$) was within tolerance. The job order is not yet closed.
5. **Scrap Return:** The artisan returns $3.100\text{g}$ gross of bench scrap cuttings @ $91.60\%$ ($2.840\text{g}$ fine) via `RECEIPT_SCRAP`.
6. **Final Reconciliation:** Total accounted = $95.000 + 1.900 + 3.100 = 100.000\text{g}$ gross ($91.600\text{g}$ fine). Net outstanding balance for the batch is exactly $\mathbf{0.000\text{g}}$ gross and $\mathbf{0.000\text{g}}$ fine.

---

## 4. Database-Enforced Idempotency & Duplicate Protection

### 4.1 Architecture
To guarantee that network drops, browser timeouts, and rapid double-clicks never create duplicate accounting entries:
1. Every transaction submission accepts an `idempotency_key` (via HTTP Header `Idempotency-Key` or JSON body `idempotency_key`).
2. The `gold_transactions` table enforces uniqueness at the database engine level:
   `op.create_index('ix_gold_transactions_idempotency_key', 'gold_transactions', ['idempotency_key'], unique=True)`
3. **Safe Retries:** If a request is received with an existing `idempotency_key`, the backend immediately replays and returns the existing transaction record without creating a duplicate or modifying balances.
4. **Legitimate Identical Transactions:** Distinct physical transactions with identical weights, karigars, and purity (e.g. issuing two identical 10.000g batches back-to-back) are processed independently and assigned unique idempotency keys by the client. The brittle 10-second artificial suppression window has been replaced entirely.

---

## 5. Client Sample Data Taxonomy

The application maintains a strict taxonomy to separate parameters explicitly provided in the client problem statement from synthetic evaluation data:
- **`CLIENT_BRIEF_SPECIFICATIONS`**:
  Specifications explicitly provided in the client brief:
  - Workshop location: Coimbatore internal workshop with 5 regional retail showrooms.
  - Organization size: ~40 karigars and ~180 employees.
  - Functional purpose: Replacement of paper gold ledgers (*Vellai Thaal*) and manual Excel sheets.
  - Scale & Precision: 3-decimal precision for gold weights (0.001g), 2-decimal precision for purity (0.01%).
  - Governance: Mandatory human confirmation for scale reading images before ledger posting.
- **`SYNTHETIC_KARIGAR_PROFILES`**:
  Representative craftsmen profiles created for demonstration purposes reflecting regional specializations (temple jewellery, solid kadas, antique cast chokers, stone setting, die stamping, chains). All individual names, codes, phone numbers, and starting balances are synthetic demo data.
- **`SYNTHETIC_VAULT_INVENTORY`**:
  Demonstration vault holdings illustrating standard workshop raw materials (24K pure bullion bar, 22K 916 casting grain, and melting scrap).
- **`SYNTHETIC_DEMO_TRANSACTIONS`**:
  Demonstration workflow transactions exercising the complete lifecycle: Issue $\to$ Jewellery Receipt $\to$ Scrap Return $\to$ Wastage Settlement $\to$ Loss Alert.

---

## 6. Database Schema Design (Updated)

```
┌─────────────────────────────────────────────────────────────┐
│                       gold_transactions                     │
├─────────────────────────────────────────────────────────────┤
│ id (PK)                                                     │
│ slip_number (VARCHAR 100, UNIQUE)                           │
│ idempotency_key (VARCHAR 100, UNIQUE, INDEX)                │
│ related_slip_number (VARCHAR 100, INDEX)                    │
│ transaction_type (VARCHAR 50)                               │
│ karigar_id (FK -> karigars.id)                              │
│ created_by_user_id (FK -> users.id)                         │
│ item_description (VARCHAR 255)                              │
│ gross_weight (NUMERIC 10, 3)                                │
│ stone_weight (NUMERIC 10, 3)                                │
│ net_weight (NUMERIC 10, 3)                                  │
│ purity_percent (NUMERIC 5, 2)                               │
│ fine_weight (NUMERIC 10, 3)                                 │
│ allowed_wastage_percent (NUMERIC 5, 2)                      │
│ actual_wastage_weight (NUMERIC 10, 3)                       │
│ wastage_variance_weight (NUMERIC 10, 3)                     │
│ is_loss_alert (BOOLEAN)                                     │
│ scale_reading_confirmed (BOOLEAN)                           │
│ scale_image_url (VARCHAR 500)                               │
│ notes (TEXT)                                                │
│ created_at (DATETIME)                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. Perpetual Vault Inventory & Physical Gold Conservation

### 7.1 Location-Level Custody Accounting
To prevent gold from disappearing or being double-counted across physical custody transitions, the system enforces perpetual location accounting across three primary custody centers:
1. **Central Strongroom Vault:**
   $$\text{Closing Vault Fine} = \text{Opening Vault Fine} - \sum \text{Fine Issued} + \sum \text{Fine Physically Returned} + \sum \text{Purchases Fine}$$
2. **Karigar Bench Custody:**
   $$\text{Closing Karigar Fine} = \text{Opening Karigar Fine} + \sum \text{Fine Issued} - \sum \text{Fine Physically Returned} - \sum \text{Settled Wastage Fine} - \sum \text{Loss Adjusted Fine}$$
3. **Refinery Stock:**
   $$\text{Closing Refinery Fine} = \text{Opening Refinery Fine} + \sum \text{Dispatches to Refinery Fine} - \sum \text{Returns from Refinery Fine}$$

### 7.2 Total Physical Company Gold Conservation
$$\mathbf{\text{Total Company Physical Fine Gold} = \text{Closing Central Vault Fine} + \text{Closing Refinery Fine} + \text{Closing Karigar Custody Fine}}$$

Transfers between the central vault and karigar workbenches are strictly zero-sum ($\Delta = 0$). Total company physical gold changes **ONLY** upon:
- Approved craft wastage consumption ($-\text{Settled Wastage Fine}$)
- Write-offs or verified recoveries ($-\text{Loss Adjustments}$)
- Outside bullion purchases ($+\text{Purchases Fine}$)

---

## 8. Test Database Isolation Architecture

### 8.1 Zero-Mutation Guarantee
Automated testing must never contaminate development or client demonstration environments. To guarantee absolute isolation:
- `conftest.py` configures `TEST_DATABASE_URL = "postgresql+psycopg2://postgres@localhost:5433/karigarflow_test_db"`.
- A hard assertion verifies that the target database is strictly `karigarflow_test_db`.
- FastAPI's `get_db` dependency is overridden with `TestingSessionLocal` across all test requests.
- An autouse fixture truncates and reseeds `karigarflow_test_db` deterministically prior to each test case.
- Live database verification tests (`test_dev_database_isolation_safety`) confirm that running automated test suites causes zero row changes in `karigarflow_db`.
