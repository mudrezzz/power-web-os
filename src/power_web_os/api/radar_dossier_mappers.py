"""Run dossier projection for the Radar API."""

from __future__ import annotations

from typing import Any

from power_web_os.api.radar_dtos import (
    RadarRunDossierContextResponse,
    RadarRunDossierDefinitionResponse,
    RadarRunDossierQueryResponse,
    RadarRunDossierResponse,
    RadarRunDossierSourceResponse,
    RadarRunDossierSourceUsageResponse,
    RadarRunDossierSummaryResponse,
)
from power_web_os.api.radar_mappers import journal_event_response
from power_web_os.application.radar_records import (
    RadarDefinitionRecord,
    RadarReviewDecisionRecord,
    RadarRunEventRecord,
    RadarRunOutputRecord,
    RadarRunRecord,
)


def dossier_response(
    run: RadarRunRecord,
    *,
    output: RadarRunOutputRecord | None,
    active_definition: RadarDefinitionRecord | None,
    events: tuple[RadarRunEventRecord, ...],
    reviews: tuple[RadarReviewDecisionRecord, ...] = (),
) -> RadarRunDossierResponse:
    artifact = output.artifact_payload if output is not None else {}
    candidates = _list(artifact.get("candidates"))
    sources = _list(artifact.get("sources"))
    source_usage_index = _source_usage_index(candidates)
    queries = _dossier_queries(output.search_plan_payload if output is not None else {}, sources, source_usage_index)
    source_responses = [_dossier_source_response(item, source_usage_index=source_usage_index) for item in sources]
    validation = _list(artifact.get("contract_validation")) or (output.contract_validation_payload if output is not None else [])
    timeline = [journal_event_response(event) for event in events if event.visibility != "debug"]
    used_source_count = sum(1 for item in source_responses if item.usage_status == "used")
    review_flag_count = sum(len([flag for flag in item.get("review_flags", []) if isinstance(flag, str)]) for item in candidates)

    return RadarRunDossierResponse(
        run_context=_dossier_context(run),
        radar_snapshot=_dict(artifact.get("radar")) or _definition_payload_summary(active_definition),
        definition_snapshot=_definition_snapshot(active_definition),
        search_plan=queries,
        sources=source_responses,
        validation=validation,
        timeline=timeline,
        summary=RadarRunDossierSummaryResponse(
            output_state="available" if output is not None else ("failed" if run.status.value == "failed" else "pending"),
            query_count=len(queries),
            source_count=len(source_responses),
            used_source_count=used_source_count,
            candidate_count=len(candidates),
            validation_issue_count=len(validation),
            review_flag_count=review_flag_count + len(reviews),
        ),
    )


def _dossier_context(run: RadarRunRecord) -> RadarRunDossierContextResponse:
    metadata = _dict(run.run_metadata)
    nested_metadata = _dict(metadata.get("run_metadata"))
    return RadarRunDossierContextResponse(
        run_id=run.run_id,
        radar_id=run.radar_id,
        status=run.status.value,
        live=bool(metadata.get("live", True)),
        requester=str(metadata.get("requester", "")),
        correlation_id=run.correlation_id,
        idempotency_key=run.idempotency_key,
        queued_at=run.queued_at,
        started_at=run.started_at,
        completed_at=run.completed_at,
        model=_metadata_text(metadata, nested_metadata, "model"),
        web_mode=_metadata_text(metadata, nested_metadata, "web_mode"),
        runtime=_metadata_text(metadata, nested_metadata, "runtime") or "",
        task_context=_dict(metadata.get("task_context")),
    )


def _definition_snapshot(record: RadarDefinitionRecord | None) -> RadarRunDossierDefinitionResponse | None:
    if record is None:
        return None
    return RadarRunDossierDefinitionResponse(
        definition_id=record.definition_id,
        definition_version=record.definition_version,
        is_active=record.is_active,
        payload_summary=_definition_payload_summary(record),
    )


def _definition_payload_summary(record: RadarDefinitionRecord | None) -> dict[str, Any]:
    if record is None:
        return {}
    payload = record.definition_payload
    return {
        "definition_id": payload.get("definition_id", record.definition_id),
        "metadata": _dict(payload.get("metadata")),
        "qualification_rule_count": len(_flatten_definition_rules(_dict(payload.get("account_qualification")).get("rule_group"))),
        "intent_signal_count": len(payload.get("intent_signals", [])) if isinstance(payload.get("intent_signals"), list) else 0,
        "source_policy": _dict(payload.get("global_search_policy")),
    }


