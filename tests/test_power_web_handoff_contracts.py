from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from power_web_os.application.radar.power_web_discovery.contracts import (
    CandidateHandoffSource,
    PowerWebHandoffSnapshot,
    PowerWebSignalContextSnapshot,
    ProductHandoffSource,
    RadarPowerWebPolicyVersion,
    SemanticRoleSnapshot,
    SignalOutcomeSnapshot,
)
from power_web_os.application.radar.power_web_discovery.handoff import (
    AccountIdentitySnapshotFactory,
    PowerWebHandoffError,
    PowerWebHandoffService,
    PowerWebSignalContextSelector,
    RoleDemandCompiler,
    next_policy_version,
)


NOW = datetime(2026, 7, 21, 12, 0, tzinfo=UTC)


class MemoryPolicyRepository:
    def __init__(self, policy: RadarPowerWebPolicyVersion | None = None) -> None:
        self.policy = policy
        self.versions: list[RadarPowerWebPolicyVersion] = [policy] if policy else []

    def get_active(self, radar_id: str) -> RadarPowerWebPolicyVersion | None:
        return self.policy if self.policy and self.policy.radar_id == radar_id else None

    def list_versions(self, radar_id: str) -> tuple[RadarPowerWebPolicyVersion, ...]:
        return tuple(item for item in self.versions if item.radar_id == radar_id)

    def save(self, policy: RadarPowerWebPolicyVersion) -> RadarPowerWebPolicyVersion:
        self.policy = policy
        self.versions.append(policy)
        return policy


class MemoryHandoffRepository:
    def __init__(self) -> None:
        self.items: list[PowerWebHandoffSnapshot] = []

    def get(self, handoff_id: str) -> PowerWebHandoffSnapshot | None:
        return next((item for item in self.items if item.handoff_id == handoff_id), None)

    def find_by_idempotency_key(self, key: str) -> PowerWebHandoffSnapshot | None:
        return next((item for item in self.items if item.idempotency_key == key), None)

    def create(self, handoff: PowerWebHandoffSnapshot) -> PowerWebHandoffSnapshot:
        self.items.append(handoff)
        return handoff

    def list_for_candidate(self, *, radar_id: str, source_candidate_run_id: str, candidate_id: str):
        return tuple(
            item for item in self.items
            if item.radar_id == radar_id
            and item.source_candidate_run_id == source_candidate_run_id
            and item.source_candidate_id == candidate_id
        )


class MemoryCandidateReader:
    def __init__(self, candidate: CandidateHandoffSource | None) -> None:
        self.candidate = candidate

    def get_candidate(self, *, radar_id: str, source_candidate_run_id: str, candidate_id: str):
        item = self.candidate
        if item and (item.radar_id, item.source_candidate_run_id, item.candidate_id) == (
            radar_id, source_candidate_run_id, candidate_id
        ):
            return item
        return None


class MemoryProductReader:
    def __init__(self, *products: ProductHandoffSource) -> None:
        self.products = {item.product_id: item for item in products}

    def get_active_product(self, product_id: str) -> ProductHandoffSource | None:
        return self.products.get(product_id)


class MemorySignalReader:
    def __init__(self, *contexts: PowerWebSignalContextSnapshot) -> None:
        self.contexts = contexts

    def list_candidate_contexts(self, *, radar_id: str, source_candidate_run_id: str, candidate_id: str):
        return tuple(
            item for item in self.contexts
            if item.radar_id == radar_id
            and item.source_candidate_run_id == source_candidate_run_id
            and item.candidate_id == candidate_id
        )


def _roles(count: int, *, shared_first: bool = False) -> tuple[SemanticRoleSnapshot, ...]:
    return tuple(
        SemanticRoleSnapshot(
            role_code="economic_sponsor" if shared_first and index == 0 else f"role_{index}",
            display_name=f"Role {index}",
            responsibility=f"Responsibility {index}",
            required=index < max(1, count - 2),
            priority="high" if index < max(1, count - 2) else "normal",
            scope="account",
        )
        for index in range(count)
    )


