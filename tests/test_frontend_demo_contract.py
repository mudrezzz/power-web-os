from pathlib import Path


def test_frontend_imports_design_system_tokens() -> None:
    entrypoint = Path("frontend/src/main.tsx").read_text(encoding="utf-8")

    assert "ui-design-system/colors_and_type.css" in entrypoint


def test_frontend_demo_contains_required_sections() -> None:
    app = Path("frontend/src/App.tsx").read_text(encoding="utf-8")

    for label in [
        "Account context",
        "Signal evidence",
        "Power Web Lite",
        "Unresolved gaps",
        "Access Plan",
        "Human review",
    ]:
        assert label in app


def test_frontend_public_artifact_is_available_for_vite() -> None:
    assert Path("frontend/public/demo/access_plan.json").exists()
