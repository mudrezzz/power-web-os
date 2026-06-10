# QA Artifacts

This folder stores reproducible quality artifacts that help keep product documentation and visual behavior current.

## Visual Smoke Screenshots

Run:

```bash
python -m power_web_os.demo generate-icp-radar
python -m power_web_os.demo generate-account-radar
npm --prefix ./frontend run visual:smoke
```

The command starts a local Vite server through the Vite Node API, opens Chromium through Playwright, captures screenshots, and shuts the server down.

Screenshots are written to:

```text
docs/qa/screenshots/visual-smoke/
```

Covered screens:

- `ICP Radar`
- `Accounts`
- `Account Map`
- `Access Plans`
- `Playbook`

Covered desktop viewports:

- `1280x720`
- `1366x768`

These screenshots are not pixel-perfect regression baselines yet. They are visual smoke evidence for documentation, layout review, and small-monitor checks.

## GitHub Wiki Publishing

The repository includes a wiki publisher script:

```bash
python scripts/publish_github_wiki.py --dry-run
python scripts/publish_github_wiki.py
```

`--dry-run` builds the wiki package locally at `.wiki-build/` without pushing.

The publishing command:

- enables the GitHub Wiki for `mudrezzz/power-web-os`;
- builds `Home.md`, `_Sidebar.md`, documentation pages, and screenshot assets;
- pushes them to `https://github.com/mudrezzz/power-web-os.wiki.git`.

If GitHub returns `Repository not found` for the wiki remote after Wiki is enabled, create the first wiki page once in the GitHub web UI, then rerun the publishing command. GitHub creates the wiki git repository only after that first page exists.
