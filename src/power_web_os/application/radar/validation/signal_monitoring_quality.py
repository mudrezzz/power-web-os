"""Signal-monitoring quality metrics for pipeline acceptance validation."""

from __future__ import annotations

from typing import Any


def evaluate_signal_report(
    report: dict[str, Any],
    *,
    negative_controls: object = (),
) -> dict[str, int]:
    tasks = _list(report.get("tasks"))
    decisions = [item for item in _list(report.get("source_strategy_decisions")) if item.get("status") == "selected"]
    ledger = _list(report.get("source_lane_ledger"))
    receipts = _list(report.get("search_execution_receipts"))
    observations = _list(report.get("observations"))
    task_observations = _list(report.get("task_observations"))
    validations = _list(_dict(report.get("evidence_validation_summary")).get("records"))
    source_index = _source_index(report)
    source_urls = {
        ref: _canonical_url(source.get("url"))
        for ref, source in source_index.items()
        if source.get("url")
    }
    source_bindings = _list(report.get("source_binding_decisions"))
    previous_source_keys = {
        str(item) for item in _list_values(_dict(report.get("input_snapshot")).get("previous_signal_source_keys"))
    }
    watermarks_before = _watermark_map(report.get("watermarks_before"))
    watermarks_after = _watermark_map(report.get("watermarks_after"))
    ledger_decisions = {value for item in ledger for value in item.get("source_decision_ids", [])}
    executed_task_ids = {item.get("task_id") for item in ledger if item.get("status") == "executed"}
    receipt_task_ids = {item.get("task_id") for item in receipts}
    validation_by_task = {item.get("task_id"): item for item in validations}
    negative_tested, negative_false = _negative_control_metrics(
        task_observations,
        source_index,
        source_bindings,
        _list(negative_controls),
    )
    candidates = _list(report.get("candidates"))
    confirmed_evidence = _confirmed_evidence(task_observations)
    return {
        "candidate_count": len(candidates),
        "accepted_candidate_count": sum(str(item.get("product_acceptance_status")) == "product_candidate" for item in candidates),
        "review_candidate_count": sum(str(item.get("product_acceptance_status")) != "product_candidate" for item in candidates),
        "signal_rule_count": len(_list(report.get("signal_rules"))),
        "candidate_signal_pair_count": len({(item.get("candidate_id"), item.get("signal_code")) for item in tasks}),
        "task_count": len(tasks),
        "orphan_decisions": sum(item.get("decision_id") not in ledger_decisions for item in decisions),
        "opaque_known_tasks": sum(
            item.get("source_lane") == "known_source"
            and not any(source.get("url") for source in _list(item.get("source_contracts")))
            for item in tasks
        ),
        "unrestricted_official_tasks": sum(
            item.get("source_lane") == "official_company" and not item.get("domain_restrictions")
            for item in tasks
        ),
        "open_web_task_count": sum(item.get("source_lane") == "open_web" for item in tasks),
        "receipt_gap_count": len(executed_task_ids - receipt_task_ids),
        "false_not_observed_count": sum(
            item.get("action") == "not_observed"
            and int(item.get("required_task_count") or 0) != int(item.get("completed_required_task_count") or 0)
            for item in _list(report.get("checkpoint_decisions"))
        ),
        "initial_lookback_days": int(_dict(report.get("window_policy")).get("initial_lookback_days") or 0),
        "incremental_window_count": sum(
            item.get("window_basis") in {"incremental", "incremental_watermark"} for item in tasks
        ),
        "failed_watermark_advances": sum(
            watermarks_after.get(key) != watermarks_before.get(key)
            for key, item in _task_observation_map(tasks, task_observations).items()
            if item.get("search_status") not in {"searched", "duplicate_existing_signal"}
        ),
        "observed_count": sum(item.get("observation_status") == "observed" for item in observations),
        "zero_score_observed_count": sum(
            item.get("observation_status") == "observed" and int(item.get("score") or 0) <= 0
            for item in task_observations
        ),
        "rejected_observed_count": sum(
            item.get("observation_status") == "observed"
            and not _dict(validation_by_task.get(item.get("task_id"))).get("accepted", False)
            for item in task_observations
        ),
        "entity_mismatch_rejection_count": sum(item.get("reason") == "observed_evidence_candidate_mismatch" for item in validations),
        "negative_control_tested_count": negative_tested,
        "negative_control_false_positive_count": negative_false,
        "retrieved_at_as_fresh_count": sum(
            1 for _, evidence in confirmed_evidence if not _event_or_publication_date(evidence, source_index)
        ),
        "unknown_date_review_count": sum(
            item.get("search_status") in {"review_needed_date_unknown", "duplicate_existing_review"}
            for item in task_observations
        ),
        "out_of_window_confirmed_count": sum(
            item.get("observation_status") == "observed"
            for item in task_observations
            for evidence in _list(item.get("evidence"))
            if evidence.get("temporal_status") == "rejected_out_of_window"
            and evidence.get("source_ref") in set(_list_values(item.get("source_refs")))
        ),
        "sources_without_capability_count": sum(
            not source.get("capability") or not source.get("capability_basis")
            for source in source_index.values()
            if source.get("url")
        ),
        "cross_entity_known_task_count": _cross_entity_known_task_count(tasks, source_bindings, source_index),
        "identity_confirmed_signal_count": sum(
            item.get("observation_status") == "observed"
            for item in task_observations
            for source in _sources_for_observation(item, source_index)
            if source.get("capability") in {"identity_only", "registry"}
        ),
        "alternate_query_count": sum(bool(str(item.get("alternate_query") or "").strip()) for item in tasks),
        "transport_retry_proven": _transport_retry_count(report),
        "unretried_transport_error_count": _unretried_transport_error_count(report),
        "duplicate_review_count": sum(item.get("search_status") == "duplicate_existing_review" for item in task_observations),
        "unreasoned_retained_item_count": sum(
            item.get("search_status") in {
                "review_needed_date_unknown",
                "review_needed_date_conflict",
                "rejected_out_of_window",
                "duplicate_existing_review",
                "review_needed",
            }
            and not (item.get("summary") or item.get("diagnostics") or item.get("source_refs"))
            for item in task_observations
        ),
        "duplicate_count": sum(item.get("search_status") == "duplicate_existing_signal" for item in task_observations),
        "previous_source_key_count": len(previous_source_keys),
        "republished_previous_source_count": _republished_previous_source_count(
            task_observations,
            source_urls=source_urls,
            previous_source_keys=previous_source_keys,
        ),
    }


