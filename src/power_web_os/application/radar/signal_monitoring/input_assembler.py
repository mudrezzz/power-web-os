"""Build immutable signal-monitoring input from a persisted public candidate surface."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any, Iterable

from power_web_os.application.radar.shared.source_cards import planner_source_cards_for_policy
from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalMonitoringBudget,
    SignalMonitoringCandidate,
    SignalMonitoringCandidateScopeMode,
    SignalMonitoringInput,
    SignalMonitoringSignalRule,
    SignalMonitoringSourcePolicy,
    SignalMonitoringWatermark,
    SignalSourceRef,
)
from power_web_os.application.radar.signal_monitoring.source_binding import (
    SignalSourceBindingService,
    apply_capability,
)
from power_web_os.application.radar.signal_monitoring.policy import bounded_policy_int, signal_source_lanes
from power_web_os.application.radar_records import (
    RadarDefinitionRecord,
    RadarRunOutputRecord,
    RadarRunRecord,
    RadarRunStatus,
    SignalMonitoringRunOutputRecord,
)


class SignalMonitoringInputError(ValueError):
    """Raised when a candidate-discovery artifact cannot form a safe monitoring snapshot."""


class SignalMonitoringInputAssembler:
    """Assemble and validate the product-safe candidate-to-signal handoff.

    Owns:
    - Source run validation, public candidate selection, definition projection,
      known-source mapping, and previous fingerprint loading.

    Does not own:
    - Provider calls, signal observation semantics, persistence transactions, or
      worker lifecycle.

    Architecture:
    docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md
    """

    def assemble(
        self,
        *,
        run_id: str,
        radar_id: str,
        source_run: RadarRunRecord,
        source_output: RadarRunOutputRecord,
        definition: RadarDefinitionRecord,
        candidate_scope_mode: SignalMonitoringCandidateScopeMode = "accepted_and_review_needed",
        candidate_ids: Iterable[str] = (),
        signal_codes: Iterable[str] = (),
        lookback_days: int | None = None,
        previous_outputs: Iterable[SignalMonitoringRunOutputRecord] = (),
        budget: SignalMonitoringBudget | None = None,
    ) -> SignalMonitoringInput:
        previous_outputs = list(previous_outputs)
        self._validate_source_run(radar_id=radar_id, source_run=source_run, source_output=source_output)
        artifact = dict(source_output.artifact_payload)
        public_candidates = self._public_candidates(artifact)
        source_index = self._source_index(artifact, public_candidates=public_candidates)
        candidates = self._candidates(
            public_candidates,
            source_index=source_index,
            candidate_scope_mode=candidate_scope_mode,
            candidate_ids=set(candidate_ids),
        )
        signals = self._signal_rules(definition.definition_payload, signal_codes=set(signal_codes))
        if not candidates:
            raise SignalMonitoringInputError("Signal monitoring candidate scope is empty.")
        if not signals:
            raise SignalMonitoringInputError("Active Radar definition has no selected signal rules.")

        known_refs = {ref for candidate in candidates for ref in candidate.source_refs}
        known_sources = [source_index[ref] for ref in sorted(known_refs) if ref in source_index]
        source_binding_decisions = self._source_binding_decisions(candidates, source_index=source_index)
        global_policy = self._global_source_policy(definition.definition_payload)
        configured_lookback, configured_basis = self._lookback_policy(definition.definition_payload)
        resolved_lookback = lookback_days or configured_lookback
        lookback_basis = "explicit_override" if lookback_days is not None else configured_basis
        if not 1 <= resolved_lookback <= 3650:
            raise SignalMonitoringInputError("Signal monitoring lookback_days must be between 1 and 3650.")

        return SignalMonitoringInput(
            run_id=run_id,
            radar_id=radar_id,
            source_candidate_run_id=source_run.run_id,
            candidate_scope_mode=candidate_scope_mode,
            candidates=candidates,
            signal_rules=signals,
            known_sources=known_sources,
            configured_sources=self._configured_sources(global_policy),
            source_policy=self._source_policy(global_policy, signals=signals),
            source_cards=planner_source_cards_for_policy(global_policy),
            budget=budget or self.smoke_budget(),
            lookback_days=resolved_lookback,
            lookback_basis=lookback_basis,
            as_of=datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
            previous_signal_fingerprints=self._previous_fingerprints(previous_outputs),
            previous_signal_source_keys=self._previous_source_keys(previous_outputs),
            previous_watermarks=self._previous_watermarks(previous_outputs),
            source_binding_decisions=source_binding_decisions,
        )

    @staticmethod
    def smoke_budget() -> SignalMonitoringBudget:
        return SignalMonitoringBudget(
            max_signal_tasks=6,
            max_signal_provider_calls=8,
            max_retries_per_task=1,
            max_signal_extraction_retries=2,
            max_signal_backup_retries=1,
            max_signal_lookback_queries=6,
            max_signal_source_verifications=12,
            allow_backup_retry=True,
        )

    @staticmethod
    def quality_budget() -> SignalMonitoringBudget:
        return SignalMonitoringBudget(
            max_signal_tasks=48,
            max_signal_provider_calls=60,
            max_retries_per_task=1,
            max_signal_extraction_retries=8,
            max_signal_backup_retries=4,
            max_signal_lookback_queries=60,
            max_signal_source_verifications=120,
            max_query_revisions_per_candidate_signal=1,
            allow_backup_retry=True,
        )

    @staticmethod
    def _validate_source_run(
        *, radar_id: str, source_run: RadarRunRecord, source_output: RadarRunOutputRecord
    ) -> None:
        if source_run.pipeline_id != "candidate_discovery":
            raise SignalMonitoringInputError("Source run must be a candidate-discovery run.")
        if source_run.radar_id != radar_id:
            raise SignalMonitoringInputError("Source run belongs to another Radar.")
        if source_run.status is not RadarRunStatus.COMPLETED:
            raise SignalMonitoringInputError("Source candidate-discovery run is not completed.")
        if source_output.run_id != source_run.run_id:
            raise SignalMonitoringInputError("Source output does not belong to the source run.")
        if source_output.artifact_payload.get("artifact_type") != "icp_radar_live_run":
            raise SignalMonitoringInputError("Source run does not contain a candidate-discovery artifact.")

    def _candidates(
        self,
        public_candidates: list[dict[str, Any]],
        *,
        source_index: dict[str, SignalSourceRef],
        candidate_scope_mode: SignalMonitoringCandidateScopeMode,
        candidate_ids: set[str],
    ) -> list[SignalMonitoringCandidate]:
        selected: list[SignalMonitoringCandidate] = []
        seen: set[str] = set()
        duplicates: set[str] = set()
        unresolved: list[str] = []
        for payload in public_candidates:
            candidate_id = str(payload.get("candidate_id") or "").strip()
            if not candidate_id or (candidate_ids and candidate_id not in candidate_ids):
                continue
            if candidate_id in seen:
                duplicates.add(candidate_id)
                continue
            if not self._in_scope(payload, candidate_scope_mode):
                continue
            refs = self._candidate_refs(payload)
            resolved = sorted(ref for ref in refs if ref in source_index)
            if not resolved:
                unresolved.append(candidate_id)
                continue
            seen.add(candidate_id)
            selected.append(SignalMonitoringCandidate(
                candidate_id=candidate_id,
                display_name=str(payload.get("name") or payload.get("display_name") or payload.get("legal_name") or candidate_id),
                legal_name=str(payload.get("legal_name") or payload.get("name") or ""),
                aliases=self._candidate_aliases(payload),
                entity_type=str(payload.get("entity_type") or "legal_entity"),  # type: ignore[arg-type]
                monitorable=True,
                review_flags=self._string_list(payload.get("review_flags")),
                source_refs=resolved,
                candidate_surface_status=str(payload.get("candidate_surface_status") or "review_needed_candidate"),
                product_acceptance_status=str(payload.get("product_acceptance_status") or "review_required"),
            ))
        if duplicates:
            raise SignalMonitoringInputError(f"Duplicate public candidate ids: {', '.join(sorted(duplicates))}.")
        if unresolved:
            raise SignalMonitoringInputError(
                f"Selected candidates have no resolvable provenance: {', '.join(sorted(unresolved))}."
            )
        if candidate_ids:
            selected_ids = {item.candidate_id for item in selected}
            missing = sorted(candidate_ids - selected_ids)
            if missing:
                raise SignalMonitoringInputError(
                    f"Requested candidates are absent or outside the selected scope: {', '.join(missing)}."
                )
        return selected

    @staticmethod
    def _in_scope(payload: dict[str, Any], mode: SignalMonitoringCandidateScopeMode) -> bool:
        surface = str(payload.get("candidate_surface_status") or "")
        product = str(payload.get("product_acceptance_status") or "")
        accepted = surface == "accepted_product_candidate" or product == "product_candidate"
        if mode == "accepted_only":
            return accepted
        return accepted or surface in {"review_needed_candidate", "accepted_product_candidate"}

    def _source_index(
        self,
        artifact: dict[str, Any],
        *,
        public_candidates: list[dict[str, Any]],
    ) -> dict[str, SignalSourceRef]:
        index: dict[str, SignalSourceRef] = {}
        for payload in self._dict_list(artifact.get("sources")):
            self._add_source(index, payload)
        for candidate in public_candidates:
            for key in ("public_evidence", "registry_evidence", "provenance", "sources"):
                for payload in self._dict_list(candidate.get(key)):
                    self._add_source(index, payload, candidate_id=str(candidate.get("candidate_id") or ""))
        execution_results = self._dict(artifact.get("run_metadata")).get("execution_results")
        for key in ("source_lifecycle", "analyzed_sources", "retrieved_sources"):
            for payload in self._dict_list(self._dict(execution_results).get(key)):
                self._add_source(index, payload)
        return index

    def _public_candidates(self, artifact: dict[str, Any]) -> list[dict[str, Any]]:
        execution_results = self._dict(self._dict(artifact.get("run_metadata")).get("execution_results"))
        visible = self._dict_list(execution_results.get("user_visible_candidates"))
        return visible or self._dict_list(artifact.get("candidates"))

    def _add_source(
        self,
        index: dict[str, SignalSourceRef],
        payload: dict[str, Any],
        *,
        candidate_id: str = "",
    ) -> None:
        ref = str(
            payload.get("source_ref") or payload.get("evidence_ref") or payload.get("ref") or payload.get("id") or ""
        ).strip()
        if not ref or ref in index:
            return
        source = SignalSourceRef(
            source_ref=ref,
            title=str(payload.get("title") or payload.get("label") or payload.get("legal_name") or ref),
            url=str(payload.get("url") or ""),
            snippet=str(payload.get("snippet") or payload.get("reason") or payload.get("fact") or ""),
            source_id=str(payload.get("source_id") or payload.get("provider") or ""),
            observed_at=str(payload.get("observed_at") or payload.get("retrieved_at") or ""),
            retrieved_at=str(payload.get("retrieved_at") or payload.get("observed_at") or ""),
            published_at=str(payload.get("published_at") or ""),
            date_basis=str(payload.get("date_basis") or "none"),  # type: ignore[arg-type]
            date_confidence=str(payload.get("date_confidence") or "weak"),  # type: ignore[arg-type]
            date_evidence=str(payload.get("date_evidence") or ""),
            lifecycle_state=str(payload.get("lifecycle_state") or "unknown"),  # type: ignore[arg-type]
            candidate_id=candidate_id or str(payload.get("candidate_id") or ""),
        )
        index[ref] = apply_capability(source)

    @staticmethod
    def _source_binding_decisions(
        candidates: list[SignalMonitoringCandidate],
        *,
        source_index: dict[str, SignalSourceRef],
    ) -> list:
        service = SignalSourceBindingService()
        result = []
        for candidate in candidates:
            for source_ref in candidate.source_refs:
                source = source_index.get(source_ref)
                if source is not None:
                    result.append(service.bind(candidate=candidate, source=source))
        return result

    def _signal_rules(self, definition: dict[str, Any], *, signal_codes: set[str]) -> list[SignalMonitoringSignalRule]:
        result: list[SignalMonitoringSignalRule] = []
        for payload in self._dict_list(definition.get("intent_signals")):
            code = str(payload.get("code") or payload.get("signal_code") or payload.get("signal_id") or "").strip()
            if not code or (signal_codes and code not in signal_codes):
                continue
            monitoring_policy = self._dict(payload.get("monitoring_policy"))
            enabled = bool(monitoring_policy.get("enabled", True))
            if not enabled:
                continue
            initial_lookback = self._optional_positive_int(
                monitoring_policy.get("initial_lookback_days") or payload.get("initial_lookback_days")
            )
            overlap = bounded_policy_int(monitoring_policy.get("incremental_overlap_days"), default=2, low=0, high=90)
            source_lanes = signal_source_lanes(monitoring_policy.get("source_lanes"))
            result.append(SignalMonitoringSignalRule(
                signal_code=code,
                label=str(payload.get("name") or payload.get("label") or code),
                description=str(payload.get("description") or ""),
                expected_evidence=self._expected_evidence(payload),
                query_template="{candidate} {signal}",
                initial_lookback_days=initial_lookback,
                enabled=enabled,
                incremental_overlap_days=overlap,
                cadence=str(monitoring_policy.get("cadence") or "manual"),
                source_lanes=source_lanes,
                policy_basis={
                    "enabled": "criterion_policy" if "enabled" in monitoring_policy else "system_default",
                    "initial_lookback_days": "criterion_policy" if initial_lookback is not None else "radar_or_system_default",
                    "incremental_overlap_days": "criterion_policy" if "incremental_overlap_days" in monitoring_policy else "system_default_2",
                    "cadence": "criterion_policy" if "cadence" in monitoring_policy else "system_default_manual",
                    "source_lanes": "criterion_policy" if "source_lanes" in monitoring_policy else "system_default_all_lanes",
                },
                source_ids=self._string_list(self._dict(payload.get("source_policy")).get("source_ids")),
            ))
        if signal_codes:
            found = {item.signal_code for item in result}
            missing = sorted(signal_codes - found)
            if missing:
                raise SignalMonitoringInputError(f"Unknown signal codes: {', '.join(missing)}.")
        return result

    def _source_policy(
        self,
        global_policy: dict[str, Any],
        *,
        signals: list[SignalMonitoringSignalRule],
    ) -> SignalMonitoringSourcePolicy:
        sources = self._dict_list(global_policy.get("sources"))
        source_ids = [str(item.get("source_id") or "") for item in sources if item.get("source_id")]
        official = [
            str(item.get("source_id"))
            for item in sources
            if item.get("source_id") and str(item.get("trust_level") or item.get("trust") or "").lower() == "high"
        ]
        criterion_source_ids = list(dict.fromkeys(source_id for rule in signals for source_id in rule.source_ids))
        return SignalMonitoringSourcePolicy(
            enabled=True,
            allowed_source_ids=source_ids,
            preferred_source_ids=criterion_source_ids,
            official_source_ids=official,
            reuse_known_sources=True,
            allow_open_web=bool(global_policy.get("allow_open_web", True)),
        )

    @staticmethod
    def _global_source_policy(definition: dict[str, Any]) -> dict[str, Any]:
        value = definition.get("global_search_policy")
        return dict(value) if isinstance(value, dict) else {}

    @staticmethod
    def _lookback_policy(definition: dict[str, Any]) -> tuple[int, str]:
        policy = definition.get("monitoring_policy")
        raw = policy.get("lookback_window") if isinstance(policy, dict) else None
        match = re.search(r"\d+", str(raw or ""))
        if match:
            return min(max(int(match.group()), 1), 3650), "radar_policy"
        return 365, "default_365"

    @staticmethod
    def _configured_sources(global_policy: dict[str, Any]) -> list[SignalSourceRef]:
        result: list[SignalSourceRef] = []
        for item in SignalMonitoringInputAssembler._dict_list(global_policy.get("sources")):
            source_id = str(item.get("source_id") or item.get("id") or "").strip()
            if not source_id:
                continue
            reference = str(item.get("reference") or item.get("url") or "").strip()
            result.append(SignalSourceRef(
                source_ref=f"configured:{source_id}",
                source_id=source_id,
                title=str(item.get("label") or source_id),
                url=reference if reference.startswith(("http://", "https://")) else "",
                snippet="Configured Radar source.",
            ))
        return result

    @staticmethod
    def _previous_fingerprints(outputs: Iterable[SignalMonitoringRunOutputRecord]) -> list[str]:
        values: set[str] = set()
        for output in outputs:
            for observation in SignalMonitoringInputAssembler._dict_list(output.artifact_payload.get("observations")):
                fingerprint = str(observation.get("fingerprint") or "").strip()
                if fingerprint:
                    values.add(fingerprint)
        return sorted(values)

    @staticmethod
    def _previous_watermarks(outputs: Iterable[SignalMonitoringRunOutputRecord]) -> list[SignalMonitoringWatermark]:
        by_key: dict[tuple[str, str, str], SignalMonitoringWatermark] = {}
        for output in outputs:
            for raw in SignalMonitoringInputAssembler._dict_list(output.artifact_payload.get("watermarks_after")):
                try:
                    item = SignalMonitoringWatermark.model_validate(raw)
                except ValueError:
                    continue
                key = (item.candidate_id, item.signal_code, item.source_lane)
                previous = by_key.get(key)
                if previous is None or item.searched_through_at > previous.searched_through_at:
                    by_key[key] = item
        return sorted(by_key.values(), key=lambda item: (item.candidate_id, item.signal_code, item.source_lane))

    @staticmethod
    def _previous_source_keys(outputs: Iterable[SignalMonitoringRunOutputRecord]) -> list[str]:
        keys: set[str] = set()
        for output in outputs:
            observations = [
                *SignalMonitoringInputAssembler._dict_list(output.artifact_payload.get("observations")),
                *SignalMonitoringInputAssembler._dict_list(output.artifact_payload.get("task_observations")),
            ]
            for observation in observations:
                search_status = str(observation.get("search_status") or "")
                observation_status = str(observation.get("observation_status") or "")
                if observation_status != "observed" and search_status not in {
                    "review_needed_date_unknown",
                    "review_needed_date_conflict",
                    "duplicate_existing_review",
                }:
                    continue
                candidate_id = str(observation.get("candidate_id") or "")
                signal_code = str(observation.get("signal_code") or "")
                for source in SignalMonitoringInputAssembler._dict_list(observation.get("sources")):
                    url = SignalMonitoringInputAssembler._canonical_url(str(source.get("url") or ""))
                    if candidate_id and signal_code and url:
                        keys.add(f"{candidate_id}|{signal_code}|{url}")
        return sorted(keys)

    @staticmethod
    def _canonical_url(value: str) -> str:
        return value.strip().lower().rstrip("/")

    @staticmethod
    def _optional_positive_int(value: Any) -> int | None:
        if isinstance(value, bool):
            return None
        try:
            parsed = int(value)
        except (TypeError, ValueError):
            return None
        return parsed if parsed > 0 else None

    @staticmethod
    def _candidate_refs(payload: dict[str, Any]) -> set[str]:
        refs: set[str] = set()
        for key in ("source_refs", "evidence_refs", "upstream_source_refs"):
            refs.update(SignalMonitoringInputAssembler._string_list(payload.get(key)))
        for key in ("public_evidence", "registry_evidence", "provenance"):
            for item in SignalMonitoringInputAssembler._dict_list(payload.get(key)):
                ref = str(item.get("source_ref") or item.get("evidence_ref") or item.get("ref") or item.get("id") or "")
                if ref:
                    refs.add(ref)
        return refs

    @staticmethod
    def _candidate_aliases(payload: dict[str, Any]) -> list[str]:
        aliases: list[str] = []
        for key in ("aliases", "alias_names", "known_aliases"):
            aliases.extend(SignalMonitoringInputAssembler._string_list(payload.get(key)))
        for key in ("legal_name", "name", "display_name"):
            value = str(payload.get(key) or "").strip()
            if value:
                aliases.append(value)
        result: list[str] = []
        seen: set[str] = set()
        for value in aliases:
            normalized = value.strip()
            if normalized and normalized.casefold() not in seen:
                seen.add(normalized.casefold())
                result.append(normalized)
        return result

    @staticmethod
    def _expected_evidence(payload: dict[str, Any]) -> list[str]:
        values = payload.get("expected_evidence")
        if isinstance(values, list):
            return [str(item) for item in values if str(item).strip()]
        trigger = payload.get("trigger_rule_group")
        return [str(item.get("description") or item.get("rule") or "") for item in SignalMonitoringInputAssembler._dict_list(SignalMonitoringInputAssembler._dict(trigger).get("rules")) if str(item.get("description") or item.get("rule") or "").strip()]

    @staticmethod
    def _dict(value: Any) -> dict[str, Any]:
        return dict(value) if isinstance(value, dict) else {}

    @staticmethod
    def _dict_list(value: Any) -> list[dict[str, Any]]:
        return [dict(item) for item in value if isinstance(item, dict)] if isinstance(value, list) else []

    @staticmethod
    def _string_list(value: Any) -> list[str]:
        return [str(item) for item in value if str(item).strip()] if isinstance(value, list) else []
