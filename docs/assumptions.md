# Assumptions & Requirements

The client explicitly requires assumptions to be documented and tracked across development cycles. All assumptions below have been verified against the jewellery workshop problem statement and validated with regression test suites.

## Core Operational Assumptions & Invariants

1. **Synthetic Data for Demonstration:**
   - The application is initialized with realistic synthetic demonstration data reflecting a Coimbatore jewellery workshop (4 master karigars, 24K bullion, 22K 916 alloy casting grain, melting scrap, and test issue slips).
2. **Authentication & RBAC:**
   - Role-Based Access Control is enforced on both frontend routes and backend FastAPI dependencies.
   - Roles: `admin` / `finance_head`, `issue_clerk`, `manager`, and `karigar`.
3. **Karigar Privacy & Scope Boundary:**
   - Karigars can view their own slips and balances only. They cannot view central vault inventory, other craftsmen's balances, or overall company financial figures.
   - Backend APIs (`/api/karigars/{id}`, `/api/transactions`, `/api/inventory`, `/api/transactions/daily-summary`) explicitly enforce this boundary and reject ID tampering with HTTP 403 Forbidden.
4. **Gold Weight Precision:**
   - All gold weights (gross, net, stones, scrap, dust, wastage, balances) are stored, calculated, and displayed to **3 decimal places** (milligram precision, e.g. `12.450 g`).
   - Floating-point representations are strictly forbidden; all calculations use Python's `Decimal` with explicit `ROUND_HALF_UP`.
5. **Gold Purity Conventions:**
   - Purity percentages are stored and displayed to **2 decimal places** (e.g. `91.60%` for 22K 916 Hallmark, `75.00%` for 18K, `99.90%` for 24K pure bullion).
   - In Indian jewellery workshops, 22K is standardized to `91.60%` (916 BIS Hallmark), not theoretical `91.67%` (22/24).
6. **Karigar Opening Balances (Gross vs Fine):**
   - Opening balances represent physical gross gold on the artisan's bench (`opening_balance_gross`) alongside its pure fine gold equivalent (`opening_balance_fine`). Both are tracked separately and never confused.
7. **Job Wastage Settlement Accounting:**
   - When a job is completed, the accounted return equals:
     $$\text{Accounted Weight} = \text{Finished Ornament} + \text{Scrap Cuttings} + \text{Recovered Dust} + \text{Verified Actual Wastage}$$
   - Relieving the karigar's physical custody of the consumed craft wastage prevents ghost bench balances from accumulating.
8. **Negative Balance Protection:**
   - Receipt transactions cannot exceed the karigar's active physical gold balance. Attempting to record returns greater than held gold triggers an HTTP 400 Bad Request error.
9. **Idempotency & Duplicate Submission Guard:**
   - Rapid double-clicks or repeated submissions with identical parameters within a 10-second window are detected and rejected with HTTP 409 Conflict.
10. **Backend-Verified Accounting:**
    - Fine-gold calculations and live balances are computed exclusively on the backend (`fine_weight = net_weight * purity / 100`).
11. **Relational Database & Migrations:**
    - PostgreSQL is managed exclusively via Alembic migrations. `Base.metadata.create_all()` is not used in production runtime to prevent competing schema managers.
12. **AI-Assisted Scale Reading Governance:**
    - AI-extracted scale readings require explicit human confirmation before saving to ledger slips, preventing automatic erroneous postings.
13. **Wastage & Loss Alert Threshold:**
    - Workshop default benchmark allows up to `2.50%` craft wastage.
    - Any actual craft wastage exceeding the allowed tolerance by more than `0.100 g` (100 milligrams) triggers a high-priority **Loss Alert**.

---

## Confirmed Client Requirements

- **Gold Issue and Receipt Tracking:** Distinct slip numbering (`ISS-...`, `REC-...`), tracking raw gold, alloy grains, finished ornaments, and scrap cuttings.
- **Fine-Gold Accounting:** Instant normalization of multi-purity items (24K, 22K, 18K) to pure fine gold equivalent.
- **Dynamic Wastage Calculation:** Automatic comparison of allowed job wastage vs actual reported wastage with variance auditing.
- **Karigar Balances:** Continuous real-time balance tracking per craftsman without hardcoding.
- **Loss Alerts:** Visibility into jobs exceeding allowed variance.
- **Daily Stock Statement:** Complete reconciliation of central strongroom inventory, bench holdings, and day's movement.
- **AI Scale Verification:** Human verification workflow on precision scale entries.
