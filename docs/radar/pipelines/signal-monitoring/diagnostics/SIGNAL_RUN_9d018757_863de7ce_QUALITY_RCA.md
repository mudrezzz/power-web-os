# Signal Monitoring Live Quality RCA: 0.7.6.4.18.2.2

Status: Baseline diagnosis

Runs:

- `signal-run-9d018757-a96c-4902-92ac-b0bdb4d3bb50`
- `signal-run-863de7ce-cdab-456f-91f8-917c0a875452`

Source candidate run: `radar-run-3bbf9c0f-330e-4468-8901-966a751234a8`

## What Worked

- Both persisted runs completed through the dedicated Signal Monitoring API/job path.
- Every planned lane had a ledger outcome and every executed task had a receipt.
- The second run loaded per-lane watermarks and stable source keys.
- Two repeated sources were suppressed and no old event was republished as new.
- Official and open-web lanes remained separate from candidate discovery.

## Quality Failures

### Retrieval time was treated as event time

The first run projected four observed candidate/criterion outcomes. The source
and evidence contracts carried only `observed_at`, populated with the run time
`2026-07-10`. The validator therefore tested when the page was retrieved, not
when the article was published or the event occurred.

This incorrectly accepted two January 2024 reports about a SIBUR-Khimprom
maintenance/fire event inside a window beginning in July 2025:

- ChemAnalyst, publication date 25 January 2024;
- Fomag, publication date 18 January 2024.

The completed requirement `SM-VAL-01` was therefore too weak: it asserted the
presence of a parseable timestamp, not product-semantic event-time integrity.

### Known-source ownership was too broad

The input assembler built one global known-source pool from candidate refs.
Wikipedia and a POLIEF product page were scheduled for other legal entities.
Evidence validation prevented some false positives, but 6 of 14 calls were
spent on weak or cross-entity known-source tasks.

### Acceptance controls were not explicit

The live gate checked only aggregate `observed_count >= 2`. It did not match
candidate, criterion, canonical URL and expected date range. An unrelated or
out-of-window observed row could therefore help the live gate pass.

### Public semantics were internally inconsistent

Three observed pair outcomes had score zero. Missing dates were either accepted
using retrieval time or lost into generic review states instead of a dedicated
human-review temporal status.

## Corrective Decision

Slice `0.7.6.4.18.2.2` separates retrieval/publication/event times, retains
unknown-date evidence for review, introduces generic source capability and
candidate binding decisions, validates explicit post-run controls, and expands
live acceptance to six candidates and twelve candidate/criterion pairs.
