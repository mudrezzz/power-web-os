from __future__ import annotations

import json
from pathlib import Path

from power_web_os.application.radar.configuration.runtime_config import (
    build_effective_runtime_config_report,
    compare_runtime_config_reports,
)
from power_web_os.application.radar.configuration.runtime_settings import (
    DEFAULT_RADAR_CONFIG_DIR,
    effective_runtime_env,
)


def test_default_radar_config_directory_tracks_repository_config() -> None:
    assert DEFAULT_RADAR_CONFIG_DIR.resolve() == Path("config/radar").resolve()
from power_web_os.demo import _assert_no_secrets, _task_context_from_runtime_config
from power_web_os.integrations.live_radar_openrouter import OpenRouterWebSearchProvider
from power_web_os.workflows.live_radar_executor import _task_context_with_runtime_defaults


NON_SECRET_RUNTIME_ENV_KEYS = (
    "OPENROUTER_MODEL",
    "OPENROUTER_ADVANCED_MODEL",
    "OPENROUTER_PLANNER_MODEL",
    "OPENROUTER_PLANNER_BACKUP_MODEL",
    "OPENROUTER_EXTRACTOR_MODEL",
    "OPENROUTER_EXTRACTION_BACKUP_MODEL",
    "OPENROUTER_BACKUP_MODEL",
    "OPENROUTER_PLANNER_TEMPERATURE",
    "OPENROUTER_EXTRACTOR_TEMPERATURE",
    "OPENROUTER_SIGNAL_TEMPERATURE",
    "OPENROUTER_BACKUP_TEMPERATURE",
    "OPENROUTER_WEB_MODE",
    "POWER_WEB_OS_RADAR_WEB_RETRIEVAL_PROVIDER",
    "POWER_WEB_OS_OPENROUTER_WEB_SEARCH_ENGINE",
    "POWER_WEB_OS_DADATA_MODE",
    "POWER_WEB_OS_DADATA_BASE_URL",
    "POWER_WEB_OS_RADAR_RUN_PROFILE",
    "POWER_WEB_OS_RADAR_MAX_TOTAL_WEB_TASKS_PER_RUN",
    "POWER_WEB_OS_RADAR_MAX_OPENROUTER_CALLS_PER_RUN",
)


def test_runtime_config_loads_non_secret_defaults_from_config_without_env() -> None:
    report = build_effective_runtime_config_report(component="test", env={}).to_payload()
    values = {item["name"]: item for item in report["values"]}

    assert report["config"]["openrouter"]["model"] == "deepseek/deepseek-v4-pro"
    assert report["config"]["openrouter"]["advanced_model"] == "google/gemini-3.1-pro-preview"
    assert report["config"]["openrouter"]["planner_model"] == "google/gemini-3.1-pro-preview"
    assert report["config"]["openrouter"]["planner_backup_model"] == "anthropic/claude-sonnet-4.6"
    assert report["config"]["openrouter"]["extractor_model"] == "openai/gpt-5-mini"
    assert report["config"]["openrouter"]["extraction_backup_model"] == "anthropic/claude-sonnet-4.6"
    assert report["config"]["openrouter"]["web_mode"] == "server_tools"
    assert report["config"]["retrieval"]["provider"] == "openrouter_perplexity"
    assert report["config"]["retrieval"]["openrouter_web_search_engine"] == "perplexity"
    assert report["config"]["dadata"]["mode"] == "live"
    assert report["config"]["radar"]["run_profile"] == "smoke"
    assert report["config"]["radar"]["max_total_web_tasks_per_run"] == 12
    assert report["config"]["radar"]["max_openrouter_calls_per_run"] == 8
    assert report["config"]["radar"]["max_openrouter_planner_calls_per_run"] == 2
    assert report["config"]["radar"]["max_openrouter_web_task_calls_per_run"] == 6
    assert report["config"]["radar"]["max_dadata_lookups_per_run"] == 3
    assert values["OPENROUTER_MODEL"]["source"] == "config:runtime_defaults"
    assert values["POWER_WEB_OS_RADAR_MAX_TOTAL_WEB_TASKS_PER_RUN"]["source"] == "config:run_profile:smoke"


