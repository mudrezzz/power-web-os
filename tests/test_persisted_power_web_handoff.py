from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import pytest

from power_web_os.application.radar.lifecycle.records import RadarRecord, RadarRunRecord, RadarRunStatus
from power_web_os.application.radar.power_web_discovery.contracts import (
    AccountIdentitySnapshot,
    PowerWebHandoffSnapshot,
    ProductRoleDemandSet,
    ProductSnapshot,
    RadarProductBinding,
    RadarPowerWebPolicyVersion,
    RoleDemand,
)
from power_web_os.persistence import (
    Base,
    SqlAlchemyPowerWebHandoffRepository,
    SqlAlchemyRadarPowerWebPolicyRepository,
    SqlAlchemyRadarRepository,
    SqlAlchemyRadarRunRepository,
    create_database_engine,
    create_session_factory,
    session_scope,
)
from power_web_os.persistence.models import ProductModel


NOW = datetime(2026, 7, 22, 10, 0, tzinfo=UTC)


def _url(path: Path) -> str:
    return f"sqlite:///{path.as_posix()}"


def _handoff(policy_id: str) -> PowerWebHandoffSnapshot:
    product = ProductSnapshot(
        product_id="product-a",
        product_code="a",
        name="Product A",
        sales_playbook_version_id="playbook-v1",
        product_definition_version_id="product-v1",
        buying_role_policy_version_id="roles-v1",
    )
    demand = RoleDemand(
        demand_id="demand-1",
        product_id="product-a",
        sales_playbook_version_id="playbook-v1",
        buying_role_policy_version_id="roles-v1",
        semantic_role_code="owner",
        display_name="Owner",
        responsibility="Owns the outcome.",
        required=True,
        priority="high",
        scope="account",
    )
    return PowerWebHandoffSnapshot(
        handoff_id="power-web-handoff-1",
        radar_id="radar-a",
        radar_power_web_policy_version_id=policy_id,
        source_candidate_run_id="radar-run-a",
        source_candidate_id="candidate-a",
        account=AccountIdentitySnapshot(
            account_id="account-inn-7700000000",
            identity_status="stable",
            identity_basis="inn",
            legal_name="Account A",
            entity_type="legal_entity",
            inn="7700000000",
            evidence_refs=("source-a",),
            source_candidate_run_id="radar-run-a",
            source_candidate_id="candidate-a",
        ),
        product_role_demand_sets=(ProductRoleDemandSet(product=product, role_demands=(demand,)),),
        as_of=NOW,
        created_at=NOW,
        created_by="tester",
        idempotency_key="handoff-key",
        request_fingerprint="fingerprint",
    )


def test_handoff_is_immutable_and_idempotent(tmp_path: Path) -> None:
    engine = create_database_engine(database_url=_url(tmp_path / "handoff.db"))
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    policy = RadarPowerWebPolicyVersion(
        policy_version_id="policy-v1",
        radar_id="radar-a",
        version_number=1,
        product_bindings=(RadarProductBinding(product_id="product-a", position=0),),
        created_at=NOW,
        created_by="tester",
    )
    with session_scope(factory) as session:
        SqlAlchemyRadarRepository(session).upsert(
            RadarRecord(radar_id="radar-a", name="Radar A", status="active", owner="ABM")
        )
        session.add(ProductModel(
            product_id="product-a", product_code="a", lifecycle="active", created_at=NOW, updated_at=NOW
        ))
        runs = SqlAlchemyRadarRunRepository(session)
        runs.create(RadarRunRecord(run_id="radar-run-a", radar_id="radar-a"))
        runs.update_status("radar-run-a", RadarRunStatus.COMPLETED)
        policies = SqlAlchemyRadarPowerWebPolicyRepository(session)
        assert policies.save(policy) == policy
        repository = SqlAlchemyPowerWebHandoffRepository(session)
        stored = repository.create(_handoff(policy.policy_version_id))
        assert stored.role_demand_count == 1
        assert repository.find_by_idempotency_key("handoff-key") == stored
        with pytest.raises(ValueError, match="immutable"):
            repository.create(stored)

    with session_scope(factory) as session:
        policies = SqlAlchemyRadarPowerWebPolicyRepository(session)
        assert policies.get_active("radar-a") == policy
        assert policies.list_versions("radar-a") == (policy,)
        repository = SqlAlchemyPowerWebHandoffRepository(session)
        assert repository.get("power-web-handoff-1") == _handoff("policy-v1")
        assert repository.list_for_candidate(
            radar_id="radar-a", source_candidate_run_id="radar-run-a", candidate_id="candidate-a"
        )[0].idempotency_key == "handoff-key"
