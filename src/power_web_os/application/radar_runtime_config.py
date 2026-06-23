"""Redacted effective runtime configuration for Radar execution.

This module is application-owned: it describes what the current process will
use for Radar execution without importing API, Celery, SQLAlchemy, or provider
HTTP clients. Entry points can pass process-specific overrides before exposing
the report through CLI, API, run metadata, or technical trace.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urlsplit, urlunsplit

SECRET_KEYS = {
    "OPENROUTER_API_KEY",
    "DADATA_API_KEY",
    "DADATA_SECRET_KEY",
}

DEFAULT_RUNTIME_DATABASE_URL = "sqlite:///./demo/output/power_web_os.sqlite3"

CRITICAL_FINGERPRINT_PATHS = (
    ("openrouter", "model"),
    ("openrouter", "planner_model"),
    ("openrouter", "extractor_model"),
    ("openrouter", "web_mode"),
    ("retrieval", "provider"),
    ("retrieval", "openrouter_web_search_engine"),
    ("dadata", "mode"),
    ("dadata", "credentials_present"),
    ("radar", "source_verification_mode"),
    ("radar", "max_discovery_tasks_per_rule"),
    ("radar", "max_gate_tasks_per_candidate_rule"),
    ("radar", "max_signal_tasks_per_candidate_signal"),
    ("radar", "max_total_web_tasks_per_run"),
)


@dataclass(frozen=True, slots=True)
class RadarRuntimeConfigValue:
    name: str
    value: Any
    source: str
    secret_present: bool | None = None

    def to_payload(self) -> dict[str, Any]:
        payload = {"name": self.name, "value": self.value, "source": self.source}
        if self.secret_present is not None:
            payload["secret_present"] = self.secret_present
        return payload


@dataclass(frozen=True, slots=True)
class RadarRuntimeConfigCheckResult:
    code: str
    status: str
    severity: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    remediation: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "status": self.status,
            "severity": self.severity,
            "message": self.message,
            "details": self.details,
            "remediation": self.remediation,
        }


@dataclass(frozen=True, slots=True)
class RadarRuntimeConfigReport:
    component: str
    config: dict[str, Any]
    values: tuple[RadarRuntimeConfigValue, ...]
    checks: tuple[RadarRuntimeConfigCheckResult, ...] = ()

    @property
    def fingerprint(self) -> str:
        body = json.dumps(_fingerprint_payload(self.config), ensure_ascii=False, sort_keys=True)
        return hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]

    def to_payload(self) -> dict[str, Any]:
        return {
            "artifact_type": "radar_runtime_config_report",
            "component": self.component,
            "fingerprint": self.fingerprint,
            "config": self.config,
            "values": [value.to_payload() for value in self.values],
            "checks": [check.to_payload() for check in self.checks],
            "summary": {
                "openrouter_api_key_present": bool(self.config["openrouter"]["api_key_present"]),
                "dadata_credentials_present": bool(self.config["dadata"]["credentials_present"]),
                "retrieval_provider": self.config["retrieval"]["provider"],
                "retrieval_engine": self.config["retrieval"]["openrouter_web_search_engine"],
                "web_mode": self.config["openrouter"]["web_mode"],
                "source_verification_mode": self.config["radar"]["source_verification_mode"],
            },
        }


def build_effective_runtime_config_report(
    *,
    component: str,
    env: Mapping[str, str] | None = None,
    dotenv_path: Path | None = None,
    overrides: Mapping[str, Any] | None = None,
) -> RadarRuntimeConfigReport:
    env_values = _effective_env(env=env, dotenv_path=dotenv_path, overrides=overrides)
    values: list[RadarRuntimeConfigValue] = []

    def value(name: str, default: Any = None) -> Any:
        resolved, source = _resolve(env_values, name, default)
        values.append(RadarRuntimeConfigValue(name=name, value=_redacted_value(name, resolved), source=source))
        return resolved

    def secret(name: str) -> bool:
        resolved, source = _resolve(env_values, name, "")
        present = bool(str(resolved or "").strip())
        values.append(RadarRuntimeConfigValue(
            name=_public_secret_name(name),
            value="[PRESENT]" if present else "[MISSING]",
            source=source,
            secret_present=present,
        ))
        return present

    openrouter_key_present = secret("OPENROUTER_API_KEY")
    openrouter_model = str(value("OPENROUTER_MODEL", "openai/gpt-4.1-mini") or "openai/gpt-4.1-mini")
    advanced_model = str(value("OPENROUTER_ADVANCED_MODEL", "") or "")
    planner_model = str(value("OPENROUTER_PLANNER_MODEL", advanced_model or openrouter_model) or advanced_model or openrouter_model)
    extractor_model = str(value("OPENROUTER_EXTRACTOR_MODEL", advanced_model or openrouter_model) or advanced_model or openrouter_model)
    web_mode = str(value("OPENROUTER_WEB_MODE", "auto") or "auto")
    retrieval_provider = str(value("POWER_WEB_OS_RADAR_WEB_RETRIEVAL_PROVIDER", "openrouter") or "openrouter")
    retrieval_engine_default = "perplexity" if retrieval_provider == "openrouter_perplexity" else "auto"
    retrieval_engine = str(value("POWER_WEB_OS_OPENROUTER_WEB_SEARCH_ENGINE", retrieval_engine_default) or retrieval_engine_default)

    dadata_api_key_present = secret("DADATA_API_KEY")
    dadata_secret_present = secret("DADATA_SECRET_KEY")
    dadata_mode = str(value("POWER_WEB_OS_DADATA_MODE", "recorded") or "recorded")
    dadata_base_url = str(value("POWER_WEB_OS_DADATA_BASE_URL", "https://suggestions.dadata.ru/suggestions/api/4_1/rs/suggest/party") or "")

    database_url = str(value("POWER_WEB_OS_DATABASE_URL", DEFAULT_RUNTIME_DATABASE_URL) or DEFAULT_RUNTIME_DATABASE_URL)
    celery_broker_url = str(value("POWER_WEB_OS_CELERY_BROKER_URL", "redis://localhost:6379/0") or "")
    celery_result_backend = str(value("POWER_WEB_OS_CELERY_RESULT_BACKEND", "redis://localhost:6379/1") or "")

    config = {
        "openrouter": {
            "api_key_present": openrouter_key_present,
            "model": openrouter_model,
            "advanced_model": advanced_model,
            "planner_model": planner_model,
            "extractor_model": extractor_model,
            "web_mode": web_mode,
        },
        "retrieval": {
            "provider": retrieval_provider,
            "openrouter_web_search_engine": retrieval_engine,
        },
        "dadata": {
            "mode": dadata_mode,
            "base_url": _redact_url(dadata_base_url),
            "api_key_present": dadata_api_key_present,
            "secret_key_present": dadata_secret_present,
            "credentials_present": dadata_api_key_present and dadata_secret_present,
        },
        "radar": {
            "max_web_tasks_per_subject": _int_value(value("POWER_WEB_OS_RADAR_MAX_WEB_TASKS_PER_SUBJECT", 20), 20),
            "max_discovery_tasks_per_rule": _optional_int_value(value("POWER_WEB_OS_RADAR_MAX_DISCOVERY_TASKS_PER_RULE", "")),
            "max_gate_tasks_per_candidate_rule": _optional_int_value(value("POWER_WEB_OS_RADAR_MAX_GATE_TASKS_PER_CANDIDATE_RULE", "")),
            "max_signal_tasks_per_candidate_signal": _optional_int_value(value("POWER_WEB_OS_RADAR_MAX_SIGNAL_TASKS_PER_CANDIDATE_SIGNAL", "")),
            "max_total_web_tasks_per_run": _optional_int_value(value("POWER_WEB_OS_RADAR_MAX_TOTAL_WEB_TASKS_PER_RUN", "")),
            "source_verification_mode": str(value("POWER_WEB_OS_RADAR_SOURCE_VERIFICATION_MODE", "soft") or "soft"),
            "min_useful_sources_per_discovery_task": _int_value(value("POWER_WEB_OS_RADAR_MIN_USEFUL_SOURCES_PER_DISCOVERY_TASK", 3), 3),
            "min_candidates_per_discovery_task": _int_value(value("POWER_WEB_OS_RADAR_MIN_CANDIDATES_PER_DISCOVERY_TASK", 5), 5),
            "max_discovery_retries_per_task": _int_value(value("POWER_WEB_OS_RADAR_MAX_DISCOVERY_RETRIES_PER_TASK", 2), 2),
        },
        "persistence": {
            "database_kind": _url_kind(database_url),
            "database_url": _redact_url(database_url),
        },
        "celery": {
            "broker_kind": _url_kind(celery_broker_url),
            "broker_url": _redact_url(celery_broker_url),
            "result_backend_kind": _url_kind(celery_result_backend),
            "result_backend": _redact_url(celery_result_backend),
        },
    }
    checks = tuple(_runtime_config_checks(config))
    return RadarRuntimeConfigReport(component=component, config=config, values=tuple(values), checks=checks)


def compare_runtime_config_reports(
    *,
    expected: dict[str, Any] | None,
    actual: dict[str, Any],
) -> list[dict[str, Any]]:
    if not isinstance(expected, dict):
        return []
    expected_config = expected.get("config") if isinstance(expected.get("config"), dict) else {}
    actual_config = actual.get("config") if isinstance(actual.get("config"), dict) else {}
    warnings: list[dict[str, Any]] = []
    for path in CRITICAL_FINGERPRINT_PATHS:
        left = _nested_value(expected_config, path)
        right = _nested_value(actual_config, path)
        if left != right:
            warnings.append({
                "code": "runtime_config_mismatch",
                "path": ".".join(path),
                "api_value": left,
                "worker_value": right,
                "severity": "warning",
            })
    if expected.get("fingerprint") and actual.get("fingerprint") and expected.get("fingerprint") != actual.get("fingerprint"):
        warnings.append({
            "code": "runtime_config_fingerprint_mismatch",
            "api_fingerprint": expected.get("fingerprint"),
            "worker_fingerprint": actual.get("fingerprint"),
            "severity": "warning",
        })
    return warnings


def runtime_config_api_overrides(settings: Any) -> dict[str, Any]:
    return {
        "POWER_WEB_OS_DATABASE_URL": getattr(settings, "database_url", None),
        "POWER_WEB_OS_RADAR_MAX_WEB_TASKS_PER_SUBJECT": getattr(settings, "radar_max_web_tasks_per_subject", None),
        "POWER_WEB_OS_RADAR_MAX_DISCOVERY_TASKS_PER_RULE": getattr(settings, "radar_max_discovery_tasks_per_rule", None),
        "POWER_WEB_OS_RADAR_MAX_GATE_TASKS_PER_CANDIDATE_RULE": getattr(settings, "radar_max_gate_tasks_per_candidate_rule", None),
        "POWER_WEB_OS_RADAR_MAX_SIGNAL_TASKS_PER_CANDIDATE_SIGNAL": getattr(settings, "radar_max_signal_tasks_per_candidate_signal", None),
        "POWER_WEB_OS_RADAR_MAX_TOTAL_WEB_TASKS_PER_RUN": getattr(settings, "radar_max_total_web_tasks_per_run", None),
        "POWER_WEB_OS_RADAR_SOURCE_VERIFICATION_MODE": getattr(settings, "radar_source_verification_mode", None),
        "POWER_WEB_OS_RADAR_MIN_USEFUL_SOURCES_PER_DISCOVERY_TASK": getattr(settings, "radar_min_useful_sources_per_discovery_task", None),
        "POWER_WEB_OS_RADAR_MIN_CANDIDATES_PER_DISCOVERY_TASK": getattr(settings, "radar_min_candidates_per_discovery_task", None),
        "POWER_WEB_OS_RADAR_MAX_DISCOVERY_RETRIES_PER_TASK": getattr(settings, "radar_max_discovery_retries_per_task", None),
    }


def _runtime_config_checks(config: dict[str, Any]) -> list[RadarRuntimeConfigCheckResult]:
    checks: list[RadarRuntimeConfigCheckResult] = []
    checks.append(_check(
        "openrouter_credentials",
        passed=bool(config["openrouter"]["api_key_present"]),
        message="OpenRouter API key is present.",
        failed_message="OpenRouter API key is missing.",
        remediation="Set OPENROUTER_API_KEY before live OpenRouter probes or full live Radar runs.",
    ))
    if config["dadata"]["mode"] == "live":
        checks.append(_check(
            "dadata_credentials",
            passed=bool(config["dadata"]["credentials_present"]),
            message="DaData live credentials are present.",
            failed_message="DaData live mode is enabled but credentials are missing.",
            remediation="Set DADATA_API_KEY and DADATA_SECRET_KEY, or switch POWER_WEB_OS_DADATA_MODE to recorded.",
        ))
    else:
        checks.append(RadarRuntimeConfigCheckResult(
            code="dadata_credentials",
            status="skipped",
            severity="info",
            message="DaData credentials are not required in recorded mode.",
        ))
    return checks


def _check(
    code: str,
    *,
    passed: bool,
    message: str,
    failed_message: str,
    remediation: str,
) -> RadarRuntimeConfigCheckResult:
    return RadarRuntimeConfigCheckResult(
        code=code,
        status="passed" if passed else "failed",
        severity="info" if passed else "error",
        message=message if passed else failed_message,
        remediation="" if passed else remediation,
    )


def _effective_env(
    *,
    env: Mapping[str, str] | None,
    dotenv_path: Path | None,
    overrides: Mapping[str, Any] | None,
) -> dict[str, tuple[Any, str]]:
    result: dict[str, tuple[Any, str]] = {}
    if dotenv_path is not None:
        for key, value in _load_env_file(dotenv_path).items():
            result[key] = (value, ".env")
    source_env = dict(os.environ if env is None else env)
    for key, value in source_env.items():
        result[key] = (value, "process_env")
    for key, value in (overrides or {}).items():
        if value is not None:
            result[key] = (value, "explicit_override")
    return result


def _resolve(values: Mapping[str, tuple[Any, str]], name: str, default: Any) -> tuple[Any, str]:
    if name in values:
        return values[name]
    return default, "default"


def _redacted_value(name: str, value: Any) -> Any:
    if name in SECRET_KEYS:
        return "[PRESENT]" if str(value or "").strip() else "[MISSING]"
    if name.endswith("_URL") or name in {"POWER_WEB_OS_CELERY_BROKER_URL", "POWER_WEB_OS_CELERY_RESULT_BACKEND"}:
        return _redact_url(str(value or ""))
    return value


def _public_secret_name(name: str) -> str:
    return {
        "OPENROUTER_API_KEY": "openrouter credential",
        "DADATA_API_KEY": "dadata api credential",
        "DADATA_SECRET_KEY": "dadata secret credential",
    }.get(name, "credential")


def _redact_url(value: str) -> str:
    if not value:
        return ""
    parsed = urlsplit(value)
    if not parsed.scheme:
        return value
    netloc = parsed.hostname or ""
    if parsed.port:
        netloc = f"{netloc}:{parsed.port}"
    if parsed.username or parsed.password:
        netloc = f"[REDACTED]@{netloc}"
    return urlunsplit((parsed.scheme, netloc, parsed.path, "", ""))


def _url_kind(value: str) -> str:
    return (urlsplit(value).scheme or "path").split("+", 1)[0]


def _int_value(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= 0 else default


def _optional_int_value(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _fingerprint_payload(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "openrouter": config.get("openrouter", {}),
        "retrieval": config.get("retrieval", {}),
        "dadata": config.get("dadata", {}),
        "radar": config.get("radar", {}),
        "persistence": {"database_kind": _nested_value(config, ("persistence", "database_kind"))},
        "celery": {
            "broker_kind": _nested_value(config, ("celery", "broker_kind")),
            "result_backend_kind": _nested_value(config, ("celery", "result_backend_kind")),
        },
    }


def _nested_value(payload: dict[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = payload
    for item in path:
        if not isinstance(value, dict):
            return None
        value = value.get(item)
    return value


def _load_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values