def test_runtime_config_allows_env_override_over_config_defaults() -> None:
    report = build_effective_runtime_config_report(
        component="test",
        env={"OPENROUTER_PLANNER_MODEL": "override/planner"},
    ).to_payload()
    values = {item["name"]: item for item in report["values"]}

    assert report["config"]["openrouter"]["planner_model"] == "override/planner"
    assert report["config"]["openrouter"]["extractor_model"] == "openai/gpt-5-mini"
    assert values["OPENROUTER_PLANNER_MODEL"]["source"] == "process_env"


def test_runtime_config_run_profile_switches_profile_values() -> None:
    report = build_effective_runtime_config_report(
        component="test",
        env={"POWER_WEB_OS_RADAR_RUN_PROFILE": "live"},
    ).to_payload()
    values = {item["name"]: item for item in report["values"]}

    assert report["config"]["radar"]["run_profile"] == "live"
    assert report["config"]["radar"]["max_web_tasks_per_subject"] == 20
    assert report["config"]["radar"]["max_openrouter_calls_per_run"] is None
    assert values["POWER_WEB_OS_RADAR_MAX_WEB_TASKS_PER_SUBJECT"]["source"] == "config:run_profile:live"


def test_live_provider_uses_config_models_when_env_is_clean(monkeypatch) -> None:
    for key in NON_SECRET_RUNTIME_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)
    provider = OpenRouterWebSearchProvider(api_key="test-key", env_path=Path("missing.env"))

    assert provider.model == "deepseek/deepseek-v4-pro"
    assert provider.extractor_model == "openai/gpt-5-mini"
    assert provider.extraction_backup_model == "anthropic/claude-sonnet-4.6"
    assert provider.web_mode == "server_tools"
    assert provider.retrieval_provider == "openrouter_perplexity"
    assert provider.web_search_engine == "perplexity"


def test_workflow_task_context_uses_config_budget_defaults_when_env_is_clean(monkeypatch) -> None:
    for key in NON_SECRET_RUNTIME_ENV_KEYS:
        monkeypatch.delenv(key, raising=False)

    context = _task_context_with_runtime_defaults({})

    assert context["run_profile"] == "smoke"
    assert context["max_total_web_tasks_per_run"] == 12
    assert context["max_openrouter_calls_per_run"] == 8
    assert context["max_dadata_lookups_per_run"] == 3
    assert context["source_verification_mode"] == "soft"


def test_effective_runtime_env_keeps_secret_values_out_of_config() -> None:
    runtime_env = effective_runtime_env(env={})

    assert runtime_env.get("OPENROUTER_API_KEY", "") == ""
    assert runtime_env.get("DADATA_API_KEY", "") == ""
    assert runtime_env["OPENROUTER_MODEL"] == "deepseek/deepseek-v4-pro"


def test_effective_runtime_env_prefers_bom_dotenv_openrouter_key_over_process_env(tmp_path: Path) -> None:
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        "\ufeffOPENROUTER_API_KEY=sk-or-env-file\n"
        "export OPENROUTER_MODEL=openai/gpt-5-mini\n",
        encoding="utf-8",
    )

    runtime_env = effective_runtime_env(
        env={"OPENROUTER_API_KEY": "sk-or-stale-process", "OPENROUTER_MODEL": "stale/model"},
        dotenv_path=dotenv,
    )
    report = build_effective_runtime_config_report(
        component="test",
        env={"OPENROUTER_API_KEY": "sk-or-stale-process", "OPENROUTER_MODEL": "stale/model"},
        dotenv_path=dotenv,
    ).to_payload()
    values = {item["name"]: item for item in report["values"]}

    assert runtime_env["OPENROUTER_API_KEY"] == "sk-or-env-file"
    assert runtime_env["OPENROUTER_MODEL"] == "openai/gpt-5-mini"
    assert values["openrouter credential"]["source"] == ".env"
    assert values["OPENROUTER_MODEL"]["source"] == ".env"


