from __future__ import annotations

from power_web_os.domain import AccessPlan, AccessRoute, Account, Playbook, PowerWebRole, Signal


class DeterministicAccessPlanner:
    """Baseline explainable planner before LangGraph agent orchestration is added."""

    def build_plan(self, account: Account, playbook: Playbook, *, limit: int = 3) -> AccessPlan:
        candidates: list[AccessRoute] = []

        if "partner_intro" in playbook.allowed_routes:
            partner = self._find_role(account.roles, relation="partner")
            if partner is not None:
                candidates.append(self._partner_intro(account, playbook, partner))

        if "technical_benchmark" in playbook.allowed_routes:
            technical_role = self._find_role(account.roles, role_contains=("data", "it", "tech"))
            hiring_signal = self._find_signal(account.signals, "hiring")
            if technical_role is not None and hiring_signal is not None:
                candidates.append(self._technical_benchmark(account, playbook, technical_role, hiring_signal))

        if "procurement_discovery" in playbook.allowed_routes:
            procurement_signal = self._find_signal(account.signals, "procurement")
            if procurement_signal is not None:
                candidates.append(self._procurement_discovery(account, playbook, procurement_signal))

        if "dark_stakeholder_discovery" in playbook.allowed_routes and account.missing_roles:
            candidates.append(self._dark_stakeholder_discovery(account, playbook))

        ranked = tuple(sorted(candidates, key=lambda item: item.score, reverse=True)[:limit])
        return AccessPlan(
            account_id=account.account_id,
            account_name=account.name,
            routes=ranked,
            unresolved_gaps=account.missing_roles,
        )

    def _partner_intro(self, account: Account, playbook: Playbook, partner: PowerWebRole) -> AccessRoute:
        score = self._score(account.icp_fit, partner.influence, self._asset_bonus(playbook, "partner_case"))
        return AccessRoute(
            route_type="partner_intro",
            title="Request partner intro",
            score=score,
            reason=f"{partner.person_name or partner.role} is connected to the account as {partner.relation}.",
            risk="Partner may be aligned with an incumbent competitor.",
            owner="Partner Manager",
            evidence_refs=self._evidence_refs(account.signals),
            expected_state_change="partner_route: hypothesis -> verified",
            requires_human_review=self._requires_review(playbook, "partner_intro"),
        )

    def _technical_benchmark(
        self,
        account: Account,
        playbook: Playbook,
        role: PowerWebRole,
        signal: Signal,
    ) -> AccessRoute:
        score = self._score(account.icp_fit, role.influence, signal.strength, self._asset_bonus(playbook, "benchmark"))
        return AccessRoute(
            route_type="technical_benchmark",
            title="Invite technical stakeholder to a benchmark",
            score=score,
            reason=f"{signal.summary}; {role.person_name or role.role} can become a technical champion.",
            risk="Economic buyer is not confirmed yet.",
            owner="Account Executive",
            evidence_refs=self._evidence_refs((signal,)),
            expected_state_change=f"{role.role}: identified -> engaged / champion_candidate",
            requires_human_review=self._requires_review(playbook, "technical_benchmark"),
        )

    def _procurement_discovery(self, account: Account, playbook: Playbook, signal: Signal) -> AccessRoute:
        score = self._score(account.icp_fit, signal.strength, 0.55)
        return AccessRoute(
            route_type="procurement_discovery",
            title="Map procurement path before outreach",
            score=score,
            reason=signal.summary,
            risk="Formal route can be slow and may expose the team too late.",
            owner="SDR",
            evidence_refs=self._evidence_refs((signal,)),
            expected_state_change="procurement_role: unknown -> identified",
            requires_human_review=self._requires_review(playbook, "procurement_discovery"),
        )

    def _dark_stakeholder_discovery(self, account: Account, playbook: Playbook) -> AccessRoute:
        score = self._score(account.icp_fit, 0.5, 0.45)
        missing = ", ".join(account.missing_roles)
        return AccessRoute(
            route_type="dark_stakeholder_discovery",
            title="Research missing stakeholders before a direct move",
            score=score,
            reason=f"Missing roles must be surfaced before outreach: {missing}.",
            risk="Premature outreach can look irrelevant.",
            owner="RevOps",
            evidence_refs=self._evidence_refs(account.signals),
            expected_state_change="missing_roles: unknown -> research_queue",
            requires_human_review=self._requires_review(playbook, "dark_stakeholder_discovery"),
        )

    @staticmethod
    def _find_role(
        roles: tuple[PowerWebRole, ...],
        *,
        relation: str | None = None,
        role_contains: tuple[str, ...] = (),
    ) -> PowerWebRole | None:
        for role in roles:
            if relation is not None and role.relation == relation:
                return role
            if role_contains and any(token in role.role.lower() for token in role_contains):
                return role
        return None

    @staticmethod
    def _find_signal(signals: tuple[Signal, ...], kind: str) -> Signal | None:
        return next((signal for signal in signals if signal.kind == kind), None)

    @staticmethod
    def _score(*factors: float) -> int:
        normalized = sum(max(0.0, min(1.0, factor)) for factor in factors) / len(factors)
        return round(normalized * 100)

    @staticmethod
    def _asset_bonus(playbook: Playbook, token: str) -> float:
        return 0.85 if any(token in asset for asset in playbook.available_assets) else 0.45

    @staticmethod
    def _requires_review(playbook: Playbook, route_type: str) -> bool:
        return route_type in playbook.required_review_for or "all" in playbook.required_review_for

    @staticmethod
    def _evidence_refs(signals: tuple[Signal, ...]) -> tuple[str, ...]:
        refs: list[str] = []
        for signal in signals:
            refs.extend(evidence.source for evidence in signal.evidence)
        return tuple(refs)
