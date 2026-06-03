# Power Web OS — Design System

> An intelligence-grade design language for a B2B sales / ABM platform that maps the hidden web of influence inside a deal and proposes explainable routes to access it.

---

## 1 · Product context

**Power Web OS** is a white-box platform for B2B sales and ABM teams. It gathers public and first-party signals on target accounts, builds a dynamic map of the **buying committee** and the surrounding external ecosystem, and proposes explainable **Access Plans**: *through whom, by which route, with what reason, and what the next move is* to reach the account.

It is deliberately **not** a black box and **not** a contact database. The customer configures a **Sales Playbook** — roles, signals, allowed and forbidden moves, channels, assets, regions, competitors, and success criteria. On that basis the product scores the state of an account, surfaces the missing power figures, proposes the top-3 access routes, and creates tasks for sales, marketing, partner managers or RevOps.

**Core value:** *Power Web OS turns account intelligence into a managed access strategy.*

**One-line pitch:** Power Web OS helps B2B teams not just find target accounts but understand the deal's game board — who influences, who's hidden, who's for or against, which route to enter through, and what move to make next — with full transparency of the rules and the evidence.

### Positioning notes that shaped the design
- It is a **research instrument**. The interface must feel **airy, light, and made for professionals — not a toy.**
- Borrow from the clarity of CRM, but reject **strict consulting grey and strict squares.** Forms are modern and **slightly rounded.**

### Sources
No codebase, Figma, or decks were provided. This system was designed **from the brief above**. Every visual decision is an original proposal — treat it as **v1 to react to**, not a recreation of an existing product. If a Figma file, brand kit, or real screenshots exist, attach them and the system will be re-grounded against them.

---

## 2 · The system at a glance

The product's job — *reading who is for, against, or hidden, and routing through the board* — is the spine of the visual language:

| Idea in the product | Idea in the design |
|---|---|
| The buying committee is a board of people | A **relationship graph** of stance-colored **nodes** |
| Who is for / against / not yet known | A **stance palette**: ally green · blocker coral · unsurfaced amber · neutral grey |
| The recommended way in | A single **cobalt** signature lighting one **access route** |
| Explainable, white-box reasoning | Evidence, scores and confidence shown in **mono**, never hidden |
| Calm, professional research | Warm-paper canvas, generous space, soft diffuse shadows, no bounce |

---

## 3 · Content fundamentals

How Power Web OS writes.

- **Voice:** calm, precise, advisory. It sounds like a sharp chief-of-staff briefing you — confident, never hype. It states the move and the reason for it.
- **Person:** addresses the user as **you** ("your champion", "reach the economic buyer"). Refers to itself implicitly ("Recommended", "Suggested move") — rarely "we", never "I".
- **Casing:** **Sentence case** everywhere — buttons, headings, menus ("Draft next move", "Find them", "Clear the blocker first"). The only UPPERCASE is the mono **eyebrow / column label** (`BOARD COVERAGE`, `WHY THIS ROUTE`, `RANK · SCORE`), used as quiet structural signposting.
- **Domain vocabulary is load-bearing — use it precisely:** *buying committee · board · stance · ally · blocker · unsurfaced · power figure · access plan · route · hook · move · signal · playbook · evidence · confidence.* These are nouns the product owns; don't swap them for generic CRM words ("contact", "lead", "opportunity").
- **Numbers earn trust.** Scores (`82`), confidence (`0.86`), counts (`2 power figures unsurfaced`) are stated plainly and always paired with the evidence behind them. Never a number without a reason.
- **Imperatives for actions, short clauses for rationale.** "Ask Marcus for a 3-way intro." / "Marcus is engaged and reports into Priya, who owns the budget line."
- **Tone on risk is matter-of-fact, not alarmist.** A blocker is "a risk to clear," not a crisis.
- **Emoji:** none. **Exclamation marks:** effectively none. Punctuation is quiet; the middle dot ` · ` separates metadata.

Example copy lifted from the kit:
> **Warm intro through your champion** — Marcus is engaged and reports into Priya, who owns the budget line that rolls up to Diane. Shortest trusted path to the unsurfaced economic buyer.
> *Opening hook:* Q3 automation efficiency benchmark Northwind cited in earnings.
> *Next:* Ask Marcus for a 3-way intro to Priya.

---

## 4 · Visual foundations

**Overall vibe.** Airy, white-box, intelligence-grade. Lots of breathing room on a warm-paper canvas; one decisive accent; meaning carried by color, not decoration. Closer to a refined research console than a dense CRM grid.

**Color.**
- **Canvas is warm paper** (`#FBFBF9`), surfaces pure white. The neutral ramp runs warm-paper → **cool charcoal ink** (`#191B1E`) — deliberately *not* flat consulting grey.
- **One signature: cobalt** (`#2D52E0`). It is rationed — it appears on the active access route, the single primary button per view, active nav, links and focus rings. If everything were cobalt, nothing would be.
- **Stance palette is semantic, not decorative:** ally `#14935F`, blocker `#DB4A45`, unsurfaced `#C2851A`, neutral `#888D94`, each with a soft tint for fills and a mid ring for halos. These map directly to a person's posture in the deal.
- Color is used at **low saturation in fills** (tints) and **full strength in 1–2px accents** (rings, dots, route lines).

**Type.**
- **Hanken Grotesk** for everything in the UI — a humanist, *gently rounded* grotesque that reads as modern and professional without being cold. Display/headings use weights 600–700 with tight negative tracking (`-0.018 to -0.025em`); body is 15px / 1.55 for an airy read.
- **IBM Plex Mono** for anything numeric or machine-derived: scores, confidence, domains, IDs, and the uppercase eyebrow labels. Mono = "this came from the data."

