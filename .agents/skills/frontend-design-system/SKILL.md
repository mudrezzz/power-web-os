---
name: frontend-design-system
description: Use for any Power Web OS frontend work: building or modifying screens, components, layout, styling, UI copy, visual QA, responsive behavior, or frontend design review. Always use the local design system in ui-design-system/, starting from START-HERE.md, and enforce its tokens, components, visual rules, prototype references, and checklist.
---

# Frontend Design System

## Mandatory Workflow

1. Read `ui-design-system/START-HERE.md` first.
2. For implementation details, read only the needed files:
   - tokens: `ui-design-system/colors_and_type.css`
   - token tables: `ui-design-system/tokens/tokens-reference.md`
   - components: `ui-design-system/components-spec.md`
   - product tone and visual rationale: `ui-design-system/design-system-readme.md`
   - behavior/layout references: `ui-design-system/app-prototype/README.md`
3. Inspect relevant prototype files before recreating a screen or component.
4. Implement in the project frontend stack, while preserving design-system semantics.
5. Before finishing, apply the checklist in `ui-design-system/START-HERE.md`.

## Non-Negotiable Rules

- Import or include `ui-design-system/colors_and_type.css` before app styles.
- Do not hardcode hex colors, shadows, radii, spacing, or font styles when tokens exist.
- Use CSS variables from the design system.
- Keep cobalt rare: active route, one primary button per screen, active nav, links, and focus ring.
- Use stance colors only for stakeholder posture: ally, blocker, unsurfaced, neutral.
- Use sentence case in UI text. Use uppercase only for mono eyebrow labels.
- Use mono typography for scores, confidence, IDs, domains, and machine-like values.
- Give every score or confidence value a nearby explanation.
- Do not use emoji or exclamation marks in UI copy.
- Use Lucide icons in production.
- Respect `prefers-reduced-motion`.
- Do not introduce decorative gradients, photos, or illustrations unless the design system is updated to allow them.

## Component Reference Order

When building a UI element:

1. Check `ui-design-system/components-spec.md`.
2. Check `ui-design-system/app-prototype/components.jsx`.
3. Check the relevant screen prototype.
4. Implement in production style using tokens, not copied inline prototype styles.

## Visual Validation

For screens and visible component work:

1. Compare with `ui-design-system/preview/index.html`.
2. Compare screen behavior with `ui-design-system/app-prototype/index.html`.
3. Check focus states, hover/press behavior, reduced motion, and text overflow.
4. Report any known deviation from the design system before finishing.

## Final Response Requirements

Report:

- which design-system files were consulted;
- whether hardcoded visual values were avoided;
- whether the `START-HERE.md` checklist was applied;
- any known deviations from the design system.
