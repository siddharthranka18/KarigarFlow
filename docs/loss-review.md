# Finance loss review

Loss Alerts now separates open reviews from approved write-offs. Only flagged
ornament receipts are counted as alerts; generated wastage settlements are not
separate incidents. Finance and owner can inspect review evidence. Other roles
receive operational slips without review flags or investigation notes.
Only admin/owner/Finance Head can approve a loss, with investigation notes of 10–2000
characters and explicit confirmation. Scale status reflects the stored value.

Assumption: the demo supports a full write-off of the receipt's excess gross
wastage at its recorded purity after Finance investigation. This is a provisional
business policy, not a confirmed client requirement. Partial settlements, cash
recovery, rejection/reopening and approval of recovered gold are not supported.
Record recovered gold as a physical receipt, then investigate remaining custody;
this workflow refuses a write-off exceeding available gross or fine gold.
Per-job and aggregate custody checks prevent deductions beyond remaining stock.
Finance must still verify whether an earlier recovery is relevant to this
investigation; the software does not infer intent from a physical return.

POST /api/loss-alerts/{id}/write-off creates one LOSS_ADJUSTMENT linked to the
original receipt. The server computes weights from the stored variance. Creator,
timestamp and investigation notes stay in that ledger entry. Original receipts
and flags are preserved. The adjustment is accounting consumption, not a vault
receipt or scale measurement. No database migration is needed.

The existing karigar row lock serializes approval with other custody changes.
A repeat request returns the existing adjustment without changing its notes.
A reserved, unique idempotency key provides additional duplicate protection.
Generic transaction creation now rejects manual loss/wastage entries and unknown
types so clerks cannot bypass review. No edit/delete review endpoints exist.

An alert is resolved when a same-karigar LOSS_ADJUSTMENT links to its receipt.
Open counters and the legacy loss-alert filter exclude resolved receipts and
duplicate settlement flags. Historical linked adjustments are treated as
resolved; legacy partial entries require manual audit before relying on this
status. The new page shows the latest 100 reviews per category and says when the
limit is reached.

Manual review: create an ornament receipt with actual wastage above its allowance
by more than 0.100g. Open Loss Alerts as Finance, inspect the receipt, record bench
findings and confirm the write-off. Check Approved write-offs and inspect the
adjustment for its approver. Verify that vault stock stays unchanged, company
gold and karigar liability decrease, and open counters fall by one. Sign in as
Clerk to confirm approval is unavailable. All sample notes must be synthetic.
