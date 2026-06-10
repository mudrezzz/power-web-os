import json
from pathlib import Path


def test_frontend_visual_smoke_script_is_documented_and_available() -> None:
    package = json.loads(Path("frontend/package.json").read_text(encoding="utf-8"))
    script = Path("frontend/scripts/visual-smoke.mjs").read_text(encoding="utf-8")
    qa_readme = Path("docs/qa/README.md").read_text(encoding="utf-8")

    assert package["scripts"]["visual:smoke"] == "node scripts/visual-smoke.mjs"
    assert "@playwright/test" in package["devDependencies"]
    assert "createServer" in script
    assert "chromium.launch" in script
    for path_part in ["docs", "qa", "screenshots", "visual-smoke"]:
        assert path_part in script
    assert "1280x720" in script
    assert "1366x768" in script
    assert "npm --prefix ./frontend run visual:smoke" in qa_readme
