# Receipt reliability

Receipt slips and their automatically generated wastage settlements now commit
in one database transaction. A settlement write failure rolls back the receipt
and allows a retry with the same submission key. PostgreSQL locks the selected
karigar row while custody changes are validated and saved. A retry rechecks its
key after acquiring that lock.

Receipt validation includes both the returned gross weight and the wastage
being settled. It also checks the combined fine gold against available custody.
Both constraints must pass before either entry is written.

Assumption: a receipt and its approved wastage cannot reduce either recorded
gross custody or fine custody below zero. A purity mismatch requiring an assay
adjustment must be reviewed separately; this task does not create adjustments.

The transaction form retains the same submission key for an unchanged payload
when the user retries after an error. Changed payloads receive a new key. This
protection lasts for the current form session, not across browser reloads.

Regression coverage includes a simulated settlement insert failure, unchanged
balances after rollback, successful retry without duplicates, gross and fine
overdraw rejection, exact balance closure and two competing PostgreSQL receipt
requests. High-volume concurrency has not been load-tested. Scale-image extraction and finance loss approval
remain separate unfinished workflows.
