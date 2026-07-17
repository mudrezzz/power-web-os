# Power Web benchmark intake

`power_web_benchmark.schema.json` is the machine schema for the user benchmark.

The accepted dataset is stored as `benchmark.user.json`. Its canonical SHA-256
is stored in `benchmark.freeze.json` with `accepted_by_user=true`.

`benchmark.source.json` records the source workbook hash and the privacy filter.
The source workbook is not copied into the repository because it also contains
phone numbers, email addresses, Telegram handles and outreach notes. None of
those values are retained in the normalized benchmark.

The accepted SIBUR dataset contains 10 source-native profile controls, 8
identity pairs, all three employment states and 4 relationship/influence
controls. One profile is an anonymous public HH resume and remains anonymous.

Rebuild the accepted artifacts from the source workbook with:

```powershell
python scripts/normalize_power_web_benchmark.py `
  --source <path-to-sibur_priority_contacts.xlsx> `
  --output-dir docs/radar/pipelines/power-web-discovery/benchmark `
  --accepted-by-user `
  --accepted-at <accepted-timestamp>
```

The script reads only public company/name/role/source columns. It refuses to
freeze without explicit user acceptance and fails if the selected workbook
rows no longer match the approved mappings.

Blind controls are evaluator-only. `planning_payload(guided=False)` contains
the account, product, role policy and allowed lanes, but no blind person refs,
URLs, pair labels or expected answers.
