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
from power_web_os.api.radar_dossier_summaries import budget_summary as _budget_summary
from power_web_os.api.radar_dossier_summaries import coverage_summary as _coverage_summary
from power_web_os.api.radar_mappers import journal_event_response
from power_web_os.api.radar_source_lifecycle import source_lifecycle as _source_lifecycle
from power_web_os.api.radar_source_lifecycle import source_lifecycle_summary as _source_lifecycle_summary
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
    persisted_run_metadata = _dict(run.run_metadata)
    candidates = _list(artifact.get("candidates"))
    sources = _list(artifact.get("sources"))
    run_metadata = _dict(artifact.get("run_metadata"))
    discovery_plan = _dict(run_metadata.get("discovery_plan"))
    acceptance_metadata = _dict(discovery_plan.get("acceptance_metadata"))
    execution_results = _dict(run_metadata.get("execution_results"))
    retrieval_plan = _dict(execution_results.get("retrieval_plan"))
    source_policy_decisions = _list(discovery_plan.get("source_policy_decisions"))
    source_obligations = _list(execution_results.get("source_obligations"))
    source_obligation_decisions = _list(execution_results.get("source_obligation_decisions"))
    source_obligation_summary = _dict(execution_results.get("source_obligation_summary"))
    coverage_summary = _coverage_summary(discovery_plan, execution_results)
    budget_summary = _budget_summary(execution_results)
    budget_exhaustion_events = _list(execution_results.get("budget_exhaustion_events"))
    checkpoint_summary = _dict(execution_results.get("checkpoint_summary"))
    checkpoint_decisions = _list(execution_results.get("checkpoint_decisions"))
    adaptive_actions = _list(execution_results.get("adaptive_actions"))
    checkpoint_warnings = [
        str(value)
        for value in execution_results.get("checkpoint_warnings", [])
        if isinstance(value, str)
    ]
    stopped_for_review_reason = str(execution_results.get("stopped_for_review_reason") or "")
    signal_search_statuses = _list(execution_results.get("signal_search_statuses"))
    entity_resolution_results = _list(execution_results.get("entity_resolution_results"))
    linked_entity_facts = _list(execution_results.get("linked_entity_facts"))
    entity_resolution_warnings = _list(execution_results.get("entity_resolution_warnings"))
    candidate_universe = _list(execution_results.get("candidate_universe"))
    candidate_discovery_reconciliation = _dict(execution_results.get("candidate_discovery_reconciliation"))
    product_acceptance_ledger = _list(execution_results.get("product_acceptance_ledger"))
    upstream_disambiguation_results = _list(execution_results.get("upstream_disambiguation_results"))
    cross_source_disambiguation_tasks = _list(execution_results.get("cross_source_disambiguation_tasks"))
    cross_source_disambiguation_execution = _list(execution_results.get("cross_source_disambiguation_execution"))
    extraction_recovery_records = _list(execution_results.get("extraction_recovery_records"))
    coverage_checks = _list(execution_results.get("coverage_checks"))
    coverage_warnings = [str(value) for value in execution_results.get("coverage_warnings", []) if isinstance(value, str)]
    unresolved_candidate_gaps = _list(execution_results.get("unresolved_candidate_gaps"))
    source_usage_index = _source_usage_index(candidates)
    queries = _dossier_queries(output.search_plan_payload if output is not None else {}, sources, source_usage_index)
    source_responses = [_dossier_source_response(item, source_usage_index=source_usage_index) for item in sources]
    source_lifecycle = _source_lifecycle(
        sources=sources,
        execution_results=execution_results,
        source_usage_index=source_usage_index,
    )
    source_lifecycle_summary = _source_lifecycle_summary(source_lifecycle)
    execution_outcome, execution_outcome_reason = _execution_outcome(
        run=run,
        output=output,
        candidate_count=len(candidates),
        checkpoint_summary=checkpoint_summary,
        stopped_for_review_reason=stopped_for_review_reason,
    )
    validation = _list(artifact.get("contract_validation")) or (output.contract_validation_payload if output is not None else [])
    timeline = [journal_event_response(event) for event in events if event.visibility != "debug"]
    used_source_count = sum(1 for item in source_responses if item.usage_status == "used")
    analyzed_source_count = _int(execution_results.get("analyzed_source_count"), default=0)
    skipped_source_count = sum(1 for item in source_policy_decisions if str(item.get("decision")) == "skipped")
    review_flag_count = sum(len([flag for flag in item.get("review_flags", []) if isinstance(flag, str)]) for item in candidates)
    source_cards = _list(acceptance_metadata.get("source_cards"))
    source_capability_decisions = _list(acceptance_metadata.get("source_capability_decisions"))

    return RadarRunDossierResponse(
        run_context=_dossier_context(run),
        runtime_config=_runtime_config(persisted_run_metadata),
        runtime_config_warnings=_list(persisted_run_metadata.get("runtime_config_warnings")),
        radar_snapshot=_dict(artifact.get("radar")) or _definition_payload_summary(active_definition),
        definition_snapshot=_definition_snapshot(active_definition),
        discovery_plan=discovery_plan,
        retrieval_plan=retrieval_plan,
        source_cards=source_cards,
        source_capability_decisions=source_capability_decisions,
        source_capability_validation=_dict(acceptance_metadata.get("source_capability_validation")),
        source_capability_strategy_summary=_dict(execution_results.get("source_capability_strategy_summary")),
        source_policy_decisions=source_policy_decisions,
        source_obligations=source_obligations,
        source_obligation_decisions=source_obligation_decisions,
        source_obligation_summary=source_obligation_summary,
        coverage_summary=coverage_summary,
        budget_summary=budget_summary,
        budget_exhaustion_events=budget_exhaustion_events,
        external_call_budget_settings=_dict(execution_results.get("external_call_budget_settings")),
        external_call_budget_counters=_int_dict(execution_results.get("external_call_budget_counters")),
        external_call_budget_counters_by_role=_int_dict(execution_results.get("external_call_budget_counters_by_role")),
        external_call_budget_exhaustion_events=_list(execution_results.get("external_call_budget_exhaustion_events")),
        work_admission_reserved_capacity=_dict(execution_results.get("work_admission_reserved_capacity")),
        provider_retry_records=_list(execution_results.get("provider_retry_records")),
        openrouter_server_tool_usage=_dict(execution_results.get("openrouter_server_tool_usage")),
        post_call_budget_overruns=_list(execution_results.get("post_call_budget_overruns")),
        checkpoint_summary=checkpoint_summary,
        checkpoint_decisions=checkpoint_decisions,
        adaptive_actions=adaptive_actions,
        checkpoint_warnings=checkpoint_warnings,
        stopped_for_review_reason=stopped_for_review_reason,
        signal_search_statuses=signal_search_statuses,
        entity_resolution_results=entity_resolution_results,
        linked_entity_facts=linked_entity_facts,
        entity_resolution_warnings=entity_resolution_warnings,
        candidate_universe=candidate_universe,
        candidates=candidates,
        candidate_discovery_reconciliation=candidate_discovery_reconciliation,
        product_acceptance_ledger=product_acceptance_ledger,
        upstream_disambiguation_results=upstream_disambiguation_results,
        cross_source_disambiguation_tasks=cross_source_disambiguation_tasks,
        cross_source_disambiguation_execution=cross_source_disambiguation_execution,
        extraction_recovery_records=extraction_recovery_records,
        coverage_checks=coverage_checks,
        coverage_warnings=coverage_warnings,
        unresolved_candidate_gaps=unresolved_candidate_gaps,
        expansion_target_queue=_list(execution_results.get("expansion_target_queue")),
        expansion_target_summary_by_type=_int_dict(execution_results.get("expansion_target_summary_by_type")),
        search_expansion_query_variants=_list(execution_results.get("search_expansion_query_variants")),
        search_expansion_query_variants_by_target=_dict(execution_results.get("search_expansion_query_variants_by_target")),
        search_expansion_selection_summary=_dict(execution_results.get("search_expansion_selection_summary")),
        search_expansion_selection_diagnostics=_list(execution_results.get("search_expansion_selection_diagnostics")),
        search_expansion_results=_list(execution_results.get("search_expansion_results")),
        search_expansion_results_by_target=_dict(execution_results.get("search_expansion_results_by_target")),
        search_expansion_results_by_target_type=_dict(execution_results.get("search_expansion_results_by_target_type")),
        search_expansion_execution_summary=_dict(execution_results.get("search_expansion_execution_summary")),
        search_expansion_target_coverage=_list(execution_results.get("search_expansion_target_coverage")),
        targets_not_searched=_list(execution_results.get("targets_not_searched")),
        budget_reserve_counters=_int_dict(execution_results.get("budget_reserve_counters")),
        budget_reserve_exhaustion_events=_list(execution_results.get("budget_reserve_exhaustion_events")),
        semantic_task_budget_counters=_int_dict(execution_results.get("semantic_task_budget_counters")),
        semantic_task_budget_exhaustion_events=_list(execution_results.get("semantic_task_budget_exhaustion_events")),
        target_probe_guarantees=_dict(execution_results.get("target_probe_guarantees")),
        target_probe_guarantee_failures=_list(execution_results.get("target_probe_guarantee_failures")),
        work_scheduler_plan=_dict(execution_results.get("work_scheduler_plan")),
        work_scheduler_ledger=_dict(execution_results.get("work_scheduler_ledger")),
        work_admission_decisions=_list(execution_results.get("work_admission_decisions")),
        work_lane_summary=_dict(execution_results.get("work_lane_summary")),
        work_guarantee_failures=_list(execution_results.get("work_guarantee_failures")),
        work_execution_order=_list(execution_results.get("work_execution_order")),
        deferred_work_items=_list(execution_results.get("deferred_work_items")),
        rejected_work_items=_list(execution_results.get("rejected_work_items")),
        source_verification_cache_stats=_int_dict(execution_results.get("source_verification_cache_stats")),
        source_verification_unique_request_count=_int(execution_results.get("source_verification_unique_request_count"), default=0),
        source_verification_duplicate_skip_count=_int(execution_results.get("source_verification_duplicate_skip_count"), default=0),
        registry_ambiguity_fanout_summary=_dict(execution_results.get("registry_ambiguity_fanout_summary")),
        benchmark_recall_target_summary=_dict(execution_results.get("benchmark_recall_target_summary")),
        legal_subsidiary_completion_summary=_dict(execution_results.get("legal_subsidiary_completion_summary")),
        discovery_iteration_count=_int(execution_results.get("discovery_iteration_count"), default=0),
        search_plan=queries,
        sources=source_responses,
        source_lifecycle=source_lifecycle,
        source_lifecycle_summary=source_lifecycle_summary,
        validation=validation,
        timeline=timeline,
        summary=RadarRunDossierSummaryResponse(
            output_state="available" if output is not None else ("failed" if run.status.value == "failed" else "pending"),
            execution_outcome=execution_outcome,
            execution_outcome_reason=execution_outcome_reason,
            query_count=len(queries),
            source_count=len(source_responses),
            used_source_count=used_source_count,
            retrieved_source_count=_retrieved_source_count(execution_results, source_lifecycle_summary.by_state.get("retrieved", 0)),
            linked_source_count=source_lifecycle_summary.by_state.get("linked", 0) + source_lifecycle_summary.by_state.get("used", 0),
            linking_failed_source_count=source_lifecycle_summary.by_state.get("linking_failed", 0),
            schema_rejected_source_count=source_lifecycle_summary.by_state.get("schema_rejected", 0),
            analyzed_source_count=analyzed_source_count,
            analyzed_only_source_count=source_lifecycle_summary.by_state.get("analyzed_only", 0),
            diagnostic_source_count=source_lifecycle_summary.total_count,
            skipped_source_count=skipped_source_count,
            candidate_count=len(candidates),
            smoke_candidate_cap=_optional_int(execution_results.get("smoke_candidate_cap")),
            promoted_candidate_count=_int(execution_results.get("promoted_candidate_count"), default=len(candidates)),
            diagnostic_candidate_count=_int(execution_results.get("diagnostic_candidate_count"), default=0),
            review_needed_universe_count=_int(execution_results.get("review_needed_universe_count"), default=0),
            linked_branch_or_site_count=_int(execution_results.get("linked_branch_or_site_count"), default=0),
            source_cards_count=len(source_cards),
            source_capability_decision_count=len(source_capability_decisions),
            connector_profile_loaded_count=len({str(item.get("connector_profile_id") or "") for item in source_cards if str(item.get("connector_profile_id") or "").strip()}),
            validation_issue_count=len(validation),
            review_flag_count=review_flag_count + len(reviews),
            coverage_warning_count=len(coverage_warnings) + len(unresolved_candidate_gaps),
        ),
    )


