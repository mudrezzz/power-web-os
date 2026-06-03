# Design tokens — reference

Source of truth: **`../colors_and_type.css`** (CSS custom properties). This document is a human-readable index of every token. A framework-agnostic copy lives in **`tokens.json`**.

> Import the CSS once at the top of your app. Then reference everything as `var(--token-name)` — never hard-code a hex, radius, or shadow.

```css
@import url('./colors_and_type.css');   /* or bundle it via your build */
```

---

## Color — neutral ramp (warm paper → cool charcoal ink)

| Token | Value | Use |
|---|---|---|
| `--paper` | `#FBFBF9` | App canvas (warm paper) |
| `--surface` | `#FFFFFF` | Cards, panels |
| `--surface-2` | `#F5F5F2` | Inset wells, hover rows |
| `--surface-3` | `#EDEDE9` | Deeper inset, track |
| `--border-faint` | `#EEEEE9` | Hairline inside surfaces |
| `--border` | `#E3E3DD` | Default border |
| `--border-strong` | `#D2D2CA` | Emphasis / focus-adjacent |
| `--ink` | `#191B1E` | Primary text (near-black cool charcoal) |
| `--fg2` | `#565A60` | Secondary text |
| `--fg3` | `#888D94` | Muted / meta |
| `--fg4` | `#B2B6BC` | Faint / disabled |

## Color — cobalt (the signature; ration it)

Cobalt appears **only** on: the active access route, the single primary button per view, active nav, links, focus rings. If everything is cobalt, nothing is.

| Token | Value |
|---|---|
| `--cobalt-50` | `#EEF1FE` |
| `--cobalt-100` | `#DCE3FD` |
| `--cobalt-200` | `#BCC8FB` |
| `--cobalt` | `#2D52E0` *(base)* |
| `--cobalt-600` | `#2747C8` *(hover)* |
| `--cobalt-700` | `#1F3AA6` *(pressed / link text)* |

## Color — stance palette (semantic, not decorative)

Each maps directly to a person's posture in the deal. Use the `*-tint` for fills, the base for dots/strokes/text, the `*-200` for halos/rings.

| Stance | Base | Tint (fill) | Ring (`-200`) |
|---|---|---|---|
| Ally (champion / for) | `--ally` `#14935F` | `--ally-tint` `#E7F4EE` | `--ally-200` `#B7E0CC` |
| Blocker (risk / against) | `--blocker` `#DB4A45` | `--blocker-tint` `#FBEBEA` | `--blocker-200` `#F4C4C1` |
| Unsurfaced (unknown / watch) | `--unsurfaced` `#C2851A` | `--unsurfaced-tint` `#F8F0DD` | `--unsurfaced-200` `#ECD49B` |
| Neutral | `--fg3` `#888D94` | `--surface-2` | `--border-strong` |

## Color — semantic aliases (prefer these for UI intent)

| Token | Resolves to |
|---|---|
| `--accent` | `--cobalt` |
| `--accent-tint` | `--cobalt-50` |
| `--link` | `--cobalt-600` |
| `--success` | `--ally` |
| `--danger` | `--blocker` |
| `--warning` | `--unsurfaced` |
| `--focus-ring` | translucent cobalt (≈ `rgba(45,82,224,0.45)`) |

---

## Radii (slightly rounded — never strict squares, never a toy)

| Token | Value | Typical use |
|---|---|---|
| `--r-xs` | `6px` | Tiny chips, tags |
| `--r-sm` | `8px` | Small controls |
| `--r-md` | `10px` | **Buttons, inputs** |
| `--r-lg` | `14px` | **Cards** |
| `--r-xl` | `18px` | Large panels |
| `--r-2xl` | `24px` | Hero surfaces |
| `--r-pill` | `999px` | Chips, toggles, badges, route nodes |

## Shadows (soft, diffuse, low-opacity, cool-tinted)

| Token | Use |
|---|---|
| `--shadow-xs` | Resting micro-lift (default buttons) |
| `--shadow-sm` | Cards at rest |
| `--shadow-md` | Card hover, active plan card |
| `--shadow-lg` | Popovers, menus |
| `--shadow-focus` | 3px cobalt focus ring (`0 0 0 3px var(--focus-ring)`) |

## Spacing (4pt base — 16 and 24 are the workhorses)

| Token | px | | Token | px |
|---|---|---|---|---|
| `--s-1` | 4 | | `--s-8` | 32 |
| `--s-2` | 8 | | `--s-10` | 40 |
| `--s-3` | 12 | | `--s-12` | 48 |
| `--s-4` | 16 | | `--s-16` | 64 |
| `--s-5` | 20 | | `--s-20` | 80 |
| `--s-6` | 24 | | | |

## Motion (calm, no bounce)

| Token | Value |
|---|---|
| `--ease` | `cubic-bezier(0.22, 0.61, 0.36, 1)` |
| `--dur-fast` | `120ms` (hover, press) |
| `--dur` | `200ms` (default) |
| `--dur-slow` | `360ms` (panels, popovers) |

Press = 0.5px downward nudge, never a scale-pop. Respect `prefers-reduced-motion`.

---

## Typography

Two families only: **Hanken Grotesk** (`--font-sans`) for all UI, **IBM Plex Mono** (`--font-mono`) for anything numeric / machine-derived (scores, confidence, domains, IDs) and uppercase eyebrow labels. Mono signals "this came from the data."

Each scale step is a ready-made CSS `font` shorthand, e.g. `font: var(--h2);`. Apply tracking separately (the values are baked into the `.pw` element defaults — see below).

| Token | Weight / size / line-height | Tracking | Family |
|---|---|---|---|
| `--display` | 700 · 44px · 1.05 | -0.025em | sans |
| `--h1` | 650 · 32px · 1.12 | -0.018em | sans |
| `--h2` | 650 · 24px · 1.18 | -0.015em | sans |
| `--h3` | 600 · 19px · 1.25 | -0.01em | sans |
| `--h4` | 600 · 16px · 1.3 | -0.006em | sans |
| `--body-lg` | 400 · 17px · 1.55 | — | sans |
| `--body` | 400 · 15px · 1.55 | — | sans |
| `--body-sm` | 400 · 13.5px · 1.5 | — | sans |
| `--label` | 550 · 13px · 1.2 | — | sans |
| `--meta` | 500 · 12px · 1.3 | — | sans |
| `--mono` | 460 · 13px · 1.45 | — | mono |
| `--mono-sm` | 460 · 11.5px · 1.4 | — | mono |

**Eyebrow / column label** = `--mono-sm` + `letter-spacing: 0.14em` + `text-transform: uppercase` + `color: var(--fg3)`. Used for quiet structural signposting (`BOARD COVERAGE`, `WHY THIS ROUTE`). This is the **only** uppercase in the UI.

### The `.pw` helper

`colors_and_type.css` also ships an opt-in `.pw` class. Add `class="pw"` to a root element and it sets the body font/color/canvas and styles `h1`–`h4`, `.display`, `.mono`, `.meta`, `.eyebrow`, `a`, and `::selection` with the correct tracking applied. The raw `var(--*)` tokens work standalone without it — use whichever fits your stack.