def _dossier_queries(
    search_plan: dict[str, Any],
    sources: list[dict[str, Any]],
    source_usage_index: dict[str, list[RadarRunDossierSourceUsageResponse]],
) -> list[RadarRunDossierQueryResponse]:
    responses = []
    for index, item in enumerate(_list(search_plan.get("queries")), start=1):
        query_id = str(item.get("query_id") or f"q{index}")
        source_refs = [str(source.get("evidence_ref", "")) for source in sources if str(source.get("query_id", "")) == query_id]
        candidate_refs = sorted({
            usage.candidate_id
            for ref in source_refs
            for usage in source_usage_index.get(ref, [])
            if usage.candidate_id
        })
        responses.append(
            RadarRunDossierQueryResponse(
                query_id=query_id,
                query=str(item.get("query", "")),
                purpose=str(item.get("purpose", "")),
                expected_evidence=[str(value) for value in item.get("expected_evidence", []) if isinstance(value, str)],
                stage=str(item.get("stage")) if item.get("stage") is not None else None,
                subject_type=str(item.get("subject_type")) if item.get("subject_type") is not None else None,
                subject_id=str(item.get("subject_id")) if item.get("subject_id") is not None else None,
                rule_snapshot=str(item.get("rule_snapshot") or ""),
                depends_on=[str(value) for value in item.get("depends_on", []) if isinstance(value, str)],
                candidate_scope=[str(value) for value in item.get("candidate_scope", []) if isinstance(value, str)],
                source_count=len(source_refs),
                source_refs=[ref for ref in source_refs if ref],
                candidate_refs=candidate_refs,
            )
        )
    return responses


def _dossier_source_response(
    payload: dict[str, Any],
    *,
    source_usage_index: dict[str, list[RadarRunDossierSourceUsageResponse]],
) -> RadarRunDossierSourceResponse:
    evidence_ref = str(payload.get("evidence_ref", ""))
    usages = source_usage_index.get(evidence_ref, [])
    return RadarRunDossierSourceResponse(
        evidence_ref=evidence_ref,
        title=str(payload.get("title", "")),
        url=str(payload.get("url", "")),
        snippet=str(payload.get("snippet", "")),
        query_id=str(payload.get("query_id")) if payload.get("query_id") is not None else None,
        source_type=str(payload.get("source_type", "web")),
        usage_status="used" if usages else "collected_not_used",
        usages=usages,
    )


def _source_usage_index(candidates: list[dict[str, Any]]) -> dict[str, list[RadarRunDossierSourceUsageResponse]]:
    usages: dict[str, list[RadarRunDossierSourceUsageResponse]] = {}
    for candidate in candidates:
        candidate_id = str(candidate.get("candidate_id", ""))
        candidate_name = str(candidate.get("legal_name", ""))
        for source_ref in [str(ref) for ref in candidate.get("evidence_refs", []) if isinstance(ref, str)]:
            _append_source_usage(usages, source_ref, candidate_id, candidate_name, "candidate", candidate_id, candidate_name)
        for item in _list(candidate.get("qualification")):
            subject_id = _qualification_subject_id(item)
            subject_label = str(item.get("criterion", "") or item.get("criterion_code", ""))
            for source_ref in _source_refs_for_finding(item):
                _append_source_usage(usages, source_ref, candidate_id, candidate_name, "qualification", subject_id, subject_label)
        for item in _list(candidate.get("signals")):
            subject_id = str(item.get("signal_code", ""))
            subject_label = str(item.get("signal", "") or subject_id)
            for source_ref in _source_refs_for_finding(item):
                _append_source_usage(usages, source_ref, candidate_id, candidate_name, "signal", subject_id, subject_label)
    return usages


def _append_source_usage(
    usages: dict[str, list[RadarRunDossierSourceUsageResponse]],
    source_ref: str,
    candidate_id: str,
    candidate_name: str,
    subject_type: str,
    subject_id: str,
    subject_label: str,
) -> None:
    if not source_ref:
        return
    usage = RadarRunDossierSourceUsageResponse(
        candidate_id=candidate_id,
        candidate_name=candidate_name,
        subject_type=subject_type,
        subject_id=subject_id,
        subject_label=subject_label,
    )
    existing = usages.setdefault(source_ref, [])
    if usage not in existing:
        existing.append(usage)


def _source_refs_for_finding(payload: dict[str, Any]) -> list[str]:
    refs = [str(ref) for ref in payload.get("evidence_refs", []) if isinstance(ref, str)]
    refs.extend(str(item.get("source_ref", "")) for item in _list(payload.get("source_usages")))
    refs.extend(str(item.get("source_ref", "")) for item in _list(payload.get("evidence_findings")))
    return sorted({ref for ref in refs if ref})


def _metadata_text(metadata: dict[str, Any], nested_metadata: dict[str, Any], key: str) -> str | None:
    value = metadata.get(key, nested_metadata.get(key))
    return str(value) if value not in (None, "") else None


def _flatten_definition_rules(value: object) -> list[dict[str, Any]]:
    group = _dict(value)
    return _list(group.get("rules")) + [
        rule
        for child in _list(group.get("groups"))
        for rule in _flatten_definition_rules(child)
    ]


def _qualification_subject_id(payload: dict[str, Any]) -> str:
    return str(payload.get("rule_id") or payload.get("criterion_code") or "")


def _list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [dict(item) for item in value if isinstance(item, dict)]


def _dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}
