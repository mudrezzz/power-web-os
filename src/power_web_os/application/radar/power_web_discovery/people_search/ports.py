"""Provider ports owned by the people-search application stage."""

from __future__ import annotations

from typing import Protocol

from .contracts import PeopleSearchProviderResult, PeopleSearchTask, PowerWebPeopleSearchPlanningInput


class AccountRoleTitleHypothesisProvider(Protocol):
    runtime_name: str
    model_id: str

    def propose(self, planning_input: PowerWebPeopleSearchPlanningInput) -> dict[str, tuple[str, ...]]: ...


class PeopleSearchProvider(Protocol):
    runtime_name: str
    model_id: str

    def search(self, task: PeopleSearchTask) -> PeopleSearchProviderResult: ...
