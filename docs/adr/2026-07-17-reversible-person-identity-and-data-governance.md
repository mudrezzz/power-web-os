# ADR: Reversible person identity and people-data governance

## Status

Accepted

## Context

Public people data is incomplete, duplicated and sometimes anonymous. Unsafe
automatic merging can create false identities, while broad storage or facial
matching creates privacy and governance risk.

## Decision

Retain source-native profiles and broad identity hypotheses, but require two
independent compatible dimensions and no hard contradiction for a confirmed
same-person decision. Every merge is reversible and preserves its source
profiles.

Exact and perceptual duplicate-image fingerprints may be supporting,
non-biometric evidence. Cross-photo facial similarity, embeddings and reverse
face search are prohibited until a separate governance slice is explicitly
approved.

Artifacts store public product-safe excerpts, URLs, dates, source metadata and
allowed fingerprints only. They exclude raw HTML, provider payloads, binary
images, private contacts and automated outreach instructions. Authorization,
CAPTCHA, robots and source restrictions must not be bypassed.

## Consequences

- Ambiguity remains visible instead of being silently resolved.
- False confirmed merges are a hard benchmark failure.
- Review and unmerge history must be auditable in later runtime slices.
- Some people remain anonymous or unresolved, which is an accepted outcome.

## Alternatives considered

- Name/employer/title matching as confirmation: rejected as too weak.
- Face embeddings as an early resolver: rejected pending explicit legal,
  privacy and product approval.
