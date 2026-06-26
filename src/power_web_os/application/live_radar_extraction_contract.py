"""Strict extraction-shape checks before live Radar normalization.

Provider adapters may return malformed JSON even when retrieval succeeded. This
module keeps those failures explicit: repair narrow, safe shape mistakes, link
evidence refs where possible, and report unresolved errors before product
projection can turn them into "nothing was found".
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Literal
from urllib.parse import urlparse

from power_web_os.application.live_radar_contracts import QualificationContractIssue


ExtractionIssueSeverity = Literal["warning", "error"]


@dataclass(frozen=True, slots=True)
class ExtractionValidationIssue:
    code: str
    severity: ExtractionIssueSeverity
    path: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)
    remediation: str = ""

    def to_payload(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "path": self.path,
            "message": self.message,
            "details": self.details,
            "remediation": self.remediation,
        }


@dataclass(frozen=True, slots=True)
class ExtractionRepairResult:
    payload: dict[str, Any]
    issues: tuple[ExtractionValidationIssue, ...]
    repaired: bool
    repair_actions: tuple[dict[str, Any], ...] = ()

    @property
    def valid(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)

    @property
    def state(self) -> str:
        if any(issue.code == "evidence_linking_failed" and issue.severity == "error" for issue in self.issues):
            return "evidence_linking_failed"
        if any(issue.code == "extraction_schema_invalid" and issue.severity == "error" for issue in self.issues):
            return "extraction_schema_invalid"
        if self.repaired:
            return "extraction_repair_needed"
        return "accepted"

    def to_metadata(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "state": self.state,
            "repaired": self.repaired,
            "repair_actions": list(self.repair_actions),
            "issues": [issue.to_payload() for issue in self.issues],
        }


def qualification_contract_issues_from_extraction_results(execution_results: dict[str, Any]) -> list[QualificationContractIssue]:
    issues = []
    for item in execution_results.get("extraction_validation_issues", []):
        if not isinstance(item, dict):
            continue
        severity = "error" if str(item.get("severity")) == "error" else "warning"
        code = str(item.get("code") or "extraction_contract_issue")
        path = str(item.get("path") or "extraction")
        message = str(item.get("message") or code)
        issues.append(QualificationContractIssue(
            severity=severity,  # type: ignore[arg-type]
            path=f"extraction.{path}",
            message=f"{code}: {message}",
        ))
    return issues


def extraction_validation_state(issues: list[dict[str, Any]], *, repaired: bool) -> str:
    codes_by_severity = {(str(issue.get("code")), str(issue.get("severity"))) for issue in issues}
    if ("evidence_linking_failed", "error") in codes_by_severity:
        return "evidence_linking_failed"
    if ("extraction_schema_invalid", "error") in codes_by_severity:
        return "extraction_schema_invalid"
    return "extraction_repair_needed" if repaired else "accepted"


def validate_and_repair_extraction_payload(payload: Any) -> ExtractionRepairResult:
    """Return a repaired extraction payload plus explicit validation issues."""

    issues: list[ExtractionValidationIssue] = []
    repair_actions: list[dict[str, Any]] = []
    payload, parsed_repair = _payload_object(payload)
    if parsed_repair is not None:
        issues.append(parsed_repair)
        repair_actions.append({"type": "json_object_extracted", "path": "$"})
    if not isinstance(payload, dict):
        return ExtractionRepairResult(
            payload={},
            issues=(
                _issue(
                    "extraction_schema_invalid",
                    "error",
                    "$",
                    "Provider extraction output must be a JSON object.",
                    details={"payload_type": type(payload).__name__},
                    remediation="Reject non-object extraction responses before normalization.",
                ),
            ),
            repaired=False,
        )

    repaired = dict(payload)
    for field_name in ("sources", "candidates", "candidate_observations", "source_outcomes", "candidate_universe_gaps", "coverage_findings"):
        if field_name not in repaired:
            continue
        value = repaired[field_name]
        if isinstance(value, list):
            repaired_list, list_issues, list_actions = _repair_list_items(field_name, value)
            repaired[field_name] = repaired_list
            issues.extend(list_issues)
            repair_actions.extend(list_actions)
            continue
        if isinstance(value, dict) and _dict_looks_like_single_item(field_name, value):
            repaired[field_name] = [dict(value)]
            issues.append(_issue(
                "extraction_repair_needed",
                "warning",
                f"$.{field_name}",
                f"Provider returned {field_name} as an object; it was wrapped as a one-item list.",
                details={"field": field_name},
                remediation="Keep extraction response fields as arrays even when a task finds one item.",
            ))
            repair_actions.append({"type": "object_wrapped_as_list", "path": f"$.{field_name}"})
            continue
        if isinstance(value, dict):
            collection_items = _repair_dict_collection_items(field_name, value)
            if collection_items:
                repaired[field_name] = collection_items
                issues.append(_issue(
                    "extraction_repair_needed",
                    "warning",
                    f"$.{field_name}",
                    f"Provider returned {field_name} as an object keyed by ids/names; values were converted to a list.",
                    details={"field": field_name, "item_count": len(collection_items)},
                    remediation="Keep extraction response collection fields as arrays.",
                ))
                repair_actions.append({
                    "type": "object_values_wrapped_as_list",
                    "path": f"$.{field_name}",
                    "item_count": len(collection_items),
                })
                continue
        issues.append(_issue(
            "extraction_schema_invalid",
            "error",
            f"$.{field_name}",
            f"Provider output field {field_name} must be a list.",
            details={"field": field_name, "actual_type": type(value).__name__},
            remediation="Reject dict/list mismatches before normalization so product output cannot silently collapse.",
        ))
        repaired[field_name] = []

    source_indexes = _source_indexes(_list(repaired.get("sources")))
    for section_name in ("candidates", "candidate_observations"):
        candidates = _list(repaired.get(section_name))
        repaired_candidates = []
        for index, candidate in enumerate(candidates):
            repaired_candidate, candidate_issues, actions = _reconcile_candidate_refs(
                candidate,
                source_indexes=source_indexes,
                path=f"$.{section_name}[{index}]",
            )
            repaired_candidates.append(repaired_candidate)
            issues.extend(candidate_issues)
            repair_actions.extend(actions)
        if section_name in repaired:
            repaired[section_name] = repaired_candidates

    for section_name in ("candidates", "candidate_observations"):
        candidates = _list(repaired.get(section_name))
        repaired_candidates = []
        for index, candidate in enumerate(candidates):
            repaired_candidate, projection_issues, actions = _repair_invalid_zero_score_projection(
                candidate,
                path=f"$.{section_name}[{index}]",
            )
            repaired_candidates.append(repaired_candidate)
            issues.extend(projection_issues)
            repair_actions.extend(actions)
        if section_name in repaired:
            repaired[section_name] = repaired_candidates

    return ExtractionRepairResult(
        payload=repaired,
        issues=tuple(issues),
        repaired=bool(repair_actions),
        repair_actions=tuple(repair_actions),
    )


def _payload_object(payload: Any) -> tuple[Any, ExtractionValidationIssue | None]:
    if not isinstance(payload, str):
        return payload, None
    stripped = payload.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?", "", stripped).strip()
        stripped = re.sub(r"```$", "", stripped).strip()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        parsed = _single_json_object_from_text(stripped)
    if parsed is None:
        return payload, None
    if stripped and not stripped.startswith("{"):
        return parsed, _issue(
            "extraction_repair_needed",
            "warning",
            "$",
            "Provider output contained prose before the JSON object; the single JSON object was extracted.",
            details={"payload_excerpt": stripped[:160]},
            remediation="Keep provider extraction output as strict JSON without prose.",
        )
    return parsed, None


def _single_json_object_from_text(value: str) -> dict[str, Any] | None:
    decoder = json.JSONDecoder()
    matches: list[dict[str, Any]] = []
    for index, char in enumerate(value):
        if char != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(value[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            matches.append(parsed)
    extraction_like = [
        item for item in matches
        if set(item) & {"sources", "candidates", "candidate_observations", "source_outcomes", "candidate_universe_gaps"}
    ]
    if len(extraction_like) == 1:
        return extraction_like[0]
    return matches[0] if len(matches) == 1 else None


def _dict_looks_like_single_item(field_name: str, value: dict[str, Any]) -> bool:
    expected_keys = {
        "sources": {"evidence_ref", "title", "url", "snippet"},
        "candidates": {"legal_name", "name", "qualification", "signals", "evidence_refs"},
        "candidate_observations": {"legal_name", "name", "qualification", "signals", "evidence_refs"},
        "source_outcomes": {"source_ref", "evidence_ref", "outcome", "reason"},
        "candidate_universe_gaps": {"legal_name", "name", "source_refs", "reason"},
        "coverage_findings": {"summary", "completeness_risk", "warnings"},
    }
    return bool(set(value) & expected_keys.get(field_name, set()))


def _repair_dict_collection_items(field_name: str, value: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for key, item in value.items():
        if not isinstance(item, dict) or not _dict_looks_like_single_item(field_name, item):
            continue
        repaired = dict(item)
        key_text = str(key).strip()
        if field_name == "sources" and key_text:
            repaired.setdefault("evidence_ref", key_text)
        elif field_name in {"candidates", "candidate_observations"} and key_text and not _looks_like_synthetic_key(key_text):
            repaired.setdefault("legal_name", key_text)
        elif field_name == "source_outcomes" and key_text:
            repaired.setdefault("source_ref", key_text)
        items.append(repaired)
    return items


def _repair_list_items(
    field_name: str,
    value: list[Any],
) -> tuple[list[dict[str, Any]], list[ExtractionValidationIssue], list[dict[str, Any]]]:
    repaired_items: list[dict[str, Any]] = []
    issues: list[ExtractionValidationIssue] = []
    actions: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if isinstance(item, dict):
            repaired_items.append(dict(item))
            continue
        if field_name == "candidate_universe_gaps" and isinstance(item, str) and item.strip():
            repaired_items.append({
                "legal_name": item.strip(),
                "reason": "Provider returned candidate universe gap as a string; retained as review-needed diagnostic input.",
            })
            issues.append(_issue(
                "extraction_repair_needed",
                "warning",
                f"$.{field_name}[{index}]",
                "Provider returned a candidate universe gap as a string; it was converted to an object.",
                details={"field": field_name},
                remediation="Return candidate universe gaps as objects with legal_name/source_refs/reason.",
            ))
            actions.append({"type": "string_gap_wrapped_as_object", "path": f"$.{field_name}[{index}]"})
    return repaired_items, issues, actions


def _looks_like_synthetic_key(value: str) -> bool:
    return bool(re.fullmatch(r"(?:candidate|item|row|gap|source)?[_-]?\d+", value.strip(), flags=re.IGNORECASE))


def _source_indexes(sources: list[dict[str, Any]]) -> dict[str, dict[str, str]]:
    exact: dict[str, str] = {}
    by_url: dict[str, str] = {}
    by_title_domain: dict[str, list[str]] = {}
    for source in sources:
        evidence_ref = str(source.get("evidence_ref") or source.get("source_ref") or "").strip()
        if not evidence_ref:
            continue
        exact[evidence_ref] = evidence_ref
        url_key = _normalize_url(str(source.get("url") or ""))
        if url_key:
            by_url[url_key] = evidence_ref
        title_domain_key = _title_domain_key(str(source.get("title") or ""), str(source.get("url") or ""))
        if title_domain_key:
            by_title_domain.setdefault(title_domain_key, []).append(evidence_ref)
    unique_title_domain = {key: refs[0] for key, refs in by_title_domain.items() if len(refs) == 1}
    return {"exact": exact, "by_url": by_url, "by_title_domain": unique_title_domain}


def _reconcile_candidate_refs(
    candidate: dict[str, Any],
    *,
    source_indexes: dict[str, dict[str, str]],
    path: str,
) -> tuple[dict[str, Any], list[ExtractionValidationIssue], list[dict[str, Any]]]:
    issues: list[ExtractionValidationIssue] = []
    actions: list[dict[str, Any]] = []

    def reconcile_ref(value: Any, ref_path: str) -> str | None:
        if not isinstance(value, str) or not value.strip():
            issues.append(_issue(
                "evidence_linking_failed",
                "error",
                ref_path,
                "Evidence ref must be a non-empty string.",
                details={"source_ref": str(value), "reason": "non_string_or_empty"},
                remediation="Use stable string evidence refs that resolve to normalized sources.",
            ))
            return None
        raw = value.strip()
        if raw in source_indexes["exact"]:
            return raw
        repaired = _repair_ref(raw, source_indexes)
        if repaired:
            issues.append(_issue(
                "extraction_repair_needed",
                "warning",
                ref_path,
                "Evidence ref was repaired to a normalized source evidence_ref.",
                details={"original_ref": raw, "repaired_ref": repaired},
                remediation="Provider extraction should reference source evidence_ref values directly.",
            ))
            actions.append({"type": "evidence_ref_reconciled", "path": ref_path, "from": raw, "to": repaired})
            return repaired
        issues.append(_issue(
            "evidence_linking_failed",
            "error",
            ref_path,
            "Evidence ref cannot be linked to any normalized source.",
            details={"source_ref": raw, "known_source_refs": sorted(source_indexes["exact"])},
            remediation="Reject or repair evidence refs before product projection so sources do not collapse silently.",
        ))
        return None

    def walk(value: Any, current_path: str, key_name: str = "") -> Any:
        if isinstance(value, list):
            if key_name in {"evidence_refs", "source_refs"}:
                repaired_refs = []
                for index, ref in enumerate(value):
                    repaired_ref = reconcile_ref(ref, f"{current_path}[{index}]")
                    if repaired_ref is not None:
                        repaired_refs.append(repaired_ref)
                return repaired_refs
            return [walk(item, f"{current_path}[{index}]") for index, item in enumerate(value)]
        if isinstance(value, dict):
            return {key: walk(item, f"{current_path}.{key}", key) for key, item in value.items()}
        if key_name == "source_ref":
            return reconcile_ref(value, current_path) or value
        return value

    repaired_candidate = walk(dict(candidate), path)
    return repaired_candidate, issues, actions


def _repair_invalid_zero_score_projection(
    candidate: dict[str, Any],
    *,
    path: str,
) -> tuple[dict[str, Any], list[ExtractionValidationIssue], list[dict[str, Any]]]:
    issues: list[ExtractionValidationIssue] = []
    actions: list[dict[str, Any]] = []
    repaired = dict(candidate)
    signals = _list(repaired.get("signals"))
    changed = False
    for index, signal in enumerate(signals):
        search_status = str(signal.get("search_status") or "")
        if search_status.startswith("not_searched") and str(signal.get("status") or "") == "not_observed":
            signal["status"] = "unclear"
            signal["confidence"] = "low"
            signal["summary"] = str(signal.get("summary") or "Signal was not searched; result requires review.")
            issues.append(_issue(
                "invalid_zero_score_projection",
                "warning",
                f"{path}.signals[{index}]",
                "Unsearched signal output was projected as normal not_observed; it was downgraded to unclear.",
                details={"search_status": search_status, "signal_code": str(signal.get("signal_code") or signal.get("code") or "")},
                remediation="Represent unsearched signals as review-needed/not_searched states, not searched-negative evidence.",
            ))
            actions.append({"type": "not_searched_signal_downgraded", "path": f"{path}.signals[{index}]"})
            changed = True
    if changed:
        repaired["signals"] = signals
        flags = [str(flag) for flag in repaired.get("review_flags", []) if str(flag).strip()] if isinstance(repaired.get("review_flags"), list) else []
        repaired["review_flags"] = sorted({*flags, "invalid_zero_score_projection_requires_review"})
    return repaired, issues, actions


def _repair_ref(value: str, source_indexes: dict[str, dict[str, str]]) -> str | None:
    url_key = _normalize_url(value)
    if url_key and url_key in source_indexes["by_url"]:
        return source_indexes["by_url"][url_key]
    title_key = _title_domain_key(value, value)
    if title_key and title_key in source_indexes["by_title_domain"]:
        return source_indexes["by_title_domain"][title_key]
    return None


def _normalize_url(value: str) -> str:
    if not value:
        return ""
    parsed = urlparse(value.strip())
    if not parsed.netloc:
        return ""
    path = parsed.path.rstrip("/")
    return f"{parsed.netloc.lower()}{path.lower()}"


def _title_domain_key(title: str, url: str) -> str:
    domain = urlparse(url).netloc.lower()
    clean_title = re.sub(r"\s+", " ", title.strip().lower())
    return f"{domain}|{clean_title}" if domain and clean_title else ""


def _list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _issue(
    code: str,
    severity: ExtractionIssueSeverity,
    path: str,
    message: str,
    *,
    details: dict[str, Any] | None = None,
    remediation: str = "",
) -> ExtractionValidationIssue:
    return ExtractionValidationIssue(
        code=code,
        severity=severity,
        path=path,
        message=message,
        details=details or {},
        remediation=remediation,
    )
