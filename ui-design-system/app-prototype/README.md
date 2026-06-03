# App UI Kit — Power Web OS

A high-fidelity, click-through recreation of the Power Web OS web app. Cosmetic-fidelity React (Babel-in-browser) — not production code. Open `index.html`.

## Run
Open `index.html`. It loads `../colors_and_type.css` and the JSX files in order. Use the sidebar to move between the five screens. Design width ≈ 1320–1440px (the app has a 1180px min-width and scrolls below that).

## Screens
1. **Account Map** (`MapScreen.jsx` + `AccountMap.jsx`) — the centerpiece. The buying committee rendered as a relationship graph: stance-colored nodes, reports-to / works-with edges, a lit cobalt access route, ghosted unsurfaced figures, plus a right-hand inspector that explains board coverage, the recommended route, and any selected person's evidence. **Click a node** to inspect them; the inspector swaps between board-summary and person views.
2. **Accounts** (`AccountsScreen.jsx`) — portfolio of target accounts as a table or card grid, with board health, stage, missing figures, best route and owner. Table/grid toggle; filter chips.
3. **Access Plans** (`PlansScreen.jsx`) — the explainable top-3 routes. **Click a plan** to expand its route, why-this-route rationale, step timeline, opening hook, evidence and owner.
4. **Playbook** (`ExtraScreens.jsx`) — the configurable rules the system reasons with: roles to map, signals & weights (live toggles), allowed vs forbidden moves, channels.
5. **Signals** (`ExtraScreens.jsx`) — public & first-party signals feed, grouped by recency.

## Components (reusable)
- **Primitives** (`components.jsx`): `Button` (primary/default/ghost/quiet/danger), `IconButton`, `Chip`, `Badge`, `StanceDot`, `Avatar`, `Card`, `Field`, `HealthBar`, `Eyebrow`, `Divider`, `Mono`, plus the `STANCE` map.
- **Icons** (`icons.jsx`): `Icon`, `Logo`, `Wordmark`, `PW_ICONS` dictionary.
- **Shell** (`AppShell.jsx`): `Sidebar`, `NavItem`, `TopBar`.
- **Map** (`AccountMap.jsx`): `AccountMap`, `MapNode`, `ROUTE_PATHS`.
- **Screen parts**: `AccountContext`, `BoardInspector`, `PersonInspector`, `RoutePath`, `PlanCard`, `AccountsTable`, `AccountsGrid`, `PlaybookScreen`, `SignalsScreen`, `Toggle`.

All demo content lives in `data.jsx` (fictional account: **Northwind Robotics**).

## Notes
- Each `<script type="text/babel">` has its own scope; shared components are exported via `Object.assign(window, …)` at the end of each file.
- Icons are inlined Lucide geometry for crisp synchronous rendering. In production use the real `lucide` package.
