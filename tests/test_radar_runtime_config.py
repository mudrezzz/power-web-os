from __future__ import annotations

import json

from power_web_os.application.radar_runtime_config import (
    build_effective_runtime_config_report,
    compare_runtime_config_reports,
)


def test_runtime_config_report_redacts_secrets_and_builds_fingerprint() -> None:
    report = build_effective_runtime_config_report(
        component="test",
        env={
            "OPENROUTER_API_KEY": "sk-or-test-secret",
            "OPENROUTER_MODEL": "fast/model",
            "OPENROUTER_ADVANCED_MODEL": "advanced/model",
            "OPENROUTER_PLANNER_MODEL": "planner/model",
            "OPENROUTER_EXTRACTOR_MODEL": "extractor/model",
            "OPENROUTER_WEB_MODE": "server_tools",
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


def test_runtime_config_fingerprint_is_stable_and_changes_for_critical_values() -> None:
    first = build_effective_runtime_config_report(component="test", env={"OPENROUTER_MODEL": "a/model"}).to_payload()
    same = build_effective_runtime_config_report(component="test", env={"OPENROUTER_MODEL": "a/model"}).to_payload()
    changed = build_effective_runtime_config_report(component="test", env={"OPENROUTER_MODEL": "b/model"}).to_payload()

    assert first["fingerprint"] == same["fingerprint"]
    assert first["fingerprint"] != changed["fingerprint"]


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
