"""Demo CLI helpers for Radar execution preflight."""

from __future__ import annotations

import json
from pathlib import Path
from time import perf_counter
from typing import Any

from power_web_os.application.radar.candidate_discovery.retrieval.definition import build_live_mini_radar_definition
from power_web_os.application.radar.candidate_discovery.planning.definition_runtime import active_definition_to_live_radar_payload
from power_web_os.application.radar.candidate_discovery.contracts import RadarSearchPlan, RadarSearchQuery
from power_web_os.application.radar.candidate_discovery.sources.providers import CompanyLookupRequest
from power_web_os.application.radar.configuration.runtime_config import build_effective_runtime_config_report
from power_web_os.application.radar.configuration.runtime_settings import effective_runtime_env
from power_web_os.application.radar.preflight.service import (
    RadarExecutionPreflightService,
    validate_provider_output_fixture,
)
from power_web_os.integrations.dadata_provider import DaDataCompanyRegistryProvider
from power_web_os.integrations.live_radar_openrouter import OpenRouterWebSearchProvider
from power_web_os.persistence import (
    SqlAlchemyRadarDefinitionRepository,
    create_database_engine,
    create_session_factory,
    session_scope,
)


def build_radar_preflight_report(
    *,
    radar_id: str,
    database_url: str | None = None,
    profile: str = "recorded",
    show_runtime_config: bool = False,
    live_probes: bool = False,
    probes: tuple[str, ...] = (),
) -> dict[str, Any]:
    engine = create_database_engine(database_url=database_url)
    session_factory = create_session_factory(engine)
    with session_scope(session_factory) as session:
        definition_repository = SqlAlchemyRadarDefinitionRepository(session)
        service = RadarExecutionPreflightService(
            definition_repository=definition_repository,
            runtime_definition_provider=lambda: _active_runtime_definition_payload(
                definition_repository,
                radar_id=radar_id,
            ),
            company_registry_provider_ids=_available_company_registry_provider_ids(),
        )
        report = service.run(radar_id=radar_id, profile="recorded" if profile == "recorded" else "static")
    payload = report.to_payload()
    if show_runtime_config:
        payload["runtime_config"] = build_effective_runtime_config_report(
            component="cli",
            dotenv_path=Path.cwd() / ".env",
            overrides={"POWER_WEB_OS_DATABASE_URL": database_url} if database_url else None,
        ).to_payload()
    if probes:
        _attach_probe_results(payload, radar_id=radar_id, live_probes=live_probes, probes=_normalize_probes(probes))
    return payload


