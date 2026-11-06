# Daily stock statement

Open Daily Stock Statement, choose a workshop date, and refresh to fetch current
ledger data. CSV export uses the displayed response so exported values match the
screen, preserving backend decimal strings. Print uses a landscape layout and
hides navigation and controls. On smaller screens the table scrolls horizontally.
Export/print are disabled while loading, refreshing or after a fetch error.

The owner-only GET /api/stock-statement endpoint accepts statement_date as an ISO
date, defaulting to today's date in India. Future and invalid dates are rejected.
Karigars cannot access company stock figures. No migration is required.

The backend reconstructs opening custody by applying all earlier transactions to
baseline inventory and karigar balances. It applies entries inside the selected
India calendar day, from midnight inclusive to the next midnight exclusive, to
calculate closing stock. Today's statement is provisional through the latest
recorded transactions. Inactive karigars remain part of physical custody.
Each row satisfies opening + signed movements = closing. Internal issues and
returns cancel at company level. Wastage settlements and recorded loss
adjustments reduce company stock; purchases increase it. Reported wastage is not
counted again as physical consumption.

Assumptions and limits:

- Existing inventory lots and karigar opening balances precede all ledger
  history. No baseline effective date exists yet; this assumption applies to
  every selectable date. Editing baselines changes historical statements.
- Ledger timestamps are UTC; the workshop uses Asia/Kolkata (UTC+05:30).
  New transaction defaults explicitly persist naive UTC to match the current
  timestamp-without-time-zone column. Existing timestamps are interpreted as
  UTC; older rows written with a different server timezone need a separate
  timestamp audit before historical reports can be considered authoritative.
- Existing category/location text containing "refin" identifies refinery lots,
  consistent with the current inventory service. Refinery transfers are not
  supported, so refinery balances carry forward unchanged.
- Purchases are assigned to the central vault; loss adjustments reduce karigar
  custody. The endpoint reports existing entries and does not approve losses.
- This is reconstructed synthetic demo stock, not a signed physical count or a
  period-locked accounting statement. Baseline reads are not a period-close
  snapshot and must not be edited during statement generation.
- Gross weight includes stones where recorded; fine gold is the comparison
  basis across purities. Large ledger query optimization is deferred.

Tests cover ledger reconciliation, exclusion of later entries, India midnight
boundaries, inactive karigar custody, empty days, roles, and date validation.
Manual review: choose an empty day, create a current issue/receipt, refresh,
export CSV, inspect print preview, and check table scrolling on a phone.
