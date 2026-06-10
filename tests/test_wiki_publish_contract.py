from pathlib import Path


def test_github_wiki_publish_script_contract() -> None:
    script = Path("scripts/publish_github_wiki.py").read_text(encoding="utf-8")
    readme = Path("docs/qa/README.md").read_text(encoding="utf-8")

    assert "mudrezzz/power-web-os" in script
    assert ".wiki.git" in script
    assert "Home.md" in script
    assert "_Sidebar.md" in script
    assert "QA-Visual-Smoke.md" in script
    assert "assets/screenshots/visual-smoke" in script
    assert "docs/qa/screenshots/visual-smoke" in script
    assert "scripts/publish_github_wiki.py --dry-run" in readme
