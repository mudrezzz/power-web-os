from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_remote_dev_config_is_present_and_contains_no_secrets() -> None:
    config = read("deploy/remote-dev.env")

    for expected in [
        "POWER_WEB_OS_REMOTE_HOST=213.148.13.45",
        "POWER_WEB_OS_REMOTE_SSH_TARGET=flowise",
        "POWER_WEB_OS_REMOTE_PATH=/opt/power-web-os",
        "POWER_WEB_OS_REMOTE_API_URL=http://213.148.13.45:8001",
        "POWER_WEB_OS_REMOTE_FRONTEND_URL=http://213.148.13.45:5173",
        "POWER_WEB_OS_REMOTE_REDIS_BIND=127.0.0.1:6380",
    ]:
        assert expected in config

    forbidden_markers = ["OPENROUTER_API_KEY", "sk-or-", "token", "password", "secret"]
    assert not any(marker.lower() in config.lower() for marker in forbidden_markers)


def test_remote_deploy_script_has_dry_run_and_secret_safe_contract() -> None:
    script = read("scripts/deploy_remote_dev.ps1")

    assert "[switch]$DryRun" in script
    assert "Missing local .env" in script
    assert "--exclude=.env" in script
    assert "chmod 600" in script
    assert "docker compose config --quiet" in script
    assert "docker compose up --build -d" in script
    assert "/health" in script
    assert "/api/radars" in script
    assert "contents redacted" in script
    assert "Get-Content -Path $LocalEnvPath" not in script
    assert "OPENROUTER_API_KEY" not in script
    assert "sk-or-" not in script


def test_deploy_remote_dev_skill_is_discoverable_and_guarded() -> None:
    skill = read(".agents/skills/deploy-remote-dev/SKILL.md")
    agents = read("AGENTS.md")

    assert skill.startswith("---\nname: deploy-remote-dev\n")
    assert "залить на сервер" in skill
    assert "deploy remote dev" in skill
    assert "deploy/remote-dev.env" in skill
    assert "Never print local `.env`" in skill
    assert "git status --short --branch" in skill
    assert "scripts/deploy_remote_dev.ps1" in skill
    assert "$deploy-remote-dev" in agents


def test_remote_dev_documentation_links_deploy_script_and_checks() -> None:
    docs = read("docs/deployment/REMOTE_DEV_SERVER.md")
    developer_guide = read("docs/developer/DEVELOPER_GUIDE.md")

    for expected in [
        "scripts/deploy_remote_dev.ps1",
        "deploy/remote-dev.env",
        "http://213.148.13.45:5173",
        "http://213.148.13.45:8001/health",
        "docker compose logs --tail=100 worker",
        "Redis is development infrastructure",
    ]:
        assert expected in docs

    assert "Remote Dev Server" in developer_guide
    assert "scripts/deploy_remote_dev.ps1" in developer_guide