def test_runtime_config_report_redacts_secrets_and_builds_fingerprint() -> None:
    report = build_effective_runtime_config_report(
        component="test",
        env={
            "OPENROUTER_API_KEY": "sk-or-test-secret",
            "OPENROUTER_MODEL": "fast/model",
            "OPENROUTER_ADVANCED_MODEL": "advanced/model",
            "OPENROUTER_PLANNER_MODEL": "planner/model",
            "OPENROUTER_PLANNER_BACKUP_MODEL": "planner-backup/model",
            "OPENROUTER_EXTRACTOR_MODEL": "extractor/model",
            "OPENROUTER_EXTRACTION_BACKUP_MODEL": "backup/model",
            "OPENROUTER_PLANNER_TEMPERATURE": "0.1",
            "OPENROUTER_EXTRACTOR_TEMPERATURE": "0",
            "OPENROUTER_SIGNAL_TEMPERATURE": "0.2",
            "OPENROUTER_BACKUP_TEMPERATURE": "0.15",
            "OPENROUTER_WEB_MODE": "server_tools",
            "POWER_WEB_OS_RADAR_MODEL_PROFILE_DIR": "config/radar/model_profiles",
            "POWER_WEB_OS_RADAR_WEB_RETRIEVAL_PROVIDER": "openrouter_perplexity",
            "POWER_WEB_OS_OPENROUTER_WEB_SEARCH_ENGINE": "perplexity",
            "POWER_WEB_OS_DADATA_MODE": "live",
            "DADATA_API_KEY": "dadata-key",
            "DADATA_SECRET_KEY": "dadata-secret",
            "POWER_WEB_OS_DATABASE_URL": "postgresql://user:password@db.example.test:5432/power",
            "POWER_WEB_OS_CELERY_BROKER_URL": "redis://:password@redis.example.test:6379/0",
            "POWER_WEB_OS_RADAR_MAX_SIGNAL_TASKS_PER_CANDIDATE_SIGNAL": "2",
            "POWER_WEB_OS_RADAR_RUN_PROFILE": "smoke",
            "POWER_WEB_OS_RADAR_MAX_OPENROUTER_CALLS_PER_RUN": "8",
            "POWER_WEB_OS_RADAR_MAX_OPENROUTER_PLANNER_CALLS_PER_RUN": "2",
            "POWER_WEB_OS_RADAR_MAX_OPENROUTER_WEB_TASK_CALLS_PER_RUN": "6",
            "POWER_WEB_OS_RADAR_MAX_OPENROUTER_SERVER_TOOL_WEB_SEARCHES_PER_RUN": "24",
            "POWER_WEB_OS_RADAR_MAX_DADATA_LOOKUPS_PER_RUN": "0",
            "POWER_WEB_OS_RADAR_MAX_SOURCE_VERIFICATION_REQUESTS_PER_RUN": "20",
            "POWER_WEB_OS_RADAR_MAX_PROVIDER_RETRIES_PER_TASK": "1",
            "POWER_WEB_OS_RADAR_OPENROUTER_WEB_MAX_RESULTS_PER_CALL": "3",
            "POWER_WEB_OS_RADAR_OPENROUTER_WEB_MAX_TOTAL_RESULTS_PER_CALL": "6",
            "POWER_WEB_OS_RADAR_SMOKE_MAX_CANDIDATES": "2",
            "POWER_WEB_OS_RADAR_SMOKE_MAX_SIGNALS": "1",
        },
    ).to_payload()

    serialized = json.dumps(report, ensure_ascii=False)
    assert report["component"] == "test"
    assert len(report["fingerprint"]) == 16
    assert report["config"]["openrouter"]["api_key_present"] is True
    assert report["config"]["openrouter"]["planner_backup_model"] == "planner-backup/model"
    assert report["config"]["openrouter"]["extraction_backup_model"] == "backup/model"
    assert report["config"]["openrouter"]["planner_temperature"] == 0.1
    assert report["config"]["openrouter"]["extractor_temperature"] == 0
    assert report["config"]["openrouter"]["signal_temperature"] == 0.2
    assert report["config"]["openrouter"]["backup_temperature"] == 0.15
    assert report["config"]["model_profiles"]["status"] == "loaded"
    assert report["config"]["model_profiles"]["candidate_discovery"]["profile_id"] == "candidate_discovery_default"
    assert report["config"]["model_profiles"]["signal_monitoring"]["profile_id"] == "signal_monitoring_default"
    assert "signal_extractor" in report["config"]["model_profiles"]["signal_monitoring"]["roles"]
    assert report["config"]["dadata"]["credentials_present"] is True
    assert report["config"]["retrieval"]["provider"] == "openrouter_perplexity"
    assert report["config"]["retrieval"]["openrouter_web_search_engine"] == "perplexity"
    assert report["config"]["radar"]["max_signal_tasks_per_candidate_signal"] == 2
    assert report["config"]["radar"]["run_profile"] == "smoke"
    assert report["config"]["radar"]["max_openrouter_calls_per_run"] == 8
    assert report["config"]["radar"]["max_openrouter_planner_calls_per_run"] == 2
    assert report["config"]["radar"]["max_openrouter_web_task_calls_per_run"] == 6
    assert report["config"]["radar"]["max_openrouter_server_tool_web_searches_per_run"] == 24
    assert report["config"]["radar"]["max_dadata_lookups_per_run"] == 0
    assert report["config"]["radar"]["max_source_verification_requests_per_run"] == 20
    assert report["config"]["radar"]["max_provider_retries_per_task"] == 1
    assert report["config"]["radar"]["openrouter_web_max_results_per_call"] == 3
    assert report["config"]["radar"]["openrouter_web_max_total_results_per_call"] == 6
    assert report["config"]["radar"]["smoke_max_candidates"] == 2
    assert report["config"]["radar"]["smoke_max_signals"] == 1
    assert "[REDACTED]@db.example.test:5432" in serialized
    assert "[REDACTED]@redis.example.test:6379" in serialized
    assert not any(secret in serialized for secret in ["sk-or-test-secret", "dadata-key", "dadata-secret", "password@"])