**Spacing & layout.** 4pt base scale; 16 and 24 are the workhorses. Generous padding, clear column rhythm. Layout is a calm three-zone shell: a quiet 232px **sidebar**, a sticky translucent **top bar** carrying account context, and a **content area** that on the map splits into board + a 344px inspector. Fixed elements (sidebar, top bar, inspector, map legend/toolbar) frame a scrollable middle.

**Backgrounds & texture.** No photography, no gradients-as-decoration, no illustration. The one texture is a faint **dotted research grid** behind the account map (radial dots, 22px, ~0.6 opacity) — it signals "canvas / workspace" and nothing else. Unsurfaced people get a subtle **diagonal hatch** fill to read as "not yet known."

**Corner radii.** Slightly rounded throughout — 6/8/10/14/18px plus full pills. Cards 14px, inputs/buttons 10px, chips & toggles & route nodes are pills. Never strict squares; never cartoonishly round.

**Cards.** White surface, 1px `--border`, 14px radius, soft `--shadow-sm` at rest lifting to `--shadow-md` on hover. No colored left-border accents, no heavy outlines. Content-first, quiet chrome.

**Shadows / elevation.** Soft, diffuse, low-opacity, cool-tinted (`rgba(25,27,30,…)`). Four steps: xs/sm sit on the canvas, md/lg lift popovers, menus and the active plan card. Elevation is felt, not seen.

**Borders.** Hairline neutrals (`--border-faint` inside surfaces, `--border` default, `--border-strong` for emphasis). Dividers are 1px neutral. Dashed strokes mean "soft / inferred" (works-with relationships, ghost nodes).

**Motion.** Calm and quick — `cubic-bezier(0.22,0.61,0.36,1)`, 120–360ms. Fades and small position shifts; **no bounce, no spring.** The single ambient animation is a slow dot travelling the lit access route (2.4s loop) to imply flow. Respect reduced-motion.

**Hover / press.**
- *Hover:* surfaces lighten to `--surface-2`; cobalt elements deepen to `--cobalt-600`; cards raise shadow + darken border.
- *Press:* a 0.5px downward nudge. No scale-pop.
- *Active/selected:* cobalt-50 fill, cobalt-200 border, a 3px left bar on nav, a ring on nodes.

**Focus.** 3px translucent cobalt ring (`--focus-ring`) — visible, calm, on-brand.

**Transparency & blur.** Used once, with intent: the sticky top bar is `rgba(251,251,249,0.82)` + 8px backdrop-blur so content scrolls softly beneath it. Elsewhere the UI is opaque — clarity over glassiness.

**Imagery vibe.** People are **monogram avatars** (muted desaturated palette) or dashed ghosts when unsurfaced — never stock headshots. Company marks are quiet monogram tiles. The aesthetic is cool-neutral, evidence-first, calm.

---

## 5 · Iconography

- **Library:** [Lucide](https://lucide.dev) geometry — clean, **slightly rounded stroke** icons that match Hanken's humanist roundness. In the kit they are inlined as SVG path data (see `ui_kits/app/icons.jsx`) so they render crisply and synchronously; in production, install `lucide` / `lucide-react` and keep stroke-width **1.9–2.0** at 16–18px.
- **Style rules:** stroke (never filled), round caps & joins, two-tone only via the stance/tint system (e.g. a cobalt glyph on a cobalt-50 tile). Icon tiles are 26–40px rounded squares.
- **Custom marks:** only the **brand logomark** (`assets/logo.svg`) — a node-graph with one lit cobalt route, the product metaphor in miniature. Don't hand-draw other illustrations.
- **Emoji:** never. **Unicode:** only the middle dot ` · ` as a metadata separator and `›`/arrows where an icon is overkill.
- Representative set in use: `share` `route` `target` `activity` `settings-2` `users` `shield` `sparkles` `lightbulb` `alert-triangle` `circle-check` `eye-off` `trending-up` `briefcase` `git-branch` `compass`.

---

## 6 · Index / manifest

**Root**
- `README.md` — this file.
- `colors_and_type.css` — all design tokens: color ramp, stance palette, semantic aliases, type scale, radii, shadows, spacing, motion. Import this first in any build.
- `SKILL.md` — Agent-Skill front-matter so this system is usable inside Claude Code.
- `assets/logo.svg` — brand logomark.

**`preview/`** — Design-System-tab cards (one concept each, also a quick visual reference): `colors-neutrals` · `colors-cobalt` · `colors-stance` · `type-display` · `type-body` · `type-mono` · `radii` · `shadows` · `spacing-tokens` · `buttons` · `chips-badges` · `inputs` · `cards` · `map-node` · `route-path` · `logo`. Shared styling in `preview/preview.css`.

**`ui_kits/app/`** — the Power Web OS web app, a high-fidelity click-through recreation.
- `index.html` — run this. Switches between five screens.
- `icons.jsx` · `components.jsx` · `data.jsx` — icons/logo, shared primitives, demo data.
- `AppShell.jsx` — sidebar + top bar. `AccountMap.jsx` — the buying-committee graph. `MapScreen.jsx` — board + inspector. `AccountsScreen.jsx` — portfolio. `PlansScreen.jsx` — explainable Access Plans. `ExtraScreens.jsx` — Playbook config + Signals feed.
- See `ui_kits/app/README.md` for the component list.

---

*v1 — designed from the written brief. Fonts are Google Fonts stand-ins (see caveats). Ready to be re-grounded against real brand assets.*
