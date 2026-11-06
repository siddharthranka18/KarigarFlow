# Core build alignment with supplied client brief

Reviewed against the actual brief supplied on 6 November 2026. It supersedes
assumptions in earlier progress reports. This is not complete compliance.

| Requirement | Current position |
| --- | --- |
| Karigar master | Profiles and one default wastage percentage exist. Per-item-category agreements are missing. |
| Issue/receipt maths | Decimal accounting, separate gross/net/fine, balances and settlements work. Explicit job-number and HUID fields are missing; descriptions are not equivalent. |
| Client sample | API regression reproduces 109.920, 6.916 and 3.893 fine balances. Exact sample transactions are not yet seeded into the reviewer demo. |
| Loss reviews | Threshold-based review and finance-only full write-off exist. Full write-off is a provisional policy. History-based drift detection is missing. |
| Daily statement | Date-based custody, CSV and print styling exist. Editable baselines and missing refinery transfers are documented. CSV is not Tally export. |
| Scale-photo AI | This phase adds local OCR, retained photo, proposed values, uncertainty, confirmation and server mismatch blocking. Real engine tested on a synthetic display; workshop photo accuracy is unmeasured. |
| Roles/privacy | Sign-in and karigar self-scope exist. Staff stock access and clerk/manager alert visibility are broader than the brief and need correction. Finance-to-owner mapping is an assumption; no partner role exists yet. |
| Mobile/Tamil | Responsive structure exists; phone visual review and Tamil slips remain missing. |
| Power/network cuts | In-session retries are protected. Durable offline drafts/recovery after power loss are missing. |
| Design | Existing restrained palette and aligned numbers; preview wording corrected. Full visual QA remains. |
| Submission | Incremental commits exist. Deployment, reviewer demo, TDD and submission ZIP remain unfinished. |

The sample leaves 3.893g fine outstanding. That is not automatically loss merely
because an allowance exists: actual wastage must be reported, and remaining gold
may still be scrap or WIP.

Next priorities: restrict stock/alert exposure; category agreements and explicit
job linkage; exact seeded scenario; durable tablet drafts; Tamil and photo/mobile
QA. Old-gold desk, PAN/payment recording and Tally export are optional depth for
this core build. Tax-rule implementation needs separate verified guidance if
selected. Billing replacement, loans and savings stay out of scope. Client
savings and reconciliation figures are assumptions/targets, not measured results.
