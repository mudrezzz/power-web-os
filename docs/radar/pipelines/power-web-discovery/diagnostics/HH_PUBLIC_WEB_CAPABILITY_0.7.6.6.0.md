# HH.ru public-web capability probe

Date: 2026-07-17
Outcome: `public_search_only` / `PASS`

The probe used three ordinary search patterns restricted to `hh.ru`: account +
technical role, account + production title/unit, and role + geography. All three
returned publicly indexed HH result pages with URL/title/snippet metadata.

No HH API, OAuth, employer account, mass crawling or direct resume extraction
was used. API calls: **0**. Private contacts retained: **0**. Raw pages retained:
**0**.

The result proves only source-lane feasibility. A citation or inaccessible
indexed page is a source lead. It does not prove a person's name, identity,
employment or relationship.

Machine-readable receipts are stored in
`HH_PUBLIC_WEB_CAPABILITY_0.7.6.6.0.json`.