def test_runtime_config_keeps_candidate_and_signal_model_profiles_independent(tmp_path: Path) -> None:
    first_dir = tmp_path / "profiles-a"
    second_dir = tmp_path / "profiles-b"
    first_dir.mkdir()
    second_dir.mkdir()
    _write_model_profiles(first_dir, candidate_model="candidate/model-a", signal_model="signal/model")
    _write_model_profiles(second_dir, candidate_model="candidate/model-b", signal_model="signal/model")

    first = build_effective_runtime_config_report(
        component="test",
        env={"POWER_WEB_OS_RADAR_MODEL_PROFILE_DIR": str(first_dir)},
    ).to_payload()
    second = build_effective_runtime_config_report(
        component="test",
        env={"POWER_WEB_OS_RADAR_MODEL_PROFILE_DIR": str(second_dir)},
    ).to_payload()

    assert (
        first["config"]["model_profiles"]["candidate_discovery"]["roles"]["planner"]["primary_model"]
        != second["config"]["model_profiles"]["candidate_discovery"]["roles"]["planner"]["primary_model"]
    )
    assert first["config"]["model_profiles"]["signal_monitoring"] == second["config"]["model_profiles"]["signal_monitoring"]


def test_runtime_config_fingerprint_is_stable_and_changes_for_critical_values() -> None:
    first = build_effective_runtime_config_report(component="test", env={"OPENROUTER_MODEL": "a/model"}).to_payload()
    same = build_effective_runtime_config_report(component="test", env={"OPENROUTER_MODEL": "a/model"}).to_payload()
    changed = build_effective_runtime_config_report(component="test", env={"OPENROUTER_MODEL": "b/model"}).to_payload()

    assert first["fingerprint"] == same["fingerprint"]
    assert first["fingerprint"] != changed["fingerprint"]


