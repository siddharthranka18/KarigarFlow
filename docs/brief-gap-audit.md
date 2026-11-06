# Core build completion and acceptance limits

Updated 7 November 2026 against the actual client brief. This supersedes the
earlier gap snapshot. Scope remains the Software Engineering core, with selected
depth; the product is not a replacement for showroom billing or a production ERP.

| Requirement | Implemented and checked |
| --- | --- |
| Karigar master | Validated category-to-wastage agreements. Finance/owner editor; other roles cannot change them. |
| Issues and receipts | Explicit job/category, net/fine maths, optional HUID, running balances, per-job and total overdraw checks, vault protection and linked settlements. |
| Client reference | Exact three slips seeded additively under KG-REFERENCE. API regression preserves 109.920, 6.916 and 3.893g fine balances. |
| Scale-photo AI | Actual local ONNX OCR, retained photo beside proposal, uncertainty handling, explicit confirmation and server mismatch blocking. No paid API key. |
| Loss and drift | Finance/owner-only discrepancy review, same-category six-receipt drift rule and linked write-offs with notes. No accusations or automatic penalties. |
| Daily stock | Owner-only opening/movement/closing custody for vault, refinery and karigars, CSV and print. |
| Permissions | Separate Finance and owner accounts. Clerks cannot fetch stock totals or review endpoints. Review flags/notes are masked in operational slips. Karigars see only self. |
| Phone/Tamil | Own Tamil/English cards. Phone-width screenshots inspected; measurement fields stack to preserve readable digits. |
| Power/network cuts | Static production shell caches offline. Per-user drafts and submission keys recover after offline reload; no automatic offline posting. |
| UI feedback | Loading/error/empty states, retry controls, labelled inputs, focus-managed dialogs and review success feedback. |
| Validation | 67 backend tests, four production-build browser flows, build success and zero known npm advisories at validation. GitHub repository verified public. |
| Submission | TDD PDF plus deployment.md packaged in one ZIP under 25 MB. GitHub URL is at the top of the TDD; accounts/run steps are documented. |

The implementation uses labelled provisional policies, not undocumented client
facts. See technical-design.md assumptions A1–A14 for calculation basis, category
defaults, excess/drift settings, write-off scope, baseline/timezone interpretation,
OCR score limits and managed-device draft storage.

External acceptance still needed: connect hosting and verify a live reviewer URL
if deployment is desired; obtain real workshop photo trials and native Tamil
acceptance; confirm business policies with the client. A Docker definition and
Render Blueprint are provided, but the local Docker daemon was unavailable.
CI is configured; consult its actual run rather than assuming it succeeded.

Deliberate cuts: optional old-gold/PAN/payment desk, Tally-specific integration,
refinery transfer/assay workflow, period-close snapshots, partial/cash settlements,
cross-device offline synchronization and production operations. Refinery baseline
custody is included and carries forward. CSV is not represented as Tally output.
Client savings are targets/assumptions; no measured ROI is claimed.