def _product(product_id: str, role_count: int, *, shared_first: bool = False) -> ProductHandoffSource:
    return ProductHandoffSource(
        product_id=product_id,
        lifecycle="active",
        sales_playbook_version_id=f"playbook-{product_id}-v1",
        product_definition_version_id=f"definition-{product_id}-v1",
        buying_role_policy_version_id=f"roles-{product_id}-v1",
        product_code=product_id.removeprefix("product-"),
        name=product_id,
        roles=_roles(role_count, shared_first=shared_first),
    )


def _candidate(*, review: bool = False, inn: str | None = "7700000000", evidence: bool = True):
    return CandidateHandoffSource(
        radar_id="radar-1",
        source_candidate_run_id="radar-run-1",
        run_pipeline_id="candidate_discovery",
        run_status="completed",
        candidate_id="candidate-1",
        legal_name="Example Plant",
        candidate_surface_status="review_needed_candidate" if review else "accepted_product_candidate",
        product_acceptance_status="review_required" if review else "product_candidate",
        inn=inn,
        evidence_refs=("source-1",) if evidence else (),
    )


def _service(*, candidate=None, signals=()):
    policy = next_policy_version(
        radar_id="radar-1",
        product_ids=("product-smartdiagnostics", "product-energy"),
        created_by="tester",
        previous=None,
        now=NOW,
    )
    handoffs = MemoryHandoffRepository()
    service = PowerWebHandoffService(
        policy_repository=MemoryPolicyRepository(policy),
        handoff_repository=handoffs,
        candidate_reader=MemoryCandidateReader(candidate or _candidate()),
        product_reader=MemoryProductReader(
            _product("product-smartdiagnostics", 8, shared_first=True),
            _product("product-energy", 6, shared_first=True),
        ),
        signal_reader=MemorySignalReader(*signals),
    )
    return service, handoffs


def test_radar_product_policy_is_ordered_and_versioned() -> None:
    first = next_policy_version(
        radar_id="radar-1", product_ids=("product-a", "product-b"), created_by="u", previous=None, now=NOW
    )
    second = next_policy_version(
        radar_id="radar-1", product_ids=("product-b",), created_by="u", previous=first, now=NOW
    )
    assert first.version_number == 1
    assert [item.product_id for item in first.product_bindings] == ["product-a", "product-b"]
    assert second.version_number == 2
    with pytest.raises(PowerWebHandoffError, match="duplicate_product_binding"):
        next_policy_version(
            radar_id="radar-1", product_ids=("product-a", "product-a"), created_by="u", previous=second
        )


def test_role_demands_freeze_product_versions() -> None:
    service, _ = _service()
    handoff = service.create(
        radar_id="radar-1", source_candidate_run_id="radar-run-1", candidate_id="candidate-1",
        product_ids=None, include_latest_signal_context=True, reviewer=None, acknowledgement_comment=None,
        idempotency_key="all-products", requester="tester", now=NOW,
    )
    assert handoff.role_demand_count == 14
    assert [len(item.role_demands) for item in handoff.product_role_demand_sets] == [8, 6]
    assert handoff.product_role_demand_sets[0].product.sales_playbook_version_id.endswith("-v1")


def test_review_needed_candidate_requires_acknowledgement() -> None:
    service, _ = _service(candidate=_candidate(review=True))
    with pytest.raises(PowerWebHandoffError, match="review_needed_acknowledgement_required"):
        service.create(
            radar_id="radar-1", source_candidate_run_id="radar-run-1", candidate_id="candidate-1",
            product_ids=None, include_latest_signal_context=False, reviewer=None, acknowledgement_comment=None,
            idempotency_key="review", requester="tester", now=NOW,
        )
    handoff = service.create(
        radar_id="radar-1", source_candidate_run_id="radar-run-1", candidate_id="candidate-1",
        product_ids=None, include_latest_signal_context=False, reviewer="reviewer", acknowledgement_comment="Proceed",
        idempotency_key="review-ok", requester="tester", now=NOW,
    )
    assert handoff.review_needed_acknowledgement is not None
    assert handoff.review_needed_acknowledgement.reviewer == "reviewer"