def control_match_summary(
    report: dict[str, Any],
    controls: list[dict[str, Any]],
    *,
    expected: str,
) -> dict[str, Any]:
    source_index = _source_index(report)
    observations = _list(report.get("task_observations"))
    bindings = _list(report.get("source_binding_decisions"))
    matched: list[str] = []
    missing: list[str] = []
    for control in controls:
        control_id = str(control.get("id") or control.get("url") or "")
        if expected == "confirmed":
            ok = _positive_control_matches(control, observations, source_index)
        elif expected == "unknown":
            ok = _unknown_control_matches(control, observations, source_index)
        else:
            ok = _negative_control_matches(control, observations, source_index, bindings)
        (matched if ok else missing).append(control_id)
    return {"matched": len(matched), "matched_ids": matched, "missing": missing}


def _source_index(report: dict[str, Any]) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    input_snapshot = _dict(report.get("input_snapshot"))
    for source in [
        *_list(report.get("sources")),
        *_list(report.get("known_sources")),
        *_list(input_snapshot.get("known_sources")),
        *_list(input_snapshot.get("configured_sources")),
    ]:
        ref = str(source.get("source_ref") or source.get("source_id") or "")
        if ref:
            result.setdefault(ref, source)
    for observation in [*_list(report.get("task_observations")), *_list(report.get("observations"))]:
        for source in _list(observation.get("sources")):
            ref = str(source.get("source_ref") or source.get("source_id") or "")
            if ref:
                result[ref] = {**result.get(ref, {}), **source}
    return result