def _execution_outcome(
    *,
    run: RadarRunRecord,
    output: RadarRunOutputRecord | None,
    candidate_count: int,
    checkpoint_summary: dict[str, Any],
    stopped_for_review_reason: str,
) -> tuple[str, str]:
    if run.status.value == "failed":
        return "failed", str(run.error_message or "")
    if output is None:
        return "pending", ""
    if bool(checkpoint_summary.get("hard_failure_recommended")):
        return "blocked_by_policy", _checkpoint_reason(checkpoint_summary) or stopped_for_review_reason
    if stopped_for_review_reason or bool(checkpoint_summary.get("stopped_for_review")):
        return "stopped_for_review", stopped_for_review_reason or _checkpoint_reason(checkpoint_summary)
    if candidate_count:
        return "completed_with_candidates", ""
    return "completed_empty", ""


def _checkpoint_reason(checkpoint_summary: dict[str, Any]) -> str:
    by_reason = checkpoint_summary.get("by_reason")
    if not isinstance(by_reason, dict) or not by_reason:
        return ""
    return ", ".join(str(key) for key in sorted(by_reason))


def _retrieved_source_count(execution_results: dict[str, Any], fallback: int) -> int:
    refs = {
        str(item.get("source_ref") or item.get("evidence_ref") or item.get("id") or "").strip()
        for item in _list(execution_results.get("retrieved_sources"))
    }
    refs.discard("")
    if refs:
        return len(refs)
    explicit = execution_results.get("retrieved_source_count")
    return explicit if isinstance(explicit, int) and not isinstance(explicit, bool) else fallback


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


def _runtime_config(metadata: dict[str, Any]) -> dict[str, Any]:
    worker_config = _dict(metadata.get("worker_runtime_config"))
    if worker_config:
        return worker_config
    return _dict(metadata.get("api_runtime_config"))


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
                source_scope=str(item.get("source_scope") or "additional"),
                source_base=str(item.get("source_base")) if item.get("source_base") is not None else None,
                application_scope=str(item.get("application_scope")) if item.get("application_scope") is not None else None,
                source_ids=[str(value) for value in item.get("source_ids", []) if isinstance(value, str)],
                external_source_hints=[str(value) for value in item.get("external_source_hints", []) if isinstance(value, str)],
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


def _int_dict(value: object) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    result: dict[str, int] = {}
    for key, item in value.items():
        try:
            result[str(key)] = int(item)  # type: ignore[arg-type]
        except (TypeError, ValueError):
            continue
    return result


def _int(value: object, *, default: int) -> int:
    return value if isinstance(value, int) and not isinstance(value, bool) else default


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None
