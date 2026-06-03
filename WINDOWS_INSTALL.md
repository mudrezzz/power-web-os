# Windows Install Notes

## Local Setup

From the repository root:

```powershell
python -m pip install -e ".[dev]"
python -m pytest
python demo\run_demo.py
```

Install the LangGraph document AI framework when working on workflow slices:

```powershell
python -m pip install -e ".[agent,dev]"
```

## Useful Checks

```powershell
Get-ChildItem -Force
git status --short --branch
```

## Notes

- `.external\` is for local research checkouts and is ignored by Git.
- Product requirements are in `power_web_os_concept.md` and the Power Web OS PDF.
- GitHub repositories for this project family are created under `mudrezzz`.
