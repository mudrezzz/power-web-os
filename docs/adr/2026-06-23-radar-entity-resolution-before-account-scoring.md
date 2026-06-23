# ADR: Radar Entity Resolution Before Account Scoring

## Status

Accepted.

## Context

Live Radar discovery can return mixed entities: legal entities, production
sites, plants, projects, installations, and assets. Treating every extracted
name as `legal_name` makes project or site mentions look like account
candidates and can send them into qualification, signal search, and scoring.

## Decision

Radar account candidates are legal entities. Application services must resolve
entity type before candidate-universe freeze and before signal search.

- `legal_entity` observations may become scored Radar candidates.
- `production_site`, `project`, and `asset` observations are linked facts when
  they can be attached to a resolved legal entity.
- unresolved non-account entities become review-needed candidate-universe gaps,
  not scored candidates.
- `unknown_entity` observations remain review-needed and must not be projected
  as high-confidence legal entities.

DaData and other company-registry providers support legal-entity identity and
enrichment. They do not replace web evidence for intent signals.

## Consequences

- Candidate counts may decrease because non-account entities are no longer
  counted as accounts.
- Dossier and diagnostics can explain why a project/site/asset was linked or
  rejected as an account.
- Future normalized candidate/evidence tables should preserve this distinction
  instead of flattening all entity mentions into account rows.
