"""Connector-profile checks for Radar execution preflight."""

from __future__ import annotations

from typing import Any, Mapping

from power_web_os.application.connector_profiles import ConnectorProfileRegistry
from power_web_os.application.radar_preflight import RadarPreflightCheckResult


def connector_profile_checks(
    definition_payload: dict[str, Any],
    *,
    connector_profile_registry: ConnectorProfileRegistry,
    environment: Mapping[str, str],
    require_credentials: bool,
) -> list[RadarPreflightCheckResult]:
    checks: list[RadarPreflightCheckResult] = []
    registry_issues = connector_profile_registry.issues()
    for profile_id, issues in registry_issues.items():
        for issue in issues:
            if issue.severity == "error":
                checks.append(_failed(
                    "connector_profile_valid",
                    issue.message,
                    details={"profile_id": profile_id, **issue.details},
                    remediation="Fix the connector profile before using it in Radar source policy.",
                ))
            else:
                checks.append(RadarPreflightCheckResult(
                    code="connector_profile_valid",
                    status="warning",
                    severity="warning",
                    message=issue.message,
                    details={"profile_id": profile_id, **issue.details},
                    remediation="Review the connector profile warning before long live runs.",
                ))
    for source in _global_sources(definition_payload):
        checks.extend(_source_connector_checks(
            source=source,
            connector_profile_registry=connector_profile_registry,
            environment=environment,
            require_credentials=require_credentials,
        ))
    return checks


def _source_connector_checks(
    *,
    source: dict[str, Any],
    connector_profile_registry: ConnectorProfileRegistry,
    environment: Mapping[str, str],
    require_credentials: bool,
) -> list[RadarPreflightCheckResult]:
    source_id = str(source.get("source_id") or source.get("reference") or "")
    capability = connector_profile_registry.capability_for_source(source)
    if capability is None:
        return [_failed(
            "source_connector_profile_resolved",
            f"Source {source_id} does not resolve to a connector profile.",
            details={"source_id": source_id, "connector_profile_id": str(source.get("connector_profile_id") or "")},
            remediation="Add connector_profile_id to the source or add a matching connector profile config.",
        )]

    checks = [_passed(
        "source_connector_profile_resolved",
        f"Source {source_id} resolves to connector profile {capability.profile_id}.",
        details={"source_id": source_id, "connector_profile_id": capability.profile_id},
    )]
    source_type = str(source.get("source_type") or "")
    if source_type and capability.source_type and source_type != capability.source_type:
        checks.append(_failed(
            "source_connector_profile_mismatch",
            f"Source {source_id} source_type does not match connector profile {capability.profile_id}.",
            details={"source_id": source_id, "source_type": source_type, "profile_source_type": capability.source_type},
            remediation="Choose a connector profile whose source_type matches the source definition.",
        ))
    else:
        checks.append(_passed(
            "source_connector_capability_compiled",
            f"Source {source_id} compiled connector capability {capability.profile_id}.",
            details={"source_id": source_id, "capability": _safe_capability_payload(capability)},
        ))
    checks.append(_credential_check(capability=capability, environment=environment, require_credentials=require_credentials))
    return checks


def _credential_check(
    *,
    capability: Any,
    environment: Mapping[str, str],
    require_credentials: bool,
) -> RadarPreflightCheckResult:
    missing = [name for name in capability.credential_env_vars if not str(environment.get(name) or "").strip()]
    if not missing:
        return _passed(
            "connector_credentials_present",
            f"Connector profile {capability.profile_id} has required credentials or does not need credentials.",
            details={"connector_profile_id": capability.profile_id, "credential_count": len(capability.credential_env_vars)},
        )
    if require_credentials:
        return _failed(
            "connector_credentials_present",
            f"Connector profile {capability.profile_id} is missing required credentials.",
            details={"connector_profile_id": capability.profile_id, "missing_credential_count": len(missing)},
            remediation="Set the missing connector credentials in local .env or use recorded/offline mode before live execution.",
        )
    return RadarPreflightCheckResult(
        code="connector_credentials_present",
        status="skipped",
        severity="info",
        message=f"Connector profile {capability.profile_id} credentials are not present in the current environment.",
        details={"connector_profile_id": capability.profile_id, "missing_credential_count": len(missing)},
        remediation="This is acceptable for recorded/static checks; set credentials before live provider execution.",
    )


def _safe_capability_payload(capability: Any) -> dict[str, Any]:
    payload = capability.to_payload()
    payload.pop("credential_env_vars", None)
    payload["credential_count"] = len(capability.credential_env_vars)
    return payload


def _global_sources(payload: dict[str, Any]) -> list[dict[str, Any]]:
    policy = payload.get("global_search_policy")
    if not isinstance(policy, dict):
        return []
    sources = policy.get("sources")
    return [dict(item) for item in sources if isinstance(item, dict)] if isinstance(sources, list) else []


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