def print_preflight_report(report: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    status = "READY" if report.get("ready_for_live_run") else "NOT READY"
    summary = report.get("summary", {})
    print(f"Radar preflight: {status}")
    print(f"Radar: {report.get('radar_id')}")
    print(f"Definition: {report.get('definition_id') or 'missing'}")
    print(
        "Checks: "
        f"{summary.get('passed_count', 0)} passed, "
        f"{summary.get('error_count', 0)} errors, "
        f"{summary.get('warning_count', 0)} warnings"
    )
    for check in report.get("checks", []):
        if check.get("status") == "passed":
            continue
        print(f"- {check.get('code')}: {check.get('message')}")
        if check.get("remediation"):
            print(f"  remediation: {check['remediation']}")


def _active_runtime_definition_payload(
    definition_repository: Any,
    *,
    radar_id: str,
) -> dict[str, Any]:
    definition = definition_repository.get_active(radar_id)
    if definition is None:
        return build_live_mini_radar_definition()
    return active_definition_to_live_radar_payload(definition)


def _available_company_registry_provider_ids() -> set[str]:
    env = effective_runtime_env(dotenv_path=Path.cwd() / ".env")
    mode = (env.get("POWER_WEB_OS_DADATA_MODE") or "recorded").strip().lower()
    if mode == "recorded":
        return {"dadata"}
    return {"dadata"} if mode == "live" and env.get("DADATA_API_KEY") and env.get("DADATA_SECRET_KEY") else set()


def _normalize_probes(probes: tuple[str, ...]) -> tuple[str, ...]:
    normalized = tuple(dict.fromkeys(item.strip().lower() for item in probes if item.strip()))
    if "all" in normalized:
        return ("dadata", "openrouter-web", "openrouter-perplexity", "extraction-schema")
    return normalized


def _attach_probe_results(
    report: dict[str, Any],
    *,
    radar_id: str,
    live_probes: bool,
    probes: tuple[str, ...],
) -> None:
    results = [_run_probe(probe, radar_id=radar_id, live_probes=live_probes) for probe in probes]
    report["live_probes"] = results
    failed = [item["code"] for item in results if item["status"] == "failed"]
    if failed:
        report["ready_for_live_run"] = False
        summary = dict(report.get("summary") or {})
        summary["failed_codes"] = sorted(set([*summary.get("failed_codes", []), *failed]))
        summary["error_count"] = int(summary.get("error_count", 0)) + len(failed)
        report["summary"] = summary


def _run_probe(probe: str, *, radar_id: str, live_probes: bool) -> dict[str, Any]:
    if probe == "extraction-schema":
        return _extraction_schema_probe()
    if not live_probes:
        return {
            "code": f"{probe}_probe",
            "status": "skipped",
            "severity": "info",
            "message": "Live probe skipped because --live-probes was not provided.",
            "details": {"probe": probe},
            "remediation": "Add --live-probes to run this bounded network probe.",
        }
    if probe == "dadata":
        return _dadata_probe()
    if probe in {"openrouter-web", "openrouter-perplexity"}:
        return _openrouter_probe(probe=probe, radar_id=radar_id)
    return {
        "code": f"{probe}_probe",
        "status": "failed",
        "severity": "error",
        "message": f"Unknown preflight probe: {probe}.",
        "details": {"probe": probe},
        "remediation": "Use one of: dadata, openrouter-web, openrouter-perplexity, extraction-schema, all.",
    }


def _extraction_schema_probe() -> dict[str, Any]:
    started_at = perf_counter()
    issues = validate_provider_output_fixture({
        "sources": [{"evidence_ref": "probe_src", "title": "Probe", "url": "https://example.test", "snippet": "Probe"}],
        "candidates": [
            {
                "legal_name": "Probe candidate",
                "evidence_refs": ["probe_src"],
                "signals": [{"signal_code": "S1", "status": "unclear", "score": 0, "evidence_refs": ["probe_src"]}],
            }
        ],
    })
    failed = [issue for issue in issues if issue.severity == "error"]
    return {
        "code": "extraction_schema_probe",
        "status": "failed" if failed else "passed",
        "severity": "error" if failed else "info",
        "message": "Extraction schema probe accepted a minimal valid provider payload." if not failed else "Extraction schema probe failed.",
        "duration_ms": _duration_ms(started_at),
        "details": {"issue_codes": [issue.code for issue in issues]},
        "remediation": "" if not failed else "Repair extraction schema gates before running live Radar.",
    }


def _dadata_probe() -> dict[str, Any]:
    started_at = perf_counter()
    query = effective_runtime_env(dotenv_path=Path.cwd() / ".env").get("POWER_WEB_OS_DADATA_TEST_QUERY") or "1651025328"
    provider = DaDataCompanyRegistryProvider(env_path=Path.cwd() / ".env", timeout_seconds=8)
    try:
        result = provider.lookup_companies(
            CompanyLookupRequest(
                radar_id="toir-quick-live",
                task_id="preflight-dadata-probe",
                stage="qualification_discovery",
                subject_id="preflight",
                query=query,
                source_id="dadata_registry",
                source_label="DaData company registry",
                source_reference="company_registry:dadata",
                lookup_terms=[query],
                limit=3,
            )
        )
    except Exception as error:
        return {
            "code": "dadata_probe",
            "status": "failed",
            "severity": "error",
            "message": str(error),
            "duration_ms": _duration_ms(started_at),
            "details": {"error_type": error.__class__.__name__, "query": query},
            "remediation": "Check POWER_WEB_OS_DADATA_MODE, DADATA_API_KEY, DADATA_SECRET_KEY, and DaData availability.",
        }
    outcome = result.outcomes[0] if result.outcomes else None
    passed = bool(result.observations)
    return {
        "code": "dadata_probe",
        "status": "passed" if passed else "failed",
        "severity": "info" if passed else "error",
        "message": f"DaData returned {len(result.observations)} company observations." if passed else "DaData probe returned no company observations.",
        "duration_ms": _duration_ms(started_at),
        "details": {
            "query": query,
            "observation_count": len(result.observations),
            "outcome": outcome.outcome if outcome else "missing_outcome",
            "reason": outcome.reason if outcome else "",
        },
        "remediation": "" if passed else "Check POWER_WEB_OS_DADATA_MODE, DADATA_API_KEY, DADATA_SECRET_KEY, and DaData availability.",
    }


def _openrouter_probe(*, probe: str, radar_id: str) -> dict[str, Any]:
    started_at = perf_counter()
    runtime = build_effective_runtime_config_report(component="cli", dotenv_path=Path.cwd() / ".env").to_payload()
    retrieval = runtime.get("config", {}).get("retrieval", {})
    if probe == "openrouter-perplexity" and (
        retrieval.get("provider") != "openrouter_perplexity"
        or retrieval.get("openrouter_web_search_engine") != "perplexity"
    ):
        return {
            "code": "openrouter_perplexity_probe",
            "status": "failed",
            "severity": "error",
            "message": "OpenRouter Perplexity probe requested but effective retrieval config is not Perplexity.",
            "duration_ms": _duration_ms(started_at),
            "details": {"retrieval": retrieval},
            "remediation": "Set POWER_WEB_OS_RADAR_WEB_RETRIEVAL_PROVIDER=openrouter_perplexity and POWER_WEB_OS_OPENROUTER_WEB_SEARCH_ENGINE=perplexity.",
        }
    provider = OpenRouterWebSearchProvider(env_path=Path.cwd() / ".env", timeout_seconds=30)
    try:
        result = provider.run_search_plan(
            radar={"radar_id": radar_id, "name": "Radar preflight probe", "intent_signals": []},
            search_plan=RadarSearchPlan(
                radar_id=radar_id,
                queries=[
                    RadarSearchQuery(
                        query_id="preflight-openrouter-web",
                        query="СИБУР официальный сайт производственные предприятия",
                        purpose="Bounded preflight retrieval probe.",
                        expected_evidence=["official or retrieved source"],
                        stage="qualification_discovery",
                        subject_type="qualification",
                        subject_id="preflight",
                    )
                ],
            ),
        )
    except Exception as error:
        return {
            "code": f"{probe}_probe".replace("-", "_"),
            "status": "failed",
            "severity": "error",
            "message": str(error),
            "duration_ms": _duration_ms(started_at),
            "details": {"error_type": error.__class__.__name__, "retrieval": retrieval},
            "remediation": "Check OPENROUTER_API_KEY, model, web mode, retrieval provider, and OpenRouter availability.",
        }
    passed = bool(result.sources or result.provider_metadata.get("retrieved_source_count"))
    return {
        "code": f"{probe}_probe".replace("-", "_"),
        "status": "passed" if passed else "failed",
        "severity": "info" if passed else "error",
        "message": "OpenRouter retrieval probe returned source material." if passed else "OpenRouter retrieval probe returned no source material.",
        "duration_ms": _duration_ms(started_at),
        "details": {
            "source_count": len(result.sources),
            "retrieved_source_count": result.provider_metadata.get("retrieved_source_count", 0),
            "model": result.provider_metadata.get("model"),
            "web_mode": result.provider_metadata.get("web_mode"),
            "retrieval_provider": result.provider_metadata.get("retrieval_provider"),
            "retrieval_engine": result.provider_metadata.get("retrieval_engine"),
        },
        "remediation": "" if passed else "Check OPENROUTER_API_KEY, model, web mode, retrieval provider, and OpenRouter web-search availability.",
    }


def _duration_ms(started_at: float) -> int:
    return int((perf_counter() - started_at) * 1000)
