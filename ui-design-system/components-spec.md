# Components — spec & API

Reference implementations live in **`../app-prototype/components.jsx`** and **`../app-prototype/icons.jsx`** (React, inline styles). They are written as cosmetic-fidelity reference, not a published package — read them to see exact paddings, hover/press logic, and token usage, then re-implement in your real stack (React + CSS modules, Tailwind, Vue, web components — whatever the project uses). Every value resolves to a design token; nothing is hard-coded.

Open **`../app-prototype/index.html`** in a browser to see all of these assembled into the five real app screens.

---

## Interaction rules (apply to every interactive element)

- **Hover:** surfaces lighten to `--surface-2`; cobalt elements deepen to `--cobalt-600`; cards raise shadow (`sm`→`md`) and darken border to `--border-strong`.
- **Press:** a 0.5px downward nudge (`translateY(0.5px)`). No scale-pop, no bounce.
- **Active / selected:** `--cobalt-50` fill, `--cobalt-200` border; a 3px left bar on nav items; a ring on map nodes.
- **Focus:** 3px translucent cobalt ring — `box-shadow: var(--shadow-focus)`. Always visible, never removed.
- **Transitions:** `--dur-fast` for hover/press, `--dur` default, eased with `--ease`.

---

## Button

`variant` × `size`. Only **one** `primary` (filled cobalt) button per view.

| Prop | Values | Default |
|---|---|---|
| `variant` | `primary` · `default` · `ghost` · `quiet` · `danger` | `default` |
| `size` | `sm` (h30) · `md` (h36) · `lg` (h44) | `md` |
| `icon` / `iconRight` | icon name (see icon set) | — |
| `disabled` | boolean | `false` |

Variant anatomy:
- **primary** — bg `--cobalt` → hover `--cobalt-600`, white text, subtle blue shadow. The single decisive action.
- **default** — white surface, `--border`, `--shadow-xs`; hover bg `--surface-2`.
- **ghost** — transparent, `--fg2` text; hover bg `--surface-2`. Low-emphasis.
- **quiet** — transparent, `--cobalt-600` text; hover bg `--cobalt-50`. Inline/link-like action.
- **danger** — `--blocker-tint` bg + `--blocker` text; hover flips to solid `--blocker` + white. For destructive / "clear blocker".

Shared: radius `--r-md`, font `560 weight`, letter-spacing `-0.005em`, `nowrap`.

## IconButton

Square icon-only control (default 36px, radius `--r-md`). States: rest transparent; hover bg `--surface-2` + `--border`; `active` → `--cobalt-50` bg, `--cobalt-200` border, `--cobalt-600` glyph. Use for toolbar actions, table/grid toggles, close.

## Chip

Selectable pill (h30, radius `--r-pill`, `530` weight). Props: `active`, `icon`, `tone` (`neutral` | `cobalt`). Selected = `--cobalt-50` / `--cobalt-200` / `--cobalt-700`. Use for filters and quick toggles.

## WorkspaceTabs

Underline navigation for real sections of one workspace. The component owns
`tablist`, `tab` and `tabpanel` relationships, roving focus, Arrow Left/Right,
Home and End navigation, and horizontal overflow on narrow screens. The active
tab uses a cobalt underline; inactive tabs have no pill background or rounded
container.

Use `WorkspaceTabs` for page sections such as Radar candidates/runs/settings,
candidate detail, run diagnostics, Access Plans and product configuration. Do
not use pill chips for section navigation. Keep `Chip` and segmented controls
for filters, display modes and bounded option switches.

## Badge

Static pill label (h22, radius `--r-pill`, `600`/11.5px). Props: `tone` (`ally` · `blocker` · `unsurfaced` · `cobalt` · `neutral`), `icon`, `solid`. Tinted by default (tint bg + colored text); `solid` fills with the tone color + white text. Use for stance, stage, counts.

## StanceDot

Small dot (default 9px) colored by `stance` (`ally` · `blocker` · `unsurfaced` · `neutral`). Optional `ring` adds a 3px tint halo. The atomic stance indicator — use in lists, legends, next to names.

## Avatar

Monogram circle (default 34px). Derives initials from `name` and picks a stable muted color from a 6-tone desaturated palette. Optional `stance` adds a colored 2-ring halo; optional `src` shows an image. **No stock headshots** — monograms or dashed ghosts (for unsurfaced) only.

## Card

White surface, `--border`, radius `--r-lg`, `--shadow-sm` at rest. Pass `hover` to lift to `--shadow-md` + `--border-strong`; pass `onClick` to make it interactive. `pad` defaults to `--s-5` (20px). No colored left-border accents, no heavy outlines — quiet chrome, content first.

## Field

Text input row (h38, or h32 at `size="sm"`, radius `--r-md`). Optional leading `icon`. Focus → border `--cobalt` + `--shadow-focus` ring. Plain, calm, hairline border at rest.

## HealthBar

Track + fill meter (`value` 0–100, `width` default 64). Fill color is automatic: ≥70 `--ally`, ≥40 `--unsurfaced`, else `--blocker`. Trailing mono number. Use for board coverage / account health.

## Small primitives

- **Eyebrow** — uppercase mono-sm label, `0.14em` tracking, `--fg3`. Structural signpost.
- **Divider** — 1px `--border` line.
- **Mono** — wraps text in `--mono` (use for scores, confidence, domains, IDs).

`STANCE` is an exported map (`ally` / `blocker` / `unsurfaced` / `neutral` → `{ label, color, tint, ring }`) — the single source for stance styling. Re-create it as a constant in your codebase rather than scattering stance colors.

---

## Icons & brand

- **Library:** [Lucide](https://lucide.dev). In the reference kit icons are inlined as SVG path data in `icons.jsx` (`PW_ICONS` dictionary + `<Icon name size strokeWidth color />`). **In production, install `lucide` / `lucide-react`** rather than copying path data.
- **Style:** stroke only (never filled), round caps & joins, **stroke-width 1.9–2.0**, sizes 16–18px. Icon tiles are 26–40px rounded squares; two-tone only via the stance/tint system (e.g. cobalt glyph on a `--cobalt-50` tile).
- **Brand:** `Logo` (node-graph with one lit cobalt route — the product metaphor) and `Wordmark` (Logo + "Power Web OS"). The vector mark is also at **`../assets/logo.svg`**. Don't hand-draw other illustrations.
- **Emoji:** never. Unicode allowed: the middle dot ` · ` as a metadata separator, and `›` / arrows where an icon is overkill.

Icons used across the app: `share` · `route` · `target` · `activity` · `settings-2` · `users` · `shield` · `sparkles` · `lightbulb` · `alert-triangle` · `circle-check` · `eye-off` · `trending-up` · `briefcase` · `git-branch` · `compass` (full list in `PW_ICONS`).