def test_source_less_candidate_is_rejected() -> None:
    service, _ = _service(candidate=_candidate(evidence=False))
    with pytest.raises(PowerWebHandoffError, match="candidate_provenance_missing"):
        service.create(
            radar_id="radar-1", source_candidate_run_id="radar-run-1", candidate_id="candidate-1",
            product_ids=None, include_latest_signal_context=False, reviewer=None, acknowledgement_comment=None,
            idempotency_key="no-source", requester="tester", now=NOW,
        )


def test_account_identity_prefers_inn_and_scopes_provisional_ids() -> None:
    factory = AccountIdentitySnapshotFactory()
    stable = factory.create(_candidate(inn="77 000 000 00"))
    provisional = factory.create(_candidate(inn=None))
    another_run = factory.create(_candidate(inn=None).model_copy(update={"source_candidate_run_id": "radar-run-2"}))
    assert stable.account_id == "account-inn-7700000000"
    assert stable.identity_status == "stable"
    assert provisional.identity_status == "provisional"
    assert provisional.account_id != another_run.account_id


def test_role_demand_contract_excludes_search_inventions() -> None:
    schema = RoleDemandCompiler().compile(_product("product-a", 1)).role_demands[0].model_dump()
    for forbidden in ("title", "aliases", "queries", "url", "expected_evidence", "reason", "access_playbook"):
        assert forbidden not in schema


def test_equal_role_codes_from_two_products_are_not_merged() -> None:
    service, _ = _service()
    handoff = service.create(
        radar_id="radar-1", source_candidate_run_id="radar-run-1", candidate_id="candidate-1",
        product_ids=None, include_latest_signal_context=False, reviewer=None, acknowledgement_comment=None,
        idempotency_key="roles", requester="tester", now=NOW,
    )
    shared = [
        demand for group in handoff.product_role_demand_sets for demand in group.role_demands
        if demand.semantic_role_code == "economic_sponsor"
    ]
    assert len(shared) == 2
    assert len({item.demand_id for item in shared}) == 2


def test_signal_selector_uses_latest_matching_candidate_scope() -> None:
    older = PowerWebSignalContextSnapshot(
        signal_run_id="signal-run-old", radar_id="radar-1", source_candidate_run_id="radar-run-1",
        candidate_id="candidate-1", completed_at=NOW - timedelta(days=1),
    )
    latest = older.model_copy(update={"signal_run_id": "signal-run-latest", "completed_at": NOW})
    assert PowerWebSignalContextSelector().select((latest, older)) == latest
    service, _ = _service(signals=(older, latest))
    handoff = service.create(
        radar_id="radar-1", source_candidate_run_id="radar-run-1", candidate_id="candidate-1",
        product_ids=("product-smartdiagnostics",), include_latest_signal_context=True,
        reviewer=None, acknowledgement_comment=None, idempotency_key="signal", requester="tester", now=NOW,
    )
    assert handoff.source_signal_run_id == "signal-run-latest"
    assert handoff.role_demand_count == 8


def test_signal_context_is_optional() -> None:
    service, _ = _service()
    handoff = service.create(
        radar_id="radar-1", source_candidate_run_id="radar-run-1", candidate_id="candidate-1",
        product_ids=("product-smartdiagnostics",), include_latest_signal_context=True,
        reviewer=None, acknowledgement_comment=None, idempotency_key="no-signal", requester="tester", now=NOW,
    )
    assert handoff.signal_context is None
    assert handoff.role_demand_count == 8
