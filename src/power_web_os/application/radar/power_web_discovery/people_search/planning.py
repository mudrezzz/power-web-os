"""Deterministic planning and acceptance for Power Web people search."""

from __future__ import annotations

from hashlib import sha256
import re
from urllib.parse import urlparse

from ..contracts import PowerWebHandoffSnapshot, RoleDemand
from .contracts import (
    AcceptedAccountRoleTitleHypothesis,
    AccountRoleTitleHypothesisProposal,
    PeopleSearchBudgetSettings,
    PeopleSearchTask,
    PeopleSourceLaneDecision,
    PowerWebPeopleSearchPlanningInput,
    TitleHypothesisAcceptanceDecision,
)


MANDATORY_LANES = ("official_company", "hh_public_web", "generic_web")
_PRIVATE_OR_URL = re.compile(r"https?://|www\.|@|\+?\d[\d\s()\-]{7,}", re.IGNORECASE)
_ROLE_MARKERS = {
    "chief", "director", "engineer", "manager", "head", "lead", "owner", "expert",
    "главный", "директор", "инженер", "руководитель", "начальник", "владелец",
    "эксперт", "технолог", "энергетик", "менеджер",
}


def _stable_id(prefix: str, *parts: str) -> str:
    digest = sha256("\x1f".join(parts).encode("utf-8")).hexdigest()[:20]
    return f"{prefix}-{digest}"


def _clean(value: str) -> str:
    return " ".join(value.split()).strip()


class PowerWebPeopleSearchPlanningInputBuilder:
    def build(
        self,
        handoff: PowerWebHandoffSnapshot,
        *,
        account_aliases: tuple[str, ...] = (),
        official_domains: tuple[str, ...] = (),
        official_domain_evidence_refs: tuple[str, ...] = (),
        geography: str | None = None,
        language: str = "ru",
    ) -> PowerWebPeopleSearchPlanningInput:
        demands = tuple(
            demand
            for group in handoff.product_role_demand_sets
            for demand in group.role_demands
        )
        aliases = tuple(dict.fromkeys(filter(None, (_clean(handoff.account.legal_name), *map(_clean, account_aliases)))))
        domains = tuple(dict.fromkeys(self._domain(item) for item in official_domains if self._domain(item)))
        return PowerWebPeopleSearchPlanningInput(
            handoff_id=handoff.handoff_id,
            account_id=handoff.account.account_id,
            account_legal_name=handoff.account.legal_name,
            account_aliases=aliases,
            official_domains=domains,
            official_domain_evidence_refs=tuple(dict.fromkeys(filter(None, map(_clean, official_domain_evidence_refs)))),
            geography=_clean(geography) if geography else None,
            language=language,
            source_candidate_run_id=handoff.source_candidate_run_id,
            source_signal_run_id=handoff.source_signal_run_id,
            role_demands=demands,
            as_of=handoff.as_of,
        )

    @staticmethod
    def _domain(value: str) -> str:
        candidate = value.strip().lower()
        if "://" in candidate:
            candidate = urlparse(candidate).hostname or ""
        return candidate.removeprefix("www.").strip("./")


class AccountRoleTitleHypothesisPlanner:
    def proposals_from_values(
        self,
        planning_input: PowerWebPeopleSearchPlanningInput,
        values_by_demand: dict[str, tuple[str, ...]],
        *,
        max_per_role: int = 5,
    ) -> tuple[AccountRoleTitleHypothesisProposal, ...]:
        proposals: list[AccountRoleTitleHypothesisProposal] = []
        for demand in planning_input.role_demands:
            values = values_by_demand.get(demand.demand_id, ())[:max_per_role]
            for position, value in enumerate(values):
                proposals.append(self._proposal(planning_input, demand, value, position, "provider"))
            proposals.append(self._proposal(
                planning_input,
                demand,
                demand.display_name,
                len(values),
                "deterministic_fallback",
            ))
        return tuple(proposals)

    @staticmethod
    def _proposal(
        planning_input: PowerWebPeopleSearchPlanningInput,
        demand: RoleDemand,
        value: str,
        position: int,
        origin: str,
    ) -> AccountRoleTitleHypothesisProposal:
        return AccountRoleTitleHypothesisProposal(
            proposal_id=_stable_id("title-proposal", demand.demand_id, str(position), value, origin),
            demand_id=demand.demand_id,
            account_id=planning_input.account_id,
            product_id=demand.product_id,
            sales_playbook_version_id=demand.sales_playbook_version_id,
            buying_role_policy_version_id=demand.buying_role_policy_version_id,
            semantic_role_code=demand.semantic_role_code,
            title_or_function=_clean(value),
            language=planning_input.language,
            origin=origin,
        )


