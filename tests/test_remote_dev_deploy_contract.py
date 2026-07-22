from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_remote_dev_config_is_non_secret_and_complete() -> None:
    config = read("deploy/remote-dev.env")
    for expected in [
        "POWER_WEB_OS_EXECUTION_CONTOUR=remote",
        "POWER_WEB_OS_REMOTE_HOST=213.148.13.45",
        "POWER_WEB_OS_REMOTE_SSH_TARGET=flowise",
        "POWER_WEB_OS_REMOTE_VALIDATION_ROOT=/opt/power-web-os/workspaces",
        "POWER_WEB_OS_REMOTE_RELEASE_ROOT=/opt/power-web-os/releases",
        "POWER_WEB_OS_REMOTE_SHARED_ROOT=/opt/power-web-os/shared",
        "POWER_WEB_OS_REMOTE_COMPOSE_PROJECT=power-web-os-dev",
        "POWER_WEB_OS_REMOTE_LOCK_PATH=/var/lock/power-web-os-dev.lock",
    ]:
        assert expected in config
    assert not any(marker in config.lower() for marker in ["openrouter_api_key", "sk-or-", "password="])


def test_remote_orchestrator_has_all_actions_and_guards() -> None:
    script = read("scripts/remote_dev.ps1")
    for action in ["Probe", "Sync", "Test", "Deploy", "Exec", "ImportHistory", "Collect", "Logs", "Cleanup"]:
        assert f'"{action}"' in script
    for marker in [
        "provider_calls_blocked",
        "artifact_not_allowed",
        "remote_stack_busy",
        "workspace_sha256",
        "session-manifest.json",
        "flock -n",
        "--exclude=.env",
        "${sharedRoot}/.env",
        "pwos-val-${SessionId}",
        "Remote session workspace is absent; local manifest retained after cleanup.",
        "Local history database is active or not checkpointed",
        "pragma integrity_check",
        "power_web_os.sqlite3.before-${SessionId}.bak",
        "history_import_failed_rolling_back",
        "ImportHistory never permits provider calls",
        "ALLOW_PARTIAL_TRACE_RECOVERY",
        "unreadable_trace_count",
    ]:
        assert marker in script
    assert "LocalEnvPath" not in script
    assert "OPENROUTER_API_KEY" not in script


def test_history_import_is_explicit_locked_and_does_not_weaken_normal_sync() -> None:
    script = read("scripts/remote_dev.ps1")

    assert 'Join-Path $RepoRoot "demo/output/power_web_os.sqlite3"' in script
    assert 'Add-ManifestCommand -Kind "ImportHistory"' in script
    assert "AllowPartialTraceRecovery" in script
    assert "flock -E 75 -n" in script
    assert "cp -a \"`$target_db\" \"`$backup_db\"" in script
    assert "mv -f \"`$target_db.incoming\" \"`$target_db\"" in script
    assert '"--exclude=demo/output"' in script


def test_compatibility_wrapper_only_delegates() -> None:
    wrapper = read("scripts/deploy_remote_dev.ps1")
    assert "remote_dev.ps1" in wrapper
    assert '"Deploy"' in wrapper
    assert "scp" not in wrapper
    assert "docker compose" not in wrapper
    assert ".env" not in wrapper


def test_validation_compose_is_isolated_and_socket_is_control_only() -> None:
    compose = read("docker-compose.validation.yml")
    for service in ["backend-tests", "frontend-tests", "playwright-tests", "validation-redis"]:
        assert f"  {service}:" in compose
    assert "ports:" not in compose
    assert ".env" not in compose
    assert len([line for line in compose.splitlines() if "/var/run/docker.sock" in line]) == 1
    assert "playwright-control-tests:" in compose
    assert "mcr.microsoft.com/playwright:v1.60.0-noble" in read(
        "frontend/Dockerfile.playwright-validation"
    )
    assert "npm ci" in read("frontend/Dockerfile.validation")


def test_remote_skills_are_discoverable() -> None:
    validation_skill = read(".agents/skills/remote-dev-validation/SKILL.md")
    deploy_skill = read(".agents/skills/deploy-remote-dev/SKILL.md")
    agents = read("AGENTS.md")
    assert validation_skill.startswith("---\nname: remote-dev-validation\n")
    assert deploy_skill.startswith("---\nname: deploy-remote-dev\n")
    assert "scripts/remote_dev.ps1" in validation_skill
    assert "Never print or upload the local `.env`" in deploy_skill
    assert "$remote-dev-validation" in agents
    assert "Never silently fall back" in agents


def test_dev_compose_uses_configurable_remote_paths() -> None:
    compose = read("docker-compose.yml")
    for marker in [
        "POWER_WEB_OS_DATA_PATH",
        "POWER_WEB_OS_ENV_FILE",
        "POWER_WEB_OS_API_HOST_PORT",
        "POWER_WEB_OS_FRONTEND_HOST_PORT",
        "POWER_WEB_OS_REDIS_HOST_PORT",
    ]:
        assert marker in compose
