from __future__ import annotations

from datetime import UTC, datetime

from power_web_os.application.radar.power_web_discovery.contracts import (
    AccountIdentitySnapshot,
    PowerWebHandoffSnapshot,
    ProductRoleDemandSet,
    ProductSnapshot,
    RoleDemand,
)


def make_handoff(*, role_count: int = 8) -> PowerWebHandoffSnapshot:
    product = ProductSnapshot(
        product_id="product-smartdiagnostics",
        product_code="smartdiagnostics",
        name="SmartDiagnostics",
        sales_playbook_version_id="sales-playbook-v1",
        product_definition_version_id="product-definition-v1",
        buying_role_policy_version_id="role-policy-v1",
    )
    roles = tuple(
        RoleDemand(
            demand_id=f"demand-{index}",
            product_id=product.product_id,
            sales_playbook_version_id=product.sales_playbook_version_id,
            buying_role_policy_version_id=product.buying_role_policy_version_id,
            semantic_role_code=f"role-{index}",
            display_name=f"Technical buying role {index}",
            responsibility=f"Owns technical reliability responsibility {index}",
            required=index < 6,
            priority="high" if index < 6 else "normal",
            scope="company",
        )
        for index in range(1, role_count + 1)
    )
    now = datetime(2026, 7, 22, tzinfo=UTC)
    return PowerWebHandoffSnapshot(
        handoff_id="power-web-handoff-test",
        radar_id="benchmark-sibur-holding-contour",
        radar_power_web_policy_version_id="radar-policy-v1",
        source_candidate_run_id="radar-run-test",
        source_candidate_id="ao-sibur-him-prom",
        account=AccountIdentitySnapshot(
            account_id="account-inn-5905001527",
            identity_status="stable",
            identity_basis="inn",
            legal_name="АО СИБУР-Химпром",
            entity_type="legal_entity",
            inn="5905001527",
            evidence_refs=("source-account",),
            source_candidate_run_id="radar-run-test",
            source_candidate_id="ao-sibur-him-prom",
        ),
        product_role_demand_sets=(ProductRoleDemandSet(product=product, role_demands=roles),),
        as_of=now,
        created_at=now,
        created_by="test",
        idempotency_key="people-search-test",
        request_fingerprint="fingerprint",
    )


def make_two_product_handoff() -> PowerWebHandoffSnapshot:
    handoff = make_handoff()
    product = ProductSnapshot(
        product_id="product-energy-optimization",
        product_code="industrial-energy-optimization",
        name="Industrial Energy Optimization",
        sales_playbook_version_id="sales-playbook-energy-v1",
        product_definition_version_id="product-definition-energy-v1",
        buying_role_policy_version_id="role-policy-energy-v1",
    )
    roles = tuple(
        RoleDemand(
            demand_id=f"energy-demand-{index}",
            product_id=product.product_id,
            sales_playbook_version_id=product.sales_playbook_version_id,
            buying_role_policy_version_id=product.buying_role_policy_version_id,
            semantic_role_code=f"energy-role-{index}",
            display_name=f"Energy buying role {index}",
            responsibility=f"Owns energy optimization responsibility {index}",
            required=index < 5,
            priority="high" if index < 5 else "normal",
            scope="company",
        )
        for index in range(1, 7)
    )
    return handoff.model_copy(update={
        "handoff_id": "power-web-handoff-two-products",
        "product_role_demand_sets": (
            *handoff.product_role_demand_sets,
            ProductRoleDemandSet(product=product, role_demands=roles),
        ),
    })
