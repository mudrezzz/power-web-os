# ADR: Bounded SPA Workspace Shell

## Status

Accepted

## Context

Power Web OS is an operational workspace for sales and ABM users. It must keep navigation, account context, and profile controls available while the user reviews candidates, accounts, maps, plans, playbooks, or queues.

Earlier UI iterations allowed browser-level page scrolling and pushed profile/context blocks out of the viewport on small desktop screens. That made the product behave like a landing page instead of a workspace.

## Decision

Power Web OS product screens must run inside a bounded SPA shell.

- `html`, `body`, `#root`, and `.app-shell` must be viewport-bounded.
- The browser page must not be the normal scroll container for product screens.
- Sidebar, navigation, topbar, and profile context must remain visible inside the workspace.
- Workspace panes own vertical scrolling.
- Product work happens inside the Power Web OS shell; do not add standalone full-screen feature pages when the shell exists.
- A screen may have internal scroll areas only when they are explicit, bounded, necessary, and do not create competing nested scrolls.

## Consequences

- Screen components must be designed around explicit height and `min-height: 0` constraints.
- Layout bugs must be fixed at the shell or pane level instead of relying on body scroll.
- Visual smoke should validate small desktop viewports such as `1280x720` and `1366x768` after shell or screen changes.

## Alternatives considered

- **Document-style page scrolling.** Rejected because users lose navigation and object context while doing operational work.
- **Per-screen custom full-page layouts.** Rejected because it fragments product navigation and breaks the intended workspace model.
