# ADR: Bilingual And Responsive Frontend Baseline

## Status

Accepted

## Context

Power Web OS is used in Russian and English contexts. The demo includes Russian-language account data and UI modes. Sales users also work from small laptops and phones, so new screens cannot assume a large desktop canvas.

Earlier screens exposed untranslated English labels in RU mode and relied on desktop-width tables without a clear mobile degradation path.

## Decision

Power Web OS frontend must treat bilingual UI and responsive behavior as baseline requirements.

- Supported UI locales are `en` and `ru`.
- New visible UI strings must go through frontend i18n resources and keep EN/RU synchronized.
- Raw artifact IDs, URLs, source refs, company names, person names, and technical runtime names may remain data unless a slice says otherwise.
- Longer Russian strings must be handled by layout rules, not by viewport-scaled typography or overlapping text.
- Use `ui-design-system/` tokens and prototype behavior as the UI source of truth.
- Do not hardcode colors, radii, shadows, spacing, or typography when a design-system token exists.
- Validate small desktop viewports such as `1280x720` and `1366x768` for every shell or screen change.
- Mobile behavior is a product requirement. Until the dedicated mobile baseline slice is implemented, every new screen must at least define how it degrades on phone-sized viewports and must not introduce page-level horizontal scroll as the only way to use the screen.

## Consequences

- New frontend slices need i18n keys and RU string checks as part of implementation.
- Dense data screens may require mobile-specific layouts such as cards, stacked rows, or focused detail flows.
- Visual smoke should continue to include small desktop screenshots, and future mobile smoke should be added once the mobile baseline slice is implemented.

## Alternatives considered

- **Desktop-only UI until later.** Rejected because sales users often work from small laptops and phones.
- **Translate only navigation labels.** Rejected because mixed-language UI is confusing and undermines demo credibility.
- **Shrink text by viewport width.** Rejected because it hurts readability and does not solve dense layout structure.