class AccountRoleTitleHypothesisAcceptanceService:
    def accept(
        self,
        planning_input: PowerWebPeopleSearchPlanningInput,
        proposals: tuple[AccountRoleTitleHypothesisProposal, ...],
        *,
        max_per_role: int = 3,
    ) -> tuple[
        tuple[AcceptedAccountRoleTitleHypothesis, ...],
        tuple[TitleHypothesisAcceptanceDecision, ...],
    ]:
        demands = {item.demand_id: item for item in planning_input.role_demands}
        accepted: list[AcceptedAccountRoleTitleHypothesis] = []
        decisions: list[TitleHypothesisAcceptanceDecision] = []
        seen: dict[str, set[str]] = {item.demand_id: set() for item in planning_input.role_demands}
        counts: dict[str, int] = {item.demand_id: 0 for item in planning_input.role_demands}
        for proposal in proposals:
            demand = demands.get(proposal.demand_id)
            reason = self._rejection_reason(planning_input, proposal, demand, seen, counts, max_per_role)
            if reason:
                decisions.append(TitleHypothesisAcceptanceDecision(
                    proposal_id=proposal.proposal_id,
                    demand_id=proposal.demand_id,
                    accepted=False,
                    reason_code=reason,
                ))
                continue
            assert demand is not None
            normalized = proposal.title_or_function.casefold()
            seen[demand.demand_id].add(normalized)
            counts[demand.demand_id] += 1
            hypothesis_id = _stable_id("title-hypothesis", proposal.proposal_id)
            accepted.append(AcceptedAccountRoleTitleHypothesis(
                hypothesis_id=hypothesis_id,
                proposal_id=proposal.proposal_id,
                demand_id=demand.demand_id,
                account_id=planning_input.account_id,
                product_id=demand.product_id,
                sales_playbook_version_id=demand.sales_playbook_version_id,
                buying_role_policy_version_id=demand.buying_role_policy_version_id,
                semantic_role_code=demand.semantic_role_code,
                title_or_function=proposal.title_or_function,
                language=proposal.language,
                origin=proposal.origin,
            ))
            decisions.append(TitleHypothesisAcceptanceDecision(
                proposal_id=proposal.proposal_id,
                demand_id=demand.demand_id,
                accepted=True,
                reason_code="accepted",
                hypothesis_id=hypothesis_id,
            ))
        missing = set(demands) - {item.demand_id for item in accepted}
        if missing:
            raise ValueError(f"accepted hypotheses missing deterministic fallback for: {sorted(missing)}")
        return tuple(accepted), tuple(decisions)

    @staticmethod
    def _rejection_reason(planning_input, proposal, demand, seen, counts, max_per_role) -> str | None:
        if demand is None:
            return "unknown_demand"
        expected = (
            planning_input.account_id,
            demand.product_id,
            demand.sales_playbook_version_id,
            demand.buying_role_policy_version_id,
            demand.semantic_role_code,
        )
        actual = (
            proposal.account_id,
            proposal.product_id,
            proposal.sales_playbook_version_id,
            proposal.buying_role_policy_version_id,
            proposal.semantic_role_code,
        )
        if actual != expected:
            return "lineage_or_role_mismatch"
        value = _clean(proposal.title_or_function)
        if not value:
            return "empty"
        if _PRIVATE_OR_URL.search(value):
            return "private_contact_or_url"
        words = value.split()
        if (
            2 <= len(words) <= 3
            and all(word[:1].isupper() and word[1:].islower() for word in words)
            and not ({word.casefold() for word in words} & _ROLE_MARKERS)
        ):
            return "probable_person_name"
        if value.casefold() in seen[demand.demand_id]:
            return "duplicate"
        if counts[demand.demand_id] >= max_per_role:
            return "accepted_limit"
        return None


