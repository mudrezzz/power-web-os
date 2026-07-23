"""Composition service for hypothesis planning and deterministic retrieval planning."""

from __future__ import annotations

from dataclasses import dataclass

from .contracts import (
    AcceptedAccountRoleTitleHypothesis,
    AccountRoleTitleHypothesisProposal,
    PeopleSearchBudgetSettings,
    PeopleSearchTask,
    PeopleSourceLaneDecision,
    PowerWebPeopleSearchPlanningInput,
    TitleHypothesisAcceptanceDecision,
)
from .planning import (
    AccountRoleTitleHypothesisAcceptanceService,
    AccountRoleTitleHypothesisPlanner,
    PeopleSearchRetrievalPlanCompiler,
    PeopleSearchSourceLaneStrategy,
)
from .ports import AccountRoleTitleHypothesisProvider


@dataclass(frozen=True)
class PeopleSearchPlan:
    proposals: tuple[AccountRoleTitleHypothesisProposal, ...]
    accepted_hypotheses: tuple[AcceptedAccountRoleTitleHypothesis, ...]
    acceptance: tuple[TitleHypothesisAcceptanceDecision, ...]
    lane_decisions: tuple[PeopleSourceLaneDecision, ...]
    tasks: tuple[PeopleSearchTask, ...]
    hypothesis_provider_calls: int
    diagnostics: tuple[str, ...]


class PeopleSearchPlanningService:
    def __init__(
        self,
        *,
        provider: AccountRoleTitleHypothesisProvider | None,
        settings: PeopleSearchBudgetSettings,
    ) -> None:
        self._provider = provider
        self._settings = settings
        self._planner = AccountRoleTitleHypothesisPlanner()
        self._acceptance = AccountRoleTitleHypothesisAcceptanceService()
        self._strategy = PeopleSearchSourceLaneStrategy()
        self._compiler = PeopleSearchRetrievalPlanCompiler()

    def build(self, planning_input: PowerWebPeopleSearchPlanningInput) -> PeopleSearchPlan:
        if len(planning_input.role_demands) > self._settings.max_role_demands:
            raise ValueError("people-search role demand budget exceeded")
        values: dict[str, tuple[str, ...]] = {}
        calls = 0
        diagnostics: list[str] = []
        if self._provider is not None:
            for attempt in range(1, self._settings.max_hypothesis_provider_calls + 1):
                calls += 1
                try:
                    proposed = self._provider.propose(planning_input)
                    values = self._validated_values(planning_input, proposed)
                    break
                except (TypeError, ValueError):
                    diagnostics.append(f"hypothesis_schema_retry:{attempt}")
        if not values:
            diagnostics.append("deterministic_hypothesis_fallback_used")
        proposals = self._planner.proposals_from_values(
            planning_input,
            values,
            max_per_role=self._settings.max_proposed_hypotheses_per_role,
        )
        accepted, acceptance = self._acceptance.accept(
            planning_input,
            proposals,
            max_per_role=self._settings.max_accepted_hypotheses_per_role,
        )
        decisions = self._strategy.decide(planning_input)
        tasks = self._compiler.compile(
            planning_input,
            accepted,
            decisions,
            settings=self._settings,
        )
        return PeopleSearchPlan(
            proposals=proposals,
            accepted_hypotheses=accepted,
            acceptance=acceptance,
            lane_decisions=decisions,
            tasks=tasks,
            hypothesis_provider_calls=calls,
            diagnostics=tuple(diagnostics),
        )

    def _validated_values(self, planning_input, proposed):
        if not isinstance(proposed, dict):
            raise TypeError("hypothesis provider result must be a mapping")
        demand_ids = {item.demand_id for item in planning_input.role_demands}
        if set(proposed) - demand_ids:
            raise ValueError("hypothesis provider introduced unknown demand ids")
        result: dict[str, tuple[str, ...]] = {}
        for demand_id, values in proposed.items():
            if not isinstance(values, tuple) or not all(isinstance(item, str) for item in values):
                raise TypeError("hypothesis values must be tuples of strings")
            result[demand_id] = values[: self._settings.max_proposed_hypotheses_per_role]
        return result
