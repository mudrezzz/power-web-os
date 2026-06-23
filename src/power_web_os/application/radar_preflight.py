"""Fast preflight checks for live Radar execution readiness.

The preflight service is intentionally application-only. It inspects persisted
Radar definitions, source policy references, source-provider availability, and
recorded provider-output shapes before a developer pays for a long live run.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Iterable, Literal

from power_web_os.application.ports import RadarDefinitionRepository

RadarPreflightCheckStatus = Literal["passed", "failed", "warning", "skipped"]
RadarPreflightSeverity = Literal["info", "warning", "error"]


@dataclass(frozen=True, slots=True)
class RadarPreflightCheckResult:
    code: str
    status: RadarPreflightCheckStatus
    severity: RadarPreflightSeverity
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
class RadarPreflightReport:
    radar_id: str
    definition_id: str | None
    definition_version: str | None
    ready_for_live_run: bool
    checks: tuple[RadarPreflightCheckResult, ...]
    summary: dict[str, Any]

    def to_payload(self) -> dict[str, Any]:
        return {
            "artifact_type": "radar_execution_preflight_report",
            "radar_id": self.radar_id,
            "definition_id": self.definition_id,
            "definition_version": self.definition_version,
            "ready_for_live_run": self.ready_for_live_run,
            "summary": self.summary,
            "checks": [check.to_payload() for check in self.checks],
        }


class RadarExecutionPreflightService:
    """Run fast readiness checks before executing a live Radar job."""

    def __init__(
        self,
        *,
        definition_repository: RadarDefinitionRepository,
        runtime_definition_provider: Callable[[], dict[str, Any]],
        company_registry_provider_ids: Iterable[str] = (),
    ) -> None:
        self._definition_repository = definition_repository
        self._runtime_definition_provider = runtime_definition_provider
        self._company_registry_provider_ids = {str(item) for item in company_registry_provider_ids if str(item)}

    def run(self, *, radar_id: str, profile: Literal["static", "recorded"] = "recorded") -> RadarPreflightReport:
        checks: list[RadarPreflightCheckResult] = []
        active_definition = self._definition_repository.get_active(radar_id)
        if active_definition is None:
            checks.append(_failed(
                "active_definition_available",
                f"No active Radar definition found for {radar_id}.",
                remediation="Seed the Radar catalog before running preflight.",
            ))
            return _report(radar_id=radar_id, definition_id=None, definition_version=None, checks=checks)

        payload = dict(active_definition.definition_payload)
        checks.append(_passed(
            "active_definition_available",
            f"Active definition {active_definition.definition_id} is available.",
            details={"definition_version": active_definition.definition_version},
        ))
        checks.append(self._runtime_definition_check(payload))
        checks.extend(_source_policy_checks(payload, company_registry_provider_ids=self._company_registry_provider_ids))
        if profile == "recorded":
            checks.extend(recorded_provider_fixture_checks(payload))
        else:
            checks.append(_skipped(
                "recorded_fixture_gate",
                "Recorded provider-output fixture checks were skipped for static profile.",
            ))
        return _report(
            radar_id=radar_id,
            definition_id=active_definition.definition_id,
            definition_version=active_definition.definition_version,
            checks=checks,
        )

    def _runtime_definition_check(self, active_payload: dict[str, Any]) -> RadarPreflightCheckResult:
        runtime_payload = self._runtime_definition_provider()
        active_fingerprint = _definition_fingerprint(active_payload)
        runtime_fingerprint = _definition_fingerprint(runtime_payload)
        if active_fingerprint == runtime_fingerprint:
            return _passed(
                "definition_runtime_mismatch",
                "Runtime Radar definition matches the active persisted definition.",
                details={"fingerprint": active_fingerprint},
            )
        return _failed(
            "definition_runtime_mismatch",
            "Runtime Radar definition does not match the active persisted definition.",
            details={
                "active_definition": active_fingerprint,
                "runtime_definition": runtime_fingerprint,
            },
            remediation=(
                "Wire persisted live execution to load the active RadarDefinitionRecord "
                "instead of using the legacy hardcoded live mini definition."
            ),
        )


def recorded_provider_fixture_checks(radar_definition: dict[str, Any]) -> list[RadarPreflightCheckResult]:
    """Verify that known bad provider outputs fail explicit gates.

    These checks are intentionally positive when malformed fixtures are rejected.
    They keep the test suite green while proving the current failure modes are
    represented by fast diagnostics.
    """

    _ = radar_definition
    fixtures = {
        "prose_first_output": (
            "Here is the result:\n{\"sources\": [], \"candidates\": []}",
            {"extraction_schema_invalid"},
        ),
        "dict_candidates": (
            {"sources": [], "candidates": {"legal_name": "Candidate A"}},
            {"extraction_schema_invalid"},
        ),
        "dict_source_outcomes": (
            {"sources": [], "candidates": [], "source_outcomes": {"source_ref": "src_1"}},
            {"extraction_schema_invalid"},
        ),
        "unknown_source_ref": (
            {
                "sources": [{"evidence_ref": "src_1", "title": "A", "url": "https://example.test", "snippet": "A"}],
                "candidates": [{"legal_name": "Candidate A", "evidence_refs": ["missing_src"]}],
            },
            {"evidence_linking_failed"},
        ),
        "numeric_source_ref": (
            {
                "sources": [{"evidence_ref": "src_1", "title": "A", "url": "https://example.test", "snippet": "A"}],
                "candidates": [{"legal_name": "Candidate A", "signals": [{"signal_code": "S1", "evidence_refs": [42]}]}],
            },
            {"evidence_linking_failed"},
        ),
        "not_searched_zero_score": (
            {
                "sources": [],
                "candidates": [
                    {
                        "legal_name": "Candidate A",
                        "signals": [
                            {
                                "signal_code": "S1",
                                "status": "not_observed",
                                "search_status": "not_searched_budget_limited",
                                "score": 0,
                            }
                        ],
                    }
                ],
            },
            {"invalid_zero_score_projection"},
        ),
    }
    results: list[RadarPreflightCheckResult] = []
    for fixture_name, (payload, expected_codes) in fixtures.items():
        issues = validate_provider_output_fixture(payload)
        issue_codes = {issue.code for issue in issues}
        missing = sorted(expected_codes - issue_codes)
        if missing:
            results.append(_failed(
                "recorded_fixture_gate",
                f"Malformed fixture {fixture_name} was not rejected by expected gates.",
                details={"fixture": fixture_name, "missing_codes": missing, "actual_codes": sorted(issue_codes)},
                remediation="Tighten provider-output preflight validation before running live Radar.",
            ))
        else:
            results.append(_passed(
                "recorded_fixture_gate",
                f"Malformed fixture {fixture_name} is rejected by preflight gates.",
                details={"fixture": fixture_name, "issue_codes": sorted(issue_codes)},
            ))
    return results


def validate_provider_output_fixture(payload: Any) -> tuple[RadarPreflightCheckResult, ...]:
    checks: list[RadarPreflightCheckResult] = []
    if isinstance(payload, str):
        stripped = payload.lstrip()
        if not stripped.startswith("{"):
            checks.append(_failed(
                "extraction_schema_invalid",
                "Provider output contains prose before the JSON object.",
                details={"payload_excerpt": stripped[:160]},
                remediation="Require strict JSON output for extraction fixtures and live provider prompts.",
            ))
        try:
            payload = json.loads(stripped[stripped.find("{"):])
        except (ValueError, TypeError):
            return tuple(checks)
    if not isinstance(payload, dict):
        return (_failed(
            "extraction_schema_invalid",
            "Provider output must be a JSON object.",
            details={"payload_type": type(payload).__name__},
            remediation="Reject non-object extraction responses before normalization.",
        ),)
    checks.extend(_shape_checks(payload))
    checks.extend(_evidence_linking_checks(payload))
    checks.extend(_zero_score_projection_checks(payload))
    return tuple(checks)


def _shape_checks(payload: dict[str, Any]) -> list[RadarPreflightCheckResult]:
    checks: list[RadarPreflightCheckResult] = []
    for field_name in ["sources", "candidates", "candidate_observations", "source_outcomes"]:
        if field_name in payload and not isinstance(payload[field_name], list):
            checks.append(_failed(
                "extraction_schema_invalid",
                f"Provider output field {field_name} must be a list.",
                details={"field": field_name, "actual_type": type(payload[field_name]).__name__},
                remediation="Keep extraction schemas strict and reject dict/list mismatches before normalization.",
            ))
    return checks


def _evidence_linking_checks(payload: dict[str, Any]) -> list[RadarPreflightCheckResult]:
    source_refs = {
        ref for source in _list(payload.get("sources"))
        for ref in [_source_ref(source)]
        if ref
    }
    bad_refs: list[dict[str, str]] = []
    for candidate in [*_list(payload.get("candidates")), *_list(payload.get("candidate_observations"))]:
        for ref in _candidate_source_refs(candidate):
            if not isinstance(ref, str) or not ref.strip():
                bad_refs.append({"source_ref": str(ref), "reason": "non_string_or_empty"})
            elif ref not in source_refs:
                bad_refs.append({"source_ref": ref, "reason": "unknown_source_ref"})
    if not bad_refs:
        return []
    return [_failed(
        "evidence_linking_failed",
        "Provider output references evidence refs that cannot be linked to normalized sources.",
        details={"invalid_refs": bad_refs[:20], "known_source_refs": sorted(source_refs)},
        remediation="Reject or repair evidence refs before product projection so sources do not collapse silently.",
    )]


def _zero_score_projection_checks(payload: dict[str, Any]) -> list[RadarPreflightCheckResult]:
    invalid: list[dict[str, str]] = []
    for candidate in [*_list(payload.get("candidates")), *_list(payload.get("candidate_observations"))]:
        candidate_name = str(candidate.get("legal_name") or candidate.get("name") or "")
        for signal in _list(candidate.get("signals")):
            search_status = str(signal.get("search_status") or "")
            status = str(signal.get("status") or "")
            if search_status.startswith("not_searched") and status == "not_observed":
                invalid.append({
                    "candidate": candidate_name,
                    "signal_code": str(signal.get("signal_code") or signal.get("code") or ""),
                    "search_status": search_status,
                })
    if not invalid:
        return []
    return [_failed(
        "invalid_zero_score_projection",
        "Unsearched signal output is projected as normal not_observed zero score.",
        details={"signals": invalid},
        remediation="Represent unsearched signals as review-needed/not_searched states, not searched-negative evidence.",
    )]


def _source_policy_checks(
    definition_payload: dict[str, Any],
    *,
    company_registry_provider_ids: set[str],
) -> list[RadarPreflightCheckResult]:
    checks: list[RadarPreflightCheckResult] = []
    sources = _global_sources(definition_payload)
    source_ids = {str(source.get("source_id") or source.get("reference") or "") for source in sources if isinstance(source, dict)}
    referenced_ids = _referenced_source_ids(definition_payload)
    unknown_ids = sorted(source_id for source_id in referenced_ids if source_id and source_id not in source_ids)
    if unknown_ids:
        checks.append(_failed(
            "source_base_not_executable",
            "Source policy references unknown source ids.",
            details={"unknown_source_ids": unknown_ids, "global_source_ids": sorted(source_ids)},
            remediation="Add missing sources to global_search_policy.sources or remove invalid source ids from rules/signals.",
        ))
    else:
        checks.append(_passed(
            "source_base_not_executable",
            "All source policy source ids resolve to configured global sources.",
            details={"global_source_ids": sorted(source_ids), "referenced_source_ids": sorted(referenced_ids)},
        ))

    for source in sources:
        source_type = str(source.get("source_type") or "")
        source_id = str(source.get("source_id") or source.get("reference") or "")
        if source_type == "company_registry":
            provider_id = _provider_id(source)
            if provider_id in company_registry_provider_ids:
                checks.append(_passed(
                    "company_registry_provider_available",
                    f"Company registry source {source_id} can be executed by provider {provider_id}.",
                    details={"source_id": source_id, "provider_id": provider_id},
                ))
            else:
                checks.append(_failed(
                    "company_registry_provider_available",
                    f"Company registry source {source_id} has no executable provider.",
                    details={"source_id": source_id, "provider_id": provider_id, "available_provider_ids": sorted(company_registry_provider_ids)},
                    remediation="Configure DaData recorded/live provider before running a Radar that selects this source.",
                ))
        elif source_type in {"search_engine", "url"}:
            checks.append(_passed(
                "source_base_executable",
                f"Source {source_id} has supported type {source_type}.",
                details={"source_id": source_id, "source_type": source_type},
            ))
        else:
            checks.append(_failed(
                "source_base_not_executable",
                f"Source {source_id} has unsupported source_type {source_type}.",
                details={"source_id": source_id, "source_type": source_type},
                remediation="Map this source to a supported provider type before live execution.",
            ))
    return checks


def _definition_fingerprint(payload: dict[str, Any]) -> dict[str, Any]:
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    qualification_rules = _qualification_rules(payload)
    signals = _intent_signals(payload)
    return {
        "definition_id": str(payload.get("definition_id") or ""),
        "radar_id": str(payload.get("radar_id") or ""),
        "name": str(payload.get("name") or metadata.get("name") or ""),
        "global_source_ids": sorted(str(source.get("source_id") or source.get("reference") or "") for source in _global_sources(payload)),
        "qualification_rule_ids": sorted(str(rule.get("rule_id") or rule.get("code") or "") for rule in qualification_rules),
        "signal_codes": sorted(str(signal.get("code") or signal.get("signal_id") or "") for signal in signals),
    }


def _qualification_rules(payload: dict[str, Any]) -> list[dict[str, Any]]:
    direct = payload.get("qualification_criteria")
    if isinstance(direct, list):
        return [dict(item) for item in direct if isinstance(item, dict)]
    group = payload.get("account_qualification", {}).get("rule_group") if isinstance(payload.get("account_qualification"), dict) else {}
    rules = group.get("rules") if isinstance(group, dict) else []
    return [dict(item) for item in rules if isinstance(item, dict)]


def _intent_signals(payload: dict[str, Any]) -> list[dict[str, Any]]:
    signals = payload.get("intent_signals")
    return [dict(item) for item in signals if isinstance(item, dict)] if isinstance(signals, list) else []


def _global_sources(payload: dict[str, Any]) -> list[dict[str, Any]]:
    policy = payload.get("global_search_policy")
    if not isinstance(policy, dict):
        return []
    sources = policy.get("sources")
    return [dict(item) for item in sources if isinstance(item, dict)] if isinstance(sources, list) else []


def _referenced_source_ids(payload: dict[str, Any]) -> set[str]:
    refs: set[str] = set()
    for rule in _qualification_rules(payload):
        refs.update(_source_ids_from_policy(rule.get("source_policy")))
    for signal in _intent_signals(payload):
        trigger_group = signal.get("trigger_rule_group")
        if isinstance(trigger_group, dict):
            for rule in _list(trigger_group.get("rules")):
                refs.update(_source_ids_from_policy(rule.get("source_policy")))
        refs.update(_source_ids_from_policy(signal.get("source_policy")))
    return refs


def _source_ids_from_policy(policy: Any) -> set[str]:
    if not isinstance(policy, dict):
        return set()
    return {str(item) for item in policy.get("source_ids", []) if str(item).strip()}


def _provider_id(source: dict[str, Any]) -> str:
    if source.get("provider_id"):
        return str(source["provider_id"])
    reference = str(source.get("reference") or "")
    if ":" in reference:
        return reference.split(":")[-1]
    source_id = str(source.get("source_id") or "")
    return "dadata" if "dadata" in source_id.lower() else source_id


def _candidate_source_refs(candidate: dict[str, Any]) -> list[Any]:
    refs: list[Any] = []
    for ref in candidate.get("evidence_refs", []):
        refs.append(ref)
    for section_name in ["qualification", "signals"]:
        for item in _list(candidate.get(section_name)):
            refs.extend(item.get("evidence_refs", []) if isinstance(item.get("evidence_refs"), list) else [])
            for finding in _list(item.get("evidence_findings")):
                refs.append(finding.get("source_ref") or finding.get("evidence_ref"))
            for usage in _list(item.get("source_usages")):
                refs.append(usage.get("source_ref"))
    return refs


def _source_ref(source: dict[str, Any]) -> str:
    return str(source.get("evidence_ref") or source.get("source_ref") or source.get("id") or "")


def _list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _report(
    *,
    radar_id: str,
    definition_id: str | None,
    definition_version: str | None,
    checks: list[RadarPreflightCheckResult],
) -> RadarPreflightReport:
    error_count = sum(1 for check in checks if check.severity == "error" and check.status == "failed")
    warning_count = sum(1 for check in checks if check.severity == "warning" and check.status in {"failed", "warning"})
    passed_count = sum(1 for check in checks if check.status == "passed")
    return RadarPreflightReport(
        radar_id=radar_id,
        definition_id=definition_id,
        definition_version=definition_version,
        ready_for_live_run=error_count == 0,
        checks=tuple(checks),
        summary={
            "check_count": len(checks),
            "passed_count": passed_count,
            "error_count": error_count,
            "warning_count": warning_count,
            "failed_codes": sorted({check.code for check in checks if check.status == "failed"}),
        },
    )


def _passed(code: str, message: str, *, details: dict[str, Any] | None = None) -> RadarPreflightCheckResult:
    return RadarPreflightCheckResult(code=code, status="passed", severity="info", message=message, details=details or {})


def _failed(
    code: str,
    message: str,
    *,
    details: dict[str, Any] | None = None,
    remediation: str = "",
) -> RadarPreflightCheckResult:
    return RadarPreflightCheckResult(
        code=code,
        status="failed",
        severity="error",
        message=message,
        details=details or {},
        remediation=remediation,
    )


def _skipped(code: str, message: str) -> RadarPreflightCheckResult:
    return RadarPreflightCheckResult(code=code, status="skipped", severity="info", message=message)
