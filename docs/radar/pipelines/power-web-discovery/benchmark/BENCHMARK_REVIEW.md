# Power Web benchmark review

Status: accepted and hash-frozen on 2026-07-17.

## Intake

The user supplied `sibur_priority_contacts.xlsx` and explicitly requested that
it be used as the Power Web benchmark. The original workbook remains outside
the repository. `benchmark.source.json` records its SHA-256 and selected public
rows so the normalization is auditable without retaining private contacts.

## Accepted controls

- 8 role demands for technical, production, maintenance, reliability,
  technology, energy, automation and digital-transformation coverage.
- 10 source-native public profiles from official company pages, industry/event
  publications and public HH search results.
- 4 same-person pairs over independent sources.
- 4 different-person pairs.
- Employment controls for `current`, `former` and `unknown`.
- 4 relationship/influence controls, including review-needed hypotheses.
- 1 anonymous HH-style profile whose name remains unknown.

## Evidence quality decisions

- A fresh official source explicitly naming a person and role supports
  `current` employment.
- A public кадровый transition source explicitly saying that a role was held
  previously supports `former` employment.
- An indexed HH resume without reliable recency remains `unknown`; its title
  and employer do not prove current employment.
- Same-person controls expect at least `probable`, not an automatic merge.
- Influence inferred from a technical publication remains `review_needed`
  unless the source explicitly establishes the relationship.

## Privacy filter

Excluded from all repository artifacts:

- phone numbers and email addresses;
- Telegram and other messenger identifiers;
- private reports and contact-enrichment outputs;
- outreach history;
- private social profiles and image binaries.

Only public names or an anonymous marker, public role/employer facts, public
URLs, dates and product-safe expected facts are retained.
