# Remote persisted history migration

Session: `20260722-history-migration`

Validation status: **PASS**

## Cause

Normal remote `Sync` and `Deploy` correctly excluded `demo/output`, so the
server started from the deterministic fixture database. The local instance had
61 persisted lifecycle records for `Benchmark / SIBUR holding contour`, while
the server had only `radar-run-fixture-power-web-handoff` with two candidates.

## Migration

- Uploaded local checkpointed SQLite SHA-256:
  `2c324810e07d153669810ff3de8eb3db3a07ad6b00642600b4cb2865db90d0ef`.
- The source integrity check found five unreadable technical-trace rows in
  `radar-run-d8e4e3f7-b98a-40c8-a1d9-ca3a8b0d2249` from `toir-quick-live`.
- A clean logical database retained all 109 lifecycle runs, all 69 candidate
  outputs, all 12 signal outputs and 6,957 of 6,962 technical traces.
- Final clean database SHA-256 before normal startup:
  `7e3698cef460fb31682f363880c627212585edd355ec8ce4df652dd35947b5e5`.
- SQLite integrity passed and foreign-key issues equalled zero.
- Previous server state was retained at
  `/opt/power-web-os/shared/backups/power_web_os.sqlite3.before-20260722-history-migration.bak`.

## API and UI proof

- Benchmark candidate-discovery history: 46 runs.
- Benchmark signal-monitoring history: 15 runs.
- Latest completed candidate run:
  `radar-run-b03fac86-7307-448f-8deb-c1ea1794956c`.
- Latest public surface: 91 candidates, 84 accepted and 7 review-needed.
- Historical blind run `radar-run-3bbf9c0f-330e-4468-8901-966a751234a8`
  opens directly with 77 candidates, 71 accepted and 6 review-needed.
- Focused remote Playwright UI check passed with zero browser errors.
- API/worker restart retained the same counts and histories.

Screenshot: `frontend/test-results/radar-history-migration.png`.

Provider calls and new Radar, Signal Monitoring or Power Web runs: `0`.