def test_runtime_config_keeps_role_specific_extraction_backup_over_generic_alias() -> None:
    report = build_effective_runtime_config_report(
        component="test",
        env={"OPENROUTER_MODEL": "primary/model", "OPENROUTER_BACKUP_MODEL": "generic/backup"},
    ).to_payload()

    assert report["config"]["openrouter"]["extraction_backup_model"] == "anthropic/claude-sonnet-4.6"


def test_runtime_config_compare_reports_critical_mismatch() -> None:
    api = build_effective_runtime_config_report(
        component="api",
        env={"POWER_WEB_OS_RADAR_WEB_RETRIEVAL_PROVIDER": "openrouter"},
    ).to_payload()
    worker = build_effective_runtime_config_report(
        component="worker",
        env={"POWER_WEB_OS_RADAR_WEB_RETRIEVAL_PROVIDER": "openrouter_perplexity"},
    ).to_payload()

    warnings = compare_runtime_config_reports(expected=api, actual=worker)

    assert any(item["code"] == "runtime_config_mismatch" for item in warnings)
    assert any(item.get("path") == "retrieval.provider" for item in warnings)


def test_demo_persisted_cli_task_context_uses_effective_radar_runtime_config() -> None:
    runtime_config = build_effective_runtime_config_report(
        component="cli",
        env={
            "POWER_WEB_OS_RADAR_RUN_PROFILE": "smoke",
            "POWER_WEB_OS_RADAR_MAX_OPENROUTER_CALLS_PER_RUN": "8",
            "POWER_WEB_OS_RADAR_MAX_DADATA_LOOKUPS_PER_RUN": "3",
            "POWER_WEB_OS_RADAR_SMOKE_MAX_CANDIDATES": "2",
            "POWER_WEB_OS_RADAR_SMOKE_MAX_SIGNALS": "1",
        },
    ).to_payload()

    task_context = _task_context_from_runtime_config(runtime_config)

    assert task_context["run_profile"] == "smoke"
    assert task_context["max_openrouter_calls_per_run"] == 8
    assert task_context["max_dadata_lookups_per_run"] == 3
    assert task_context["smoke_max_candidates"] == 2
    assert task_context["smoke_max_signals"] == 1
    assert task_context["source"] == "demo_persisted_cli"


def test_demo_secret_guard_allows_env_var_names_but_rejects_secret_values() -> None:
    _assert_no_secrets({"remediation": "Check OPENROUTER_API_KEY and DADATA_API_KEY."})

    try:
        _assert_no_secrets({"value": "sk-or-test-secret"})
    except RuntimeError:
        pass
    else:  # pragma: no cover - explicit assertion keeps the failure readable.
        raise AssertionError("secret-like OpenRouter value was not rejected")


def _write_model_profiles(directory: Path, *, candidate_model: str, signal_model: str) -> None:
    (directory / "candidate_discovery.json").write_text(
        json.dumps({
            "profile_id": "candidate_discovery_default",
            "pipeline_id": "candidate-discovery",
            "roles": {
                "planner": {"primary_model": candidate_model, "temperature": 0, "max_attempts": 1}
            },
        }),
        encoding="utf-8",
    )
    (directory / "signal_monitoring.json").write_text(
        json.dumps({
            "profile_id": "signal_monitoring_default",
            "pipeline_id": "signal-monitoring",
            "roles": {
                "signal_task_builder": {"primary_model": signal_model, "temperature": 0.1, "max_attempts": 1},
                "signal_extractor": {"primary_model": signal_model, "temperature": 0, "max_attempts": 1},
                "signal_backup_extractor": {"primary_model": signal_model, "temperature": 0, "max_attempts": 1},
                "signal_evidence_judge": {"primary_model": signal_model, "temperature": 0, "max_attempts": 1},
                "signal_dedupe_judge": {"primary_model": signal_model, "temperature": 0, "max_attempts": 1},
            },
        }),
        encoding="utf-8",
    )
