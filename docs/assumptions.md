# Assumptions & Operational Status

The client explicitly requires operational assumptions to be documented and tracked across development cycles. Below, system rules are partitioned into **Locked System Invariants** (verified by the test suite and database constraints) and **Provisional Business Rules** (functional defaults implemented for demonstration that await final client workshop master and finance head sign-off).

---

## 1. Locked System Invariants (Production-Enforced)

1. **Synthetic Data for Demonstration:**
   - The application is initialized with realistic synthetic demonstration data reflecting a Coimbatore jewellery workshop (~40 karigars, 5 showrooms, ~180 employees). Individual craftsman names, phone numbers, and starting balances are synthetic demo data created for functional evaluation.
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
7. **Auditable Wastage Settlement:**
   - Craft wastage is never silently subtracted from artisan liability. Every approved wastage settlement generates an explicit, auditable `WASTAGE_SETTLEMENT` ledger entry (`WST-...`) linked to the parent finished ornament slip.
8. **Negative Balance Protection:**
   - Receipt transactions cannot exceed the karigar's active physical gold balance. Attempting to record returns greater than held gold triggers an HTTP 400 Bad Request error.
9. **Database-Enforced Idempotency:**
   - Every transaction submission accepts an `idempotency_key` enforced by a database unique index (`ix_gold_transactions_idempotency_key`). Retried requests return the original transaction without creating duplicate entries or skewing balances.
10. **Backend-Verified Accounting:**
    - Fine-gold calculations and live balances are computed exclusively on the backend (`fine_weight = round_weight(net_weight * purity / 100)`). No client-side math is trusted.
11. **Relational Database & Migrations:**
    - PostgreSQL is managed exclusively via Alembic migrations. Runtime `Base.metadata.create_all()` is removed to eliminate competing schema mechanisms.
12. **AI-Assisted Scale Reading Governance:**
    - AI-extracted scale readings require explicit human confirmation before saving to ledger slips, preventing automatic erroneous postings.

---

## 2. Provisional Business Rules (Pending Client Workshop Sign-Off)

The following operational policies are implemented with sensible defaults for the prototype but remain **provisional** until formal sign-off from the Coimbatore workshop management:

1. **Wastage Benchmark Tolerances (Provisional):**
   - *Current Implementation:* Default craft wastage tolerance is set per karigar specialization (e.g., 1.50% for die stamping, 1.80% for solid bangles, 2.20% for handmade chains, 2.50% for antique casting).
   - *Status:* **Provisional.** The client may require dynamic, piece-level wastage benchmarks determined by ornament complexity, stone count, or specific alloy purity.
2. **Loss Alert Threshold (Provisional):**
   - *Current Implementation:* Any craft wastage exceeding allowed tolerance by more than `0.100 g` (100 milligrams) triggers a high-priority **Loss Alert**.
   - *Status:* **Provisional.** Workshop management will confirm whether this should remain a flat 100mg threshold across all job sizes or transition to a sliding scale (e.g., percentage of issued weight for larger batches).
3. **Excess Wastage Recovery & Commercial Settlement (Provisional):**
   - *Current Implementation:* Excess wastage is flagged as an active alert and remains an uncredited liability on the karigar's balance. It is not automatically forgiven.
   - *Status:* **Provisional.** The exact resolution policy (e.g., deducting pure gold value from making charges / artisan wages, conducting quarterly bench sweeps / acid floor recovery, or executive write-off) requires Finance Head policy definition.
4. **Inter-Showroom Gold Transit & Consignment (Provisional):**
   - *Current Implementation:* Central vault inventory models workshop stock. Finished goods are recorded in vault stock.
   - *Status:* **Provisional.** Separate transit ledgers, gate-pass documentation, and showroom receipt acknowledgments across the 5 retail showrooms will be clarified in Phase 2.

---

## 3. Confirmed Client Requirements Traceability

- **Gold Issue and Receipt Tracking:** Distinct slip numbering (`ISS-...`, `REC-...`, `SCP-...`, `DST-...`, `WST-...`).
- **Fine-Gold Accounting:** Instant normalization of multi-purity items (24K, 22K, 18K) to pure fine gold equivalent.
- **Dynamic Wastage Calculation:** Automatic comparison of allowed job wastage vs actual reported wastage with variance auditing.
- **Karigar Balances:** Continuous real-time balance tracking per craftsman without hardcoding.
- **Loss Alerts:** Visibility into jobs exceeding allowed variance.
- **Daily Stock Statement:** Complete reconciliation of central strongroom inventory, bench holdings, and day's movement.
- **AI Scale Verification:** Human verification workflow on precision scale entries.
