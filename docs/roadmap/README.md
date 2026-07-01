# Roadmap Tracker

`ROADMAP.md` is the human-readable project report. After slice `0.7.6.4.0.1`,
the normal editing source is the local SQLite slice tracker plus a deterministic
JSONL export.

## Files

| File | Role |
|---|---|
| `docs/roadmap/roadmap.sqlite` | Local working database for slices, events, links, and roadmap metadata. |
| `docs/roadmap/slices.export.jsonl` | Git-reviewable text export. Review this instead of relying on binary SQLite diffs. |
| `ROADMAP.md` | Generated human-readable report. |

## Commands

Initialize or refresh the tracker from the current roadmap:

```bash
python -m power_web_os.roadmap init
python -m power_web_os.roadmap import-current --from ROADMAP.md
```

Inspect slices:

```bash
python -m power_web_os.roadmap list --status Ready
python -m power_web_os.roadmap list --track radar
python -m power_web_os.roadmap show 0.7.6.4.1
```

Edit slice state:

```bash
python -m power_web_os.roadmap add-slice --id 0.7.6.4.7 --title "Next slice" --status Backlog --track radar
python -m power_web_os.roadmap update-status 0.7.6.4.1 Done --note "validated"
python -m power_web_os.roadmap link 0.7.6.4.1 --type doc --target docs/radar/pipelines/README.md
```

Regenerate review artifacts:

```bash
python -m power_web_os.roadmap export
python -m power_web_os.roadmap render --output ROADMAP.md
python -m power_web_os.roadmap check
```

## Rules

- Use the tracker first for planned slice changes.
- Regenerate both `slices.export.jsonl` and `ROADMAP.md` before committing.
- `ROADMAP.md` can still be read directly by users and contributors.
- Manual edits to generated slice sections should be temporary and followed by
  tracker import/render.
- The first tracker migration manages the active/future slice range and
  preserves older roadmap history as legacy report text.
