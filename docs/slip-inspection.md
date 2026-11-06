# Slip inspection

Implemented 6 November 2026 as a focused addition to the existing ledger.

Open Gold Transactions and select a slip number. The inspection shows persisted
gross, stone, net and fine weights, purity, reported wastage, variance, notes,
creator name and timestamp. Follow a receipt's linked wastage settlement and use
the parent link to return. No database migration is needed.

`GET /api/transactions/{transaction_id}` returns the slip, creator display name,
parent and direct child entries. Staff roles can inspect workshop slips;
karigars can inspect only slips belonging to their linked profile. Inaccessible
and missing slips both return 404. Linked records must share the same karigar.
Unknown staff roles are rejected. Existing daily-summary routing is preserved.

Assumption: related_slip_number identifies a direct accounting relationship,
not a complete job or order history. The view therefore makes no job completion
claim. Scale confirmation is a stored human assertion, not image verification.
Scale OCR and loss approval remain outside this task.

Review manually with the frontend and backend running:

1. Record a small ornament receipt against available karigar stock, with wastage
   inside allowance and a note.
2. Open its slip number; check stored values and note.
3. Open the settlement; follow its parent link back to the receipt.
4. Inspect a slip without linked entries to see the empty state.
5. Stop the backend and open a slip to check the error and retry controls.
6. Sign in as a karigar and inspect their own slips.

API regression tests cover receipt/settlement navigation, ownership,
unauthenticated requests, missing/invalid IDs, cross-karigar legacy links and
daily-summary route compatibility. Browser appearance and phone interaction
require manual review; build success does not establish visual quality.