class PeopleSearchSourceLaneStrategy:
    def decide(
        self,
        planning_input: PowerWebPeopleSearchPlanningInput,
    ) -> tuple[PeopleSourceLaneDecision, ...]:
        decisions: list[PeopleSourceLaneDecision] = []
        for demand in planning_input.role_demands:
            for lane in MANDATORY_LANES:
                domains: tuple[str, ...] = ()
                status = "scheduled"
                reason = "mandatory_lane_scheduled"
                if lane == "official_company":
                    domains = planning_input.official_domains[:1]
                    if not domains:
                        status = "not_executable"
                        reason = "official_domain_missing"
                    else:
                        reason = "mandatory_lane_scheduled_from_evidence_backed_domain"
                elif lane == "hh_public_web":
                    domains = ("hh.ru",)
                decisions.append(PeopleSourceLaneDecision(
                    decision_id=_stable_id("people-lane", demand.demand_id, lane),
                    demand_id=demand.demand_id,
                    account_id=planning_input.account_id,
                    product_id=demand.product_id,
                    sales_playbook_version_id=demand.sales_playbook_version_id,
                    buying_role_policy_version_id=demand.buying_role_policy_version_id,
                    semantic_role_code=demand.semantic_role_code,
                    lane=lane,
                    status=status,
                    reason_code=reason,
                    domain_restrictions=domains,
                ))
        return tuple(decisions)


class PeopleSearchRetrievalPlanCompiler:
    def compile(
        self,
        planning_input: PowerWebPeopleSearchPlanningInput,
        hypotheses: tuple[AcceptedAccountRoleTitleHypothesis, ...],
        decisions: tuple[PeopleSourceLaneDecision, ...],
        *,
        settings: PeopleSearchBudgetSettings,
    ) -> tuple[PeopleSearchTask, ...]:
        by_demand: dict[str, list[AcceptedAccountRoleTitleHypothesis]] = {}
        for hypothesis in hypotheses:
            by_demand.setdefault(hypothesis.demand_id, []).append(hypothesis)
        tasks: list[PeopleSearchTask] = []
        for decision in decisions:
            if decision.status != "scheduled":
                continue
            if len(tasks) >= settings.max_initial_tasks:
                break
            role_hypotheses = by_demand[decision.demand_id]
            titles = tuple(item.title_or_function for item in role_hypotheses)
            query = self._query(planning_input, decision.lane, titles)
            tasks.append(PeopleSearchTask(
                task_id=_stable_id("people-task", decision.decision_id, query),
                decision_id=decision.decision_id,
                demand_id=decision.demand_id,
                account_id=decision.account_id,
                product_id=decision.product_id,
                sales_playbook_version_id=decision.sales_playbook_version_id,
                buying_role_policy_version_id=decision.buying_role_policy_version_id,
                semantic_role_code=decision.semantic_role_code,
                hypothesis_ids=tuple(item.hypothesis_id for item in role_hypotheses),
                lane=decision.lane,
                query=query,
                domain_restrictions=decision.domain_restrictions,
            ))
        return tuple(tasks)

    @staticmethod
    def _query(planning_input, lane: str, titles: tuple[str, ...]) -> str:
        account = planning_input.account_aliases[0]
        role_terms = " OR ".join(f'"{item}"' for item in titles)
        geography = f' "{planning_input.geography}"' if planning_input.geography else ""
        if lane == "official_company":
            return f'"{account}" ({role_terms}) руководство команда контакты'
        if lane == "hh_public_web":
            return f'"{account}" ({role_terms}) резюме профиль{geography}'
        return f'"{account}" ({role_terms}) руководитель эксперт интервью профиль{geography}'


class PeopleSearchQueryRevisionService:
    """Builds one broader, auditable query without changing lane obligations."""

    def revise(
        self,
        task: PeopleSearchTask,
        planning_input: PowerWebPeopleSearchPlanningInput,
        hypotheses: tuple[AcceptedAccountRoleTitleHypothesis, ...],
    ) -> PeopleSearchTask:
        if task.revision >= 1:
            raise ValueError("people-search task already uses its bounded query revision")
        role_titles = tuple(
            item.title_or_function for item in hypotheses if item.demand_id == task.demand_id
        )
        account = planning_input.account_aliases[-1]
        title = role_titles[0]
        geography = f" {planning_input.geography}" if planning_input.geography else ""
        if task.lane == "official_company":
            query = f'"{account}" "{title}" руководство команда директор'
        elif task.lane == "hh_public_web":
            query = f'"{account}" "{title}" резюме руководитель инженер{geography}'
        else:
            query = f'"{account}" "{title}" директор руководитель начальник эксперт{geography}'
        return task.model_copy(update={
            "task_id": _stable_id("people-task-revision", task.task_id, query),
            "query": query,
            "revision": 1,
        })
