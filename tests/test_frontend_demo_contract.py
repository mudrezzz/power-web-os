from pathlib import Path


def test_frontend_imports_design_system_tokens() -> None:
    entrypoint = Path("frontend/src/main.tsx").read_text(encoding="utf-8")

    assert "ui-design-system/colors_and_type.css" in entrypoint


def test_frontend_demo_contains_required_sections() -> None:
    shell = Path("frontend/src/layout/AppShell.tsx").read_text(encoding="utf-8")
    accounts_screen = Path("frontend/src/screens/AccountsScreen.tsx").read_text(encoding="utf-8")
    access_plans_screen = Path("frontend/src/screens/AccessPlansScreen.tsx").read_text(encoding="utf-8")
    planned_screen = Path("frontend/src/screens/PlannedScreen.tsx").read_text(encoding="utf-8")

    for label in [
        "Accounts",
        "Account Map",
        "Access Plans",
        "Signals",
        "Playbook",
        "My Tasks",
        "Signals Inbox",
    ]:
        assert label in shell

    for label in [
        "Account Radar",
        "Radar score",
        "Signals",
        "Missing",
        "Best route",
        "Owner",
        "Review",
    ]:
        assert label in accounts_screen

    for label in [
        "Objective",
        "Board coverage",
        "Signal evidence",
        "Review status",
    ]:
        assert label in access_plans_screen

    assert "PLANNED WORKSPACE" in planned_screen
    assert "PLANNED QUEUE" in planned_screen
    assert "Accounts portfolio" not in planned_screen


def test_frontend_shell_uses_design_system_prototype_structure() -> None:
    shell = Path("frontend/src/layout/AppShell.tsx").read_text(encoding="utf-8")
    app = Path("frontend/src/App.tsx").read_text(encoding="utf-8")

    assert "AppShell" in app
    assert "Sidebar" in shell
    assert "TopBar" in shell
    assert "Access Plans /" in shell


def test_app_loads_account_radar_and_selected_access_plan_artifacts() -> None:
    app = Path("frontend/src/App.tsx").read_text(encoding="utf-8")

    assert "/demo/account_radar.json" in app
    assert "access_plan_path" in app


def test_frontend_public_artifact_is_available_for_vite() -> None:
    radar_path = Path("frontend/public/demo/account_radar.json")

    assert radar_path.exists()
    assert Path("frontend/public/demo/access_plans").exists()