def _confirmed_evidence(observations: list[dict[str, Any]]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    result: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for observation in observations:
        if observation.get("observation_status") != "observed":
            continue
        for evidence in _list(observation.get("evidence")):
            if evidence.get("temporal_status") == "confirmed_in_window":
                result.append((observation, evidence))
    return result


def _event_or_publication_date(evidence: dict[str, Any], source_index: dict[str, dict[str, Any]]) -> str:
    source = source_index.get(str(evidence.get("source_ref") or ""), {})
    return str(evidence.get("event_at") or evidence.get("published_at") or source.get("published_at") or "").strip()


def _sources_for_observation(
    observation: dict[str, Any],
    source_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    sources = _list(observation.get("sources"))
    if sources:
        return sources
    return [
        source_index[ref]
        for ref in (str(item) for item in _list_values(observation.get("source_refs")))
        if ref in source_index
    ]


def _cross_entity_known_task_count(
    tasks: list[dict[str, Any]],
    bindings: list[dict[str, Any]],
    source_index: dict[str, dict[str, Any]],
) -> int:
    binding_by_key = {(str(item.get("candidate_id")), str(item.get("source_ref"))): item for item in bindings}
    count = 0
    for task in tasks:
        if task.get("source_lane") != "known_source":
            continue
        for ref in _list_values(task.get("source_refs")):
            binding = binding_by_key.get((str(task.get("candidate_id")), str(ref)))
            source = source_index.get(str(ref), {})
            if binding and binding.get("status") == "cross_entity":
                count += 1
            elif source.get("capability") in {"identity_only", "registry"}:
                count += 1
    return count


def _transport_retry_count(report: dict[str, Any]) -> int:
    attempts = _list(report.get("provider_attempts"))
    by_task: dict[str, list[dict[str, Any]]] = {}
    for attempt in attempts:
        by_task.setdefault(str(attempt.get("task_id")), []).append(attempt)
    return sum(
        "provider_error" in [str(item.get("outcome")) for item in task_attempts]
        and "primary_retry" in [str(item.get("attempt_role")) for item in task_attempts]
        for task_attempts in by_task.values()
    )


def _unretried_transport_error_count(report: dict[str, Any]) -> int:
    attempts = _list(report.get("provider_attempts"))
    by_task: dict[str, list[dict[str, Any]]] = {}
    for attempt in attempts:
        by_task.setdefault(str(attempt.get("task_id")), []).append(attempt)
    return sum(
        "provider_error" in [str(item.get("outcome")) for item in task_attempts]
        and "primary_retry" not in [str(item.get("attempt_role")) for item in task_attempts]
        and "backup_retry" not in [str(item.get("attempt_role")) for item in task_attempts]
        for task_attempts in by_task.values()
    )


def _positive_control_matches(
    control: dict[str, Any],
    observations: list[dict[str, Any]],
    source_index: dict[str, dict[str, Any]],
) -> bool:
    for observation in observations:
        if observation.get("candidate_id") != control.get("candidate_id"):
            continue
        if observation.get("signal_code") != control.get("signal_code"):
            continue
        if observation.get("observation_status") != "observed":
            continue
        for evidence in _list(observation.get("evidence")):
            source = _source_for_evidence(observation, evidence, source_index)
            if _url_matches_control(source.get("url"), control) and _date_inside_control(evidence, source, control):
                return True
    return False


def _unknown_control_matches(
    control: dict[str, Any],
    observations: list[dict[str, Any]],
    source_index: dict[str, dict[str, Any]],
) -> bool:
    for observation in observations:
        if observation.get("candidate_id") != control.get("candidate_id"):
            continue
        if observation.get("signal_code") != control.get("signal_code"):
            continue
        if observation.get("search_status") not in {"review_needed_date_unknown", "duplicate_existing_review"}:
            continue
        if any(
            _url_matches_control(_source_for_evidence(observation, evidence, source_index).get("url"), control)
            and evidence.get("temporal_status") == "review_needed_date_unknown"
            for evidence in _list(observation.get("evidence"))
        ):
            return True
    return False


def _negative_control_matches(
    control: dict[str, Any],
    observations: list[dict[str, Any]],
    source_index: dict[str, dict[str, Any]],
    bindings: list[dict[str, Any]],
) -> bool:
    expected = str(control.get("expected_reason") or "")
    if expected == "cross_entity":
        source_refs = {
            ref for ref, source in source_index.items()
            if _url_matches_control(source.get("url"), control)
        }
        return any(
            item.get("candidate_id") == control.get("candidate_id")
            and item.get("source_ref") in source_refs
            and item.get("status") == "cross_entity"
            for item in bindings
        )
    for observation in observations:
        if observation.get("candidate_id") != control.get("candidate_id"):
            continue
        if observation.get("signal_code") != control.get("signal_code"):
            continue
        matching_evidence = [
            evidence
            for evidence in _list(observation.get("evidence"))
            if _url_matches_control(_source_for_evidence(observation, evidence, source_index).get("url"), control)
        ]
        if not matching_evidence:
            continue
        if any(evidence.get("temporal_status") == "confirmed_in_window" for evidence in matching_evidence):
            return False
        if expected and not (
            observation.get("search_status") == expected
            or observation.get("summary") == expected
            or any(evidence.get("temporal_status") == expected for evidence in matching_evidence)
        ):
            continue
        return True
    return False


def _date_inside_control(evidence: dict[str, Any], source: dict[str, Any], control: dict[str, Any]) -> bool:
    observed = str(evidence.get("event_at") or evidence.get("published_at") or source.get("published_at") or "")[:10]
    observed_end = str(evidence.get("event_end_at") or observed)[:10]
    start = str(control.get("date_start") or "")[:10]
    end = str(control.get("date_end") or start)[:10]
    return bool(observed and start and end and observed <= end and observed_end >= start)


def _republished_previous_source_count(
    observations: list[dict[str, Any]],
    *,
    source_urls: dict[str, str],
    previous_source_keys: set[str],
) -> int:
    count = 0
    for observation in observations:
        if observation.get("observation_status") != "observed" or observation.get("search_status") != "searched":
            continue
        prefix = f"{observation.get('candidate_id')}|{observation.get('signal_code')}|"
        urls = {source_urls.get(str(ref), "") for ref in observation.get("source_refs", [])}
        count += sum(f"{prefix}{url}" in previous_source_keys for url in urls if url)
    return count


def _task_observation_map(tasks: list[dict[str, Any]], observations: list[dict[str, Any]]) -> dict[tuple[str, str, str], dict[str, Any]]:
    task_by_id = {item.get("task_id"): item for item in tasks}
    return {
        (str(task.get("candidate_id")), str(task.get("signal_code")), str(task.get("source_lane"))): observation
        for observation in observations
        if (task := task_by_id.get(observation.get("task_id")))
    }


def _negative_control_metrics(
    observations: list[dict[str, Any]],
    source_index: dict[str, dict[str, Any]],
    bindings: list[dict[str, Any]],
    controls: list[dict[str, Any]],
) -> tuple[int, int]:
    tested = 0
    false_positive = 0
    for control in controls:
        if _negative_control_matches(control, observations, source_index, bindings):
            tested += 1
        false_positive += int(_control_url_confirmed(control, observations, source_index))
    return tested, false_positive


def _control_url_confirmed(
    control: dict[str, Any],
    observations: list[dict[str, Any]],
    source_index: dict[str, dict[str, Any]],
) -> bool:
    for observation in observations:
        if observation.get("candidate_id") != control.get("candidate_id"):
            continue
        if observation.get("signal_code") != control.get("signal_code"):
            continue
        for evidence in _list(observation.get("evidence")):
            source = _source_for_evidence(observation, evidence, source_index)
            if (
                _url_matches_control(source.get("url"), control)
                and evidence.get("temporal_status") == "confirmed_in_window"
            ):
                return True
    return False


def _source_for_evidence(
    observation: dict[str, Any],
    evidence: dict[str, Any],
    source_index: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    source_ref = str(evidence.get("source_ref") or "")
    for source in _list(observation.get("sources")):
        if str(source.get("source_ref") or source.get("source_id") or "") == source_ref:
            return source
    return source_index.get(source_ref, {})


def _watermark_map(value: object) -> dict[tuple[str, str, str], dict[str, Any]]:
    return {
        (str(item.get("candidate_id")), str(item.get("signal_code")), str(item.get("source_lane"))): item
        for item in _list(value)
    }


def _list(value: object) -> list[dict[str, Any]]:
    return [dict(item) for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _dict(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _list_values(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


def _canonical_url(value: object) -> str:
    return str(value or "").strip().lower().rstrip("/")


def _control_urls(control: dict[str, Any]) -> set[str]:
    values = [
        control.get("url"),
        *_list_values(control.get("accepted_urls")),
        *_list_values(control.get("urls")),
    ]
    return {_canonical_url(value) for value in values if _canonical_url(value)}


def _url_matches_control(value: object, control: dict[str, Any]) -> bool:
    return _canonical_url(value) in _control_urls(control)
