---
name: power-web-os-deep-onboarding
description: Use at the start of a new Power Web OS / ABM chat, after context loss, before taking a new roadmap slice, or when the user asks for "погружение", "онбординг", "где что лежит", "что сейчас делаем", "введи в проект", or a quick but deep project orientation. Rebuilds current product, architecture, roadmap/tracker, validation, and working-principle context from repository files before continuing.
---

# Power Web OS Deep Onboarding

## Goal

Reconstruct enough current project context that a new chat can work safely
without asking the user to repeat the product, architecture, roadmap, and
validation history.

Answer in Russian by default unless the user asks otherwise.

## First Principle

Do not answer from memory alone. Use memory only as a routing hint, then verify
current facts in the repository. `ROADMAP.md` is a generated report; the roadmap
SQLite tracker and export are the source of truth when available.

## Quick Workflow

1. Check repository state:

   ```bash
   git status --short --branch
   ```

2. Read the mandatory local instructions:

   - `AGENTS.md`
   - `README.md`
   - `ROADMAP.md`

3. Query the roadmap tracker when it is available:

   ```bash
   python -m power_web_os.roadmap list --status "In Progress"
   python -m power_web_os.roadmap list --status Ready
   python -m power_web_os.roadmap check
   ```

   If tracker commands fail, say so and fall back to `ROADMAP.md`.

4. Read the architecture and working docs needed for the current area:

   - always:
     - `docs/architecture/SYSTEM_ARCHITECTURE_OVERVIEW.md`
     - `docs/developer/DEVELOPER_GUIDE.md`
     - latest relevant ADRs under `docs/adr/`
   - for Radar backend:
     - `docs/architecture/RADAR_BACKEND_ARCHITECTURE.md`
     - `docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md`
     - `src/power_web_os/application/radar/README.md`
     - `src/power_web_os/application/radar/candidate_discovery/execution/README.md`
   - for Radar pipeline behavior:
     - `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md`
     - `docs/radar/pipelines/README.md`
   - for signal monitoring:
     - `docs/radar/pipelines/signal-monitoring/to-be/`
     - `config/radar/model_profiles/`
     - `config/radar/runtime_defaults.json`
   - for frontend:
     - use `$frontend-design-system` and read `ui-design-system/START-HERE.md`.

5. Inspect the code and tests around the active slice only:

   - Use `rg --files` and `rg` to find relevant modules.
   - Prefer package READMEs and architecture tests before reading large modules.
   - For Radar backend, inspect `tests/test_backend_architecture_contract.py`
     and `tests/test_radar_backend_package_contract.py` before changing
     structure.

## What To Explain

Produce a compact orientation, not a formal report.

Start with one plain sentence:

> Мы делаем Power Web OS: систему над CRM, которая ищет целевые аккаунты,
> мониторит сигналы по ним и помогает строить доступ к сделкам.

Then cover:

- current product focus;
- current architecture in 5-7 bullets;
- where to look first for product, backend, Radar pipeline, frontend, demo,
  roadmap, and tests;
- current active slice and next ready slice;
- what changed recently if visible from git/tracker;
- validation commands relevant to the next task;
- principles that must not be violated;
- risks/blockers and the recommended next action.

## Output Shape

Use this structure unless the user asks for a different shape:

```markdown
**Суть проекта**
<one sentence>

**Где мы сейчас**
<short paragraph>

**Архитектура**
- ...

**Карта файлов**
- ...

**Roadmap**
- Active/In Progress:
- Next Ready:

**Как проверять**
- ...

**Правила работы**
- ...

**Следующий шаг**
<one clear recommendation>
```

Keep it readable. Do not dump every file in the repository.

## Project-Specific Guardrails

- Work through roadmap tracker commands, then render/export/check `ROADMAP.md`.
- Do not create new root-level `src/power_web_os/application/live_radar_*.py`
  modules.
- Radar candidate-discovery backend code belongs under
  `src/power_web_os/application/radar/candidate_discovery/...`.
- Candidate-discovery execution must follow service classes, context/state, and
  handbook docstrings from
  `docs/architecture/radar/CANDIDATE_DISCOVERY_EXECUTION_ARCHITECTURE.md`.
- Preserve compatibility shims while migration slices are active.
- Do not hide stateful logic inside large module-level helpers.
- Do not treat live provider runs as the first validation signal. Prefer
  architecture tests, recorded fixtures, focused unit/integration tests, then
  Docker/live smoke only when the slice requires it.
- Keep `.env` secrets out of docs, reports, tests, commits, and final answers.

## When The User Asks To Continue Work

After onboarding, continue only if the user's request implies action. If the
user only asked for orientation, stop after the summary. If the user asks to
implement the next slice, use the active slice skill flow after the onboarding
summary.

## Minimal Validation For This Skill

If the skill itself is changed, run:

```bash
python C:\Users\solovev.v\.codex\skills\.system\skill-creator\scripts\quick_validate.py .agents/skills/power-web-os-deep-onboarding
git diff --check
```
