from pathlib import Path
import subprocess


def test_github_wiki_publish_script_contract() -> None:
    script = Path("scripts/publish_github_wiki.py").read_text(encoding="utf-8")
    readme = Path("docs/qa/README.md").read_text(encoding="utf-8")
    user_guide = Path("docs/user/USER_GUIDE.md").read_text(encoding="utf-8")

    assert "mudrezzz/power-web-os" in script
    assert ".wiki.git" in script
    assert "Home.md" in script
    assert "_Sidebar.md" in script
    assert "QA-Visual-Smoke.md" in script
    assert "assets/screenshots/visual-smoke" in script
    assert "docs/qa/screenshots/visual-smoke" in script
    assert "scripts/publish_github_wiki.py --dry-run" in readme

    assert "SCREENSHOT_WALKTHROUGH" in script
    assert "ScreenshotWalkthroughItem" in script
    assert "ICP Radar shortlist" in script
    assert "Accounts portfolio" in script
    assert "Power Web board" in script
    assert "Access Plan" in script
    assert "Playbook analysis" in script
    assert "path.stem" not in script

    assert "![ICP Radar shortlist](../qa/screenshots/visual-smoke/icp-radar-1366x768.png)" in user_guide
    assert "![Accounts portfolio](../qa/screenshots/visual-smoke/accounts-1366x768.png)" in user_guide
    assert "![Power Web board](../qa/screenshots/visual-smoke/account-map-1366x768.png)" in user_guide
    assert "![Access Plan](../qa/screenshots/visual-smoke/access-plans-1366x768.png)" in user_guide
    assert "![Playbook analysis](../qa/screenshots/visual-smoke/playbook-1366x768.png)" in user_guide


def test_github_wiki_dry_run_has_curated_pages(tmp_path: Path) -> None:
    output = tmp_path / "wiki"
    subprocess.run(
        ["python", "scripts/publish_github_wiki.py", "--dry-run", "--output", str(output)],
        check=True,
    )

    home = (output / "Home.md").read_text(encoding="utf-8")
    sidebar = (output / "_Sidebar.md").read_text(encoding="utf-8")
    user_guide = (output / "User-Guide.md").read_text(encoding="utf-8")
    qa = (output / "QA-Visual-Smoke.md").read_text(encoding="utf-8")

    assert "Current PoC Flow" in home
    assert "## Product" in sidebar
    assert "## Engineering" in sidebar

    assert "![ICP Radar shortlist](assets/screenshots/visual-smoke/icp-radar-1366x768.png)" in user_guide
    assert "![Accounts portfolio](assets/screenshots/visual-smoke/accounts-1366x768.png)" in user_guide
    assert "![Power Web board](assets/screenshots/visual-smoke/account-map-1366x768.png)" in user_guide
    assert "![Access Plan](assets/screenshots/visual-smoke/access-plans-1366x768.png)" in user_guide
    assert "![Playbook analysis](assets/screenshots/visual-smoke/playbook-1366x768.png)" in user_guide

    assert "## ICP Radar shortlist" in qa
    assert "## Accounts portfolio" in qa
    assert "## Power Web board" in qa
    assert "## Access Plan" in qa
    assert "## Playbook analysis" in qa
    assert "## icp-radar-1366x768" not in qa
    assert "## account-map-1366x768" not in qa
