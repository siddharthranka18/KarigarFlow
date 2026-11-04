# Assumptions & Requirements

The client explicitly requires assumptions to be documented and tracked across development cycles. All assumptions below are provisional and validated against the jewellery workshop problem statement.

## Core Operational Assumptions

1. **Synthetic Data for Demonstration:**
   - The application is initialized with realistic synthetic demonstration data reflecting a Coimbatore jewellery workshop (4 master karigars, 24K bullion, 22K 916 alloy casting grain, melting scrap, and test issue slips).
2. **Authentication & RBAC:**
   - Role-Based Access Control is enforced on both frontend routes and backend FastAPI dependencies.
   - Roles: `admin` / `finance_head`, `issue_clerk`, `manager`, and `karigar`.
3. **Karigar Privacy & Scope Boundary:**
   - Karigars can view their own slips and balances only. They cannot view central vault inventory, other craftsmen's balances, or overall company financial figures.
4. **Gold Weight Precision:**
   - All gold weights (gross, net, stones, scrap, dust, wastage, balances) are stored, calculated, and displayed to **3 decimal places** (milligram precision, e.g. `12.450 g`).
   - Floating-point representations are forbidden; all calculations use Python's `Decimal` with `ROUND_HALF_UP`.
5. **Gold Purity Conventions:**
   - Purity percentages are stored and displayed to **2 decimal places** (e.g. `91.60%` for 22K 916 Hallmark, `75.00%` for 18K, `99.90%` for 24K pure bullion).
6. **Backend-Verified Accounting:**
   - Fine-gold calculations and live balances are computed exclusively on the backend (`fine_weight = net_weight * purity / 100`). The frontend displays live previews for clerk convenience but final ledger figures are strictly determined by the backend.
7. **Relational Database:**
   - PostgreSQL is the primary database with strict `Numeric(10, 3)` and `Numeric(5, 2)` types, managed via SQLAlchemy 2.0 and Alembic migrations.
8. **AI-Assisted Scale Reading Governance:**
   - AI-extracted scale readings require explicit human confirmation before saving to ledger slips, preventing automatic erroneous postings.
9. **Wastage & Loss Alert Threshold:**
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
