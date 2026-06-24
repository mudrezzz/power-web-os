"""Connector profile registry and source capability compiler.

External connector profiles are product-facing descriptions of data sources.
This module compiles those descriptions into internal Radar capability cards
without making connector authors know Radar pipeline stage names.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping


INTERNAL_STAGE_NAMES = {
    "qualification_discovery",
    "candidate_universe_discovery",
    "source_probe",
    "qualification_gate",
    "coverage_check",
    "signal_search",
    "normalization_result",
    "validation_result",
}

PROFILE_REQUIRED_FIELDS = {
    "id",
    "display_name",
    "description",
    "good_inputs",
    "bad_inputs",
    "expected_facts",
    "limitations",
    "credential_env_vars",
    "runtime_provider_id",
    "source_type",
}


@dataclass(frozen=True, slots=True)
class ConnectorProfileIssue:
    code: str
    message: str
    severity: str = "error"
    details: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "details": self.details,
        }


@dataclass(frozen=True, slots=True)
class ConnectorProfile:
    id: str
    display_name: str
    description: str
    source_type: str
    runtime_provider_id: str
    good_inputs: tuple[str, ...] = ()
    bad_inputs: tuple[str, ...] = ()
    expected_facts: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()
    credential_env_vars: tuple[str, ...] = ()
    aliases: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "display_name": self.display_name,
            "description": self.description,
            "source_type": self.source_type,
            "runtime_provider_id": self.runtime_provider_id,
            "good_inputs": list(self.good_inputs),
            "bad_inputs": list(self.bad_inputs),
            "expected_facts": list(self.expected_facts),
            "limitations": list(self.limitations),
            "credential_env_vars": list(self.credential_env_vars),
            "aliases": list(self.aliases),
        }


@dataclass(frozen=True, slots=True)
class ConnectorCapabilityCard:
    profile_id: str
    display_name: str
    source_type: str
    runtime_provider_id: str
    supports_lookup: bool
    supports_broad_discovery: bool
    supports_identity: bool
    supports_enrichment: bool
    supports_coverage: bool
    supports_signal_evidence: bool
    requires_concrete_input: bool
    required_input_kinds: tuple[str, ...] = ()
    returned_fact_kinds: tuple[str, ...] = ()
    credential_env_vars: tuple[str, ...] = ()
    useful_result_criteria: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "display_name": self.display_name,
            "source_type": self.source_type,
            "runtime_provider_id": self.runtime_provider_id,
            "supports_lookup": self.supports_lookup,
            "supports_broad_discovery": self.supports_broad_discovery,
            "supports_identity": self.supports_identity,
            "supports_enrichment": self.supports_enrichment,
            "supports_coverage": self.supports_coverage,
            "supports_signal_evidence": self.supports_signal_evidence,
            "requires_concrete_input": self.requires_concrete_input,
            "required_input_kinds": list(self.required_input_kinds),
            "returned_fact_kinds": list(self.returned_fact_kinds),
            "credential_env_vars": list(self.credential_env_vars),
            "useful_result_criteria": list(self.useful_result_criteria),
        }


class ConnectorProfileRegistry:
    """Load connector profiles and resolve source definitions to capabilities."""

    def __init__(
        self,
        *,
        profiles: Mapping[str, ConnectorProfile] | None = None,
        issues: Mapping[str, tuple[ConnectorProfileIssue, ...]] | None = None,
    ) -> None:
        self._profiles = dict(profiles or {})
        self._issues = dict(issues or {})
        self._capabilities = {
            profile_id: compile_connector_capability(profile)
            for profile_id, profile in self._profiles.items()
            if not [issue for issue in self._issues.get(profile_id, ()) if issue.severity == "error"]
        }
        self._aliases: dict[str, str] = {}
        for profile in self._profiles.values():
            for alias in {profile.id, profile.runtime_provider_id, *profile.aliases}:
                if alias:
                    self._aliases[str(alias)] = profile.id

    @classmethod
    def from_directory(cls, directory: Path) -> "ConnectorProfileRegistry":
        profiles: dict[str, ConnectorProfile] = {}
        issues: dict[str, tuple[ConnectorProfileIssue, ...]] = {}
        if not directory.exists():
            return cls(issues={"__registry__": (ConnectorProfileIssue(
                code="connector_profile_directory_missing",
                message=f"Connector profile directory does not exist: {directory}",
            ),)})
        for path in sorted(directory.glob("*.json")):
            profile, profile_issues = load_connector_profile(path)
            profile_id = profile.id if profile is not None else path.stem
            if profile is not None:
                profiles[profile.id] = profile
            issues[profile_id] = tuple(profile_issues)
        return cls(profiles=profiles, issues=issues)

    @classmethod
    def from_profiles(cls, profiles: list[ConnectorProfile]) -> "ConnectorProfileRegistry":
        issues = {profile.id: tuple(validate_connector_profile(profile)) for profile in profiles}
        return cls(profiles={profile.id: profile for profile in profiles}, issues=issues)

    def profiles(self) -> tuple[ConnectorProfile, ...]:
        return tuple(self._profiles.values())

    def issues(self) -> dict[str, tuple[ConnectorProfileIssue, ...]]:
        return dict(self._issues)

    def capability(self, profile_id: str) -> ConnectorCapabilityCard | None:
        return self._capabilities.get(self._aliases.get(profile_id, profile_id))

    def capability_for_source(self, source: Mapping[str, Any]) -> ConnectorCapabilityCard | None:
        for candidate in _source_profile_candidates(source):
            capability = self.capability(candidate)
            if capability is not None:
                return capability
        return None

    def profile_id_for_source(self, source: Mapping[str, Any]) -> str:
        capability = self.capability_for_source(source)
        return capability.profile_id if capability else ""


def default_connector_profile_registry() -> ConnectorProfileRegistry:
    return ConnectorProfileRegistry.from_directory(_default_connector_profile_dir())


def load_connector_profile(path: Path) -> tuple[ConnectorProfile | None, tuple[ConnectorProfileIssue, ...]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, (ConnectorProfileIssue(
            code="connector_profile_invalid_json",
            message=f"Connector profile {path.name} is not valid JSON.",
            details={"error": str(exc)},
        ),)
    if not isinstance(payload, dict):
        return None, (ConnectorProfileIssue(
            code="connector_profile_invalid_shape",
            message=f"Connector profile {path.name} must be a JSON object.",
        ),)
    profile = ConnectorProfile(
        id=str(payload.get("id") or path.stem),
        display_name=str(payload.get("display_name") or ""),
        description=str(payload.get("description") or ""),
        source_type=str(payload.get("source_type") or ""),
        runtime_provider_id=str(payload.get("runtime_provider_id") or ""),
        good_inputs=tuple(_string_list(payload.get("good_inputs"))),
        bad_inputs=tuple(_string_list(payload.get("bad_inputs"))),
        expected_facts=tuple(_string_list(payload.get("expected_facts"))),
        limitations=tuple(_string_list(payload.get("limitations"))),
        credential_env_vars=tuple(_string_list(payload.get("credential_env_vars"))),
        aliases=tuple(_string_list(payload.get("aliases"))),
    )
    return profile, tuple(validate_connector_profile(profile, raw_payload=payload))


def validate_connector_profile(
    profile: ConnectorProfile,
    *,
    raw_payload: Mapping[str, Any] | None = None,
) -> list[ConnectorProfileIssue]:
    issues: list[ConnectorProfileIssue] = []
    if raw_payload is not None:
        missing = sorted(field for field in PROFILE_REQUIRED_FIELDS if field not in raw_payload)
        if missing:
            issues.append(ConnectorProfileIssue(
                code="connector_profile_missing_fields",
                message=f"Connector profile {profile.id} misses required fields.",
                details={"missing_fields": missing},
            ))
    if not re.fullmatch(r"[a-z0-9][a-z0-9_\-]{1,80}", profile.id):
        issues.append(ConnectorProfileIssue(
            code="connector_profile_invalid_id",
            message=f"Connector profile id {profile.id!r} must be lowercase letters, digits, hyphen, or underscore.",
        ))
    if not profile.display_name.strip() or not profile.description.strip():
        issues.append(ConnectorProfileIssue(
            code="connector_profile_missing_description",
            message=f"Connector profile {profile.id} needs display_name and description.",
        ))
    serialized = json.dumps(profile.to_payload(), ensure_ascii=False).lower()
    forbidden = sorted(name for name in INTERNAL_STAGE_NAMES if name in serialized)
    if forbidden:
        issues.append(ConnectorProfileIssue(
            code="connector_profile_uses_internal_stage_names",
            message=f"Connector profile {profile.id} must not reference internal Radar stage names.",
            details={"stage_names": forbidden},
        ))
    return issues


def compile_connector_capability(profile: ConnectorProfile) -> ConnectorCapabilityCard:
    text = _profile_text(profile)
    positive_text = " ".join([
        profile.id,
        profile.display_name,
        profile.description,
        profile.source_type,
        profile.runtime_provider_id,
        *profile.good_inputs,
        *profile.expected_facts,
    ]).lower()
    source_type = profile.source_type
    supports_lookup = _has_any(positive_text, ["lookup", "registry", "inn", "ogrn", "company facts", "legal entity"])
    supports_broad = _has_any(positive_text, ["broad", "open web", "web search", "enumerat", "candidate universe", "find companies", "coverage"])
    supports_identity = _has_any(text, ["identity", "legal entity", "inn", "ogrn", "registry", "company"])
    supports_enrichment = _has_any(text, ["enrichment", "address", "okved", "status", "registry facts"])
    supports_coverage = _has_any(text, ["coverage", "source", "citation", "snippet", "web page", "official site"])
    supports_signal = _has_any(text, ["signal", "intent", "event", "news", "current evidence", "web evidence"])
    requires_concrete = _has_any(text, ["concrete", "not broad", "bad input: broad", "broad natural-language"]) or (
        source_type == "company_registry" and not supports_broad
    )
    return ConnectorCapabilityCard(
        profile_id=profile.id,
        display_name=profile.display_name,
        source_type=source_type,
        runtime_provider_id=profile.runtime_provider_id,
        supports_lookup=supports_lookup,
        supports_broad_discovery=supports_broad,
        supports_identity=supports_identity,
        supports_enrichment=supports_enrichment,
        supports_coverage=supports_coverage,
        supports_signal_evidence=supports_signal,
        requires_concrete_input=requires_concrete,
        required_input_kinds=tuple(_required_input_kinds(text)),
        returned_fact_kinds=tuple(_returned_fact_kinds(profile)),
        credential_env_vars=profile.credential_env_vars,
        useful_result_criteria=tuple(_useful_result_criteria(profile, supports_identity=supports_identity, supports_coverage=supports_coverage)),
    )


def _default_connector_profile_dir() -> Path:
    cwd_config = Path.cwd() / "config" / "connectors"
    if cwd_config.exists():
        return cwd_config
    return Path(__file__).resolve().parents[3] / "config" / "connectors"


def _source_profile_candidates(source: Mapping[str, Any]) -> list[str]:
    candidates = [
        str(source.get("connector_profile_id") or ""),
        str(source.get("source_id") or ""),
        str(source.get("provider_id") or ""),
    ]
    reference = str(source.get("reference") or "")
    if ":" in reference:
        candidates.append(reference.split(":")[-1])
    if reference.startswith("http") and "sibur.ru" in reference.lower():
        candidates.append("sibur_site")
    source_id = str(source.get("source_id") or "").lower()
    if "dadata" in source_id:
        candidates.append("dadata_registry")
    if "openrouter" in source_id:
        candidates.append("openrouter_web")
    return [candidate for candidate in candidates if candidate]


def _profile_text(profile: ConnectorProfile) -> str:
    values = [
        profile.id,
        profile.display_name,
        profile.description,
        profile.source_type,
        profile.runtime_provider_id,
        *profile.good_inputs,
        *profile.bad_inputs,
        *profile.expected_facts,
        *profile.limitations,
    ]
    return " ".join(values).lower()


def _required_input_kinds(text: str) -> list[str]:
    result: list[str] = []
    for key, terms in {
        "legal_name": ["legal name", "company name"],
        "inn": ["inn", "инн"],
        "ogrn": ["ogrn", "огрн"],
        "domain": ["domain"],
        "url": ["url"],
        "free_text_query": ["free text", "natural-language", "web search"],
        "candidate_scope": ["candidate scope"],
    }.items():
        if _has_any(text, terms):
            result.append(key)
    return result


def _returned_fact_kinds(profile: ConnectorProfile) -> list[str]:
    facts: list[str] = []
    text = _profile_text(profile)
    for key, terms in {
        "legal_identity": ["legal entity", "legal name", "inn", "ogrn"],
        "registry_status": ["status"],
        "address": ["address"],
        "okved": ["okved"],
        "web_source": ["url", "citation", "snippet", "web page"],
        "signal_evidence": ["signal", "intent", "event", "news"],
    }.items():
        if _has_any(text, terms):
            facts.append(key)
    return facts


def _useful_result_criteria(
    profile: ConnectorProfile,
    *,
    supports_identity: bool,
    supports_coverage: bool,
) -> list[str]:
    if supports_identity:
        return ["resolved legal entity identity", "source-backed registry observation"]
    if supports_coverage:
        return ["retrieved source with URL/title/snippet", "source-backed coverage finding"]
    return [f"source result from {profile.display_name}"]


def _has_any(text: str, terms: list[str]) -> bool:
    return any(term.lower() in text for term in terms)


def _string_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []
