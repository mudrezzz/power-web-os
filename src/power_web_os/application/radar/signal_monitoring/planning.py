"""Deterministic multi-lane planning and backend acceptance."""

from __future__ import annotations

from dataclasses import dataclass
import re
from urllib.parse import urlparse

from power_web_os.application.radar.signal_monitoring.contracts import (
    SignalMonitoringInput,
    SignalMonitoringPlan,
    SignalMonitoringPlanAcceptance,
    SignalMonitoringSourceDecision,
    SignalMonitoringSourceStrategyResult,
    SignalSearchTask,
    SignalSourceLaneLedgerEntry,
    SignalSourceRef,
)
from power_web_os.application.radar.signal_monitoring.scheduling import (
    SignalMonitoringSchedule,
    SignalMonitoringWorkScheduler,
)
from power_web_os.application.radar.signal_monitoring.windows import SignalMonitoringWindowPolicy


@dataclass(frozen=True, slots=True)
class SignalMonitoringPlanningInput:
    monitoring_input: SignalMonitoringInput
    source_strategy: SignalMonitoringSourceStrategyResult


@dataclass(frozen=True, slots=True)
class SignalMonitoringExecutionPlan:
    search_plan: SignalMonitoringPlan
    acceptance: SignalMonitoringPlanAcceptance
    schedule: SignalMonitoringSchedule


class SignalMonitoringPlanningInputBuilder:
    """Build the immutable planning boundary for one signal run."""

    def build(
        self,
        monitoring_input: SignalMonitoringInput,
        source_strategy: SignalMonitoringSourceStrategyResult,
    ) -> SignalMonitoringPlanningInput:
        return SignalMonitoringPlanningInput(monitoring_input, source_strategy)


class SignalMonitoringSearchPlanner:
    """Build one explicit task per candidate, criterion, and selected lane."""

    def __init__(self, window_policy: SignalMonitoringWindowPolicy | None = None) -> None:
        self._window_policy = window_policy or SignalMonitoringWindowPolicy()

    def plan(self, planning_input: SignalMonitoringPlanningInput) -> SignalMonitoringPlan:
        monitoring = planning_input.monitoring_input
        selected = [item for item in planning_input.source_strategy.decisions if item.status == "selected"]
        sources = _source_index(monitoring)
        tasks: list[SignalSearchTask] = []
        for candidate in monitoring.candidates:
            for rule in monitoring.signal_rules:
                if not rule.enabled:
                    continue
                decisions = _candidate_decisions(
                    candidate.candidate_id,
                    candidate.source_refs,
                    selected,
                    rule_source_ids=rule.source_ids,
                )
                decisions = [decision for decision in decisions if decision.lane in rule.source_lanes]
                lane_decisions = [(decision.lane, decision) for decision in decisions]
                if not lane_decisions and rule.source_lanes:
                    fallback_lane = "open_web" if "open_web" in rule.source_lanes else rule.source_lanes[0]
                    lane_decisions = [(fallback_lane, None)]
                for lane_index, (lane, decision) in enumerate(lane_decisions, start=1):
                    contracts = _source_contracts(decision, sources)
                    candidate_sources = [
                        sources[ref]
                        for ref in candidate.source_refs
                        if ref in sources
                    ]
                    domains = _domain_restrictions(lane, contracts)
                    window = self._window_policy.resolve(
                        monitoring_input=monitoring,
                        candidate_id=candidate.candidate_id,
                        rule=rule,
                        source_lane=lane,
                    )
                    query, alternate_query = _queries(
                        template=rule.query_template,
                        candidate=candidate.display_name,
                        aliases=[candidate.legal_name, *candidate.aliases],
                        signal_code=rule.signal_code,
                        signal=rule.label,
                        expected=rule.expected_evidence,
                        lane=lane,
                        domains=domains,
                        contracts=contracts,
                        candidate_sources=candidate_sources,
                    )
                    tasks.append(SignalSearchTask(
                        task_id=f"signal-{candidate.candidate_id}-{rule.signal_code}-{lane}-{lane_index}",
                        candidate_id=candidate.candidate_id,
                        candidate_name=candidate.display_name,
                        candidate_aliases=[candidate.legal_name, *candidate.aliases],
                        signal_code=rule.signal_code,
                        signal_label=rule.label,
                        query=query,
                        alternate_query=alternate_query,
                        lookback_days=window.lookback_days,
                        known_source_refs=list(candidate.source_refs),
                        source_lane=lane,
                        source_ids=[decision.source_id] if decision and decision.source_id else [],
                        source_refs=list(decision.source_refs) if decision else [],
                        source_decision_ids=[decision.decision_id] if decision else [],
                        source_contracts=contracts,
                        domain_restrictions=domains,
                        required=bool(decision.required) if decision else True,
                        window_start=window.window_start,
                        window_end=window.window_end,
                        window_basis=window.basis,
                    ))
        return SignalMonitoringPlan(radar_id=monitoring.radar_id, tasks=tasks)


class SignalMonitoringPlanAcceptanceService:
    """Validate and safely repair deterministic signal-search plans."""

    def accept(
        self,
        *,
        planning_input: SignalMonitoringPlanningInput,
        plan: SignalMonitoringPlan,
    ) -> SignalMonitoringPlanAcceptance:
        corrections: list[dict[str, str]] = []
        errors: list[str] = []
        accepted: list[SignalSearchTask] = []
        rejected: list[SignalSearchTask] = []
        seen: set[tuple[str, str, str, tuple[str, ...], tuple[str, ...]]] = set()
        for task in plan.tasks:
            key = (
                task.candidate_id,
                task.signal_code,
                task.source_lane,
                tuple(task.source_refs),
                tuple(task.source_ids),
            )
            if key in seen:
                corrections.append({"type": "duplicate_task_removed", "task_id": task.task_id})
                continue
            seen.add(key)
            if task.source_lane == "known_source" and not any(item.url for item in task.source_contracts):
                errors.append(f"Known-source task {task.task_id} has no concrete URL.")
                rejected.append(task)
                continue
            if task.source_lane == "official_company" and not task.domain_restrictions:
                errors.append(f"Official task {task.task_id} has no domain restriction.")
                rejected.append(task)
                continue
            accepted.append(task)
        return SignalMonitoringPlanAcceptance(
            accepted=bool(accepted),
            tasks=accepted,
            rejected_tasks=rejected,
            corrections=corrections,
            errors=errors,
        )


class SignalMonitoringPlanningPipeline:
    """Compose planning, backend acceptance, and budget-aware scheduling."""

    def __init__(
        self,
        *,
        input_builder: SignalMonitoringPlanningInputBuilder | None = None,
        planner: SignalMonitoringSearchPlanner | None = None,
        acceptance_service: SignalMonitoringPlanAcceptanceService | None = None,
        scheduler: SignalMonitoringWorkScheduler | None = None,
    ) -> None:
        self._input_builder = input_builder or SignalMonitoringPlanningInputBuilder()
        self._planner = planner or SignalMonitoringSearchPlanner()
        self._acceptance = acceptance_service or SignalMonitoringPlanAcceptanceService()
        self._scheduler = scheduler or SignalMonitoringWorkScheduler()

    def build(
        self,
        monitoring_input: SignalMonitoringInput,
        source_strategy: SignalMonitoringSourceStrategyResult,
    ) -> SignalMonitoringExecutionPlan:
        planning_input = self._input_builder.build(monitoring_input, source_strategy)
        plan = self._planner.plan(planning_input)
        acceptance = self._acceptance.accept(planning_input=planning_input, plan=plan)
        accepted_plan = SignalMonitoringPlan(radar_id=plan.radar_id, tasks=acceptance.tasks)
        limit = monitoring_input.budget.max_signal_tasks
        if limit is None:
            limit = monitoring_input.budget.max_tasks
        schedule = self._scheduler.schedule(accepted_plan, task_limit=limit)
        rejected_ledger = [
            SignalSourceLaneLedgerEntry(
                task_id=task.task_id,
                candidate_id=task.candidate_id,
                signal_code=task.signal_code,
                source_lane=task.source_lane,
                required=task.required,
                status="not_executable",
                reason="plan_acceptance_rejected",
                source_decision_ids=list(task.source_decision_ids),
            )
            for task in acceptance.rejected_tasks
        ]
        schedule = SignalMonitoringSchedule(schedule.tasks, [*schedule.ledger, *rejected_ledger])
        return SignalMonitoringExecutionPlan(plan, acceptance, schedule)


class SignalMonitoringTaskPlanner:
    """Compatibility facade returning scheduled tasks from the planning pipeline."""

    def build_tasks(
        self,
        monitoring_input: SignalMonitoringInput,
        source_strategy_result: SignalMonitoringSourceStrategyResult,
    ) -> list[SignalSearchTask]:
        return SignalMonitoringPlanningPipeline().build(monitoring_input, source_strategy_result).schedule.tasks


def _candidate_decisions(
    candidate_id: str,
    candidate_source_refs: list[str],
    decisions: list[SignalMonitoringSourceDecision],
    *,
    rule_source_ids: list[str],
) -> list[SignalMonitoringSourceDecision]:
    candidate_refs = set(candidate_source_refs)
    known = [
        item for item in decisions
        if item.lane == "known_source"
        and item.candidate_id == candidate_id
        and item.source_refs
        and candidate_refs.intersection(item.source_refs)
    ]
    known = known[:2]
    generic = [
        item for item in decisions
        if item.lane != "known_source"
        and (
            item.lane != "signal_specific"
            or not rule_source_ids
            or item.source_id in set(rule_source_ids)
        )
    ]
    result: list[SignalMonitoringSourceDecision] = []
    seen: set[tuple[str, str, str]] = set()
    for item in [*known, *generic]:
        key = (item.lane, item.source_id, item.source_ref)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _source_index(monitoring: SignalMonitoringInput) -> dict[str, SignalSourceRef]:
    return {
        item.source_ref: item
        for item in [*monitoring.known_sources, *monitoring.configured_sources]
        if item.source_ref
    }


def _source_contracts(
    decision: SignalMonitoringSourceDecision | None,
    sources: dict[str, SignalSourceRef],
) -> list[SignalSourceRef]:
    if decision is None:
        return []
    return [sources[ref] for ref in decision.source_refs if ref in sources]


def _domain_restrictions(lane: str, contracts: list[SignalSourceRef]) -> list[str]:
    if lane != "official_company":
        return []
    result: list[str] = []
    for item in contracts:
        host = urlparse(item.url).hostname or ""
        host = host.removeprefix("www.").strip().lower()
        if host and host not in result:
            result.append(host)
    return result


def _queries(
    *,
    template: str,
    candidate: str,
    aliases: list[str],
    signal_code: str,
    signal: str,
    expected: list[str],
    lane: str,
    domains: list[str],
    contracts: list[SignalSourceRef],
    candidate_sources: list[SignalSourceRef],
) -> tuple[str, str]:
    query_signal = _query_signal_terms(
        signal_code=signal_code,
        signal=signal,
        expected=expected,
        values=[candidate, *aliases],
    )
    path_terms = _candidate_path_terms(candidate_sources)
    base_signal = " ".join(value for value in [query_signal, path_terms] if value).strip()
    base = " ".join(template.format(candidate=candidate, signal=base_signal or query_signal).split())
    alias = next(
        (
            value.strip()
            for value in aliases
            if value and value.strip() and value.strip() != candidate
        ),
        "",
    )
    evidence_terms = _expected_terms(expected, query_signal)
    alternate_base = " ".join(
        value for value in [
            template.format(candidate=alias or candidate, signal=base_signal or query_signal),
            evidence_terms,
        ]
        if value
    ).strip()
    if lane == "official_company" and domains:
        return f"site:{domains[0]} {base}", f"site:{domains[0]} {alternate_base or base}"
    if lane == "known_source" and contracts:
        return f"{base} {contracts[0].url}", f"{alternate_base or base} {contracts[0].url}"
    return base, alternate_base or base


def _query_signal_terms(
    *,
    signal_code: str,
    signal: str,
    expected: list[str],
    values: list[str],
) -> str:
    text = " ".join([signal_code, signal, *expected]).lower()
    cyrillic = any(re.search(r"[А-Яа-яЁё]", value or "") for value in values)
    if cyrillic and (
        signal_code.upper() == "S1"
        or any(marker in text for marker in ("toir", "reliability", "maintenance", "repair", "turnaround"))
    ):
        return "остановочный ремонт ТОиР пусконаладочные работы запуск первая продукция ремонтная кампания 2026"
    if cyrillic and (
        signal_code.upper() == "S2"
        or any(marker in text for marker in ("modernization", "capacity", "investment", "equipment"))
    ):
        return "модернизация строительство новое производство спецкомпонент автоматизация планы 2026"
    return " ".join(signal.split())


def _expected_terms(expected: list[str], query_signal: str) -> str:
    values = [value.strip() for value in expected[:2] if value.strip()]
    if not values:
        return ""
    joined = " ".join(values)
    return "" if joined == query_signal else joined


def _candidate_path_terms(sources: list[SignalSourceRef]) -> str:
    terms: list[str] = []
    ignored = {"upload", "iblock", "press-center", "disclosure", "products", "product", "news", "company"}
    file_suffixes = {"xls", "xlsx", "csv", "xml", "json", "pdf"}
    for source in sources:
        parsed = urlparse(source.url)
        suffix = parsed.path.rsplit(".", 1)[-1].casefold() if "." in parsed.path else ""
        if suffix in file_suffixes:
            continue
        segments = [segment for segment in parsed.path.split("/") if segment]
        for segment in segments[:2]:
            normalized = segment.strip()
            if not normalized or normalized.lower() in ignored or "." in normalized:
                continue
            if normalized not in terms:
                terms.append(normalized)
            if len(terms) >= 2:
                return " ".join(terms)
    return " ".join(terms)
