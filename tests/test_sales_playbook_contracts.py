from __future__ import annotations

import inspect
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from power_web_os.application.sales_playbook.compatibility import legacy_playbook
from power_web_os.application.sales_playbook.contracts import (
    AccessPlaybookDefinition,
    AccessRouteRule,
    AccountRoleTitleHypothesis,
    ProductDefinition,
    RolePriority,
    RoleScope,
    SalesPlaybookDraft,
    SemanticBuyingRole,
    validate_publishable,
)
from power_web_os.application.sales_playbook.seed import SMARTDIAGNOSTICS_PRODUCT_ID, seed_smartdiagnostics
from power_web_os.application.sales_playbook.service import SalesPlaybookService
from power_web_os.persistence import Base, SqlAlchemySalesPlaybookRepository, create_database_engine, create_session_factory, session_scope
from power_web_os.persistence.models import (
    AccessPlaybookVersionModel,
    BuyingRolePolicyVersionModel,
    ProductDefinitionVersionModel,
    SalesPlaybookDefinitionVersionModel,
)


def _role(code: str = "technical_owner") -> SemanticBuyingRole:
    return SemanticBuyingRole(
        role_code=code,
        display_name="Владелец технического результата",
        business_responsibility="Отвечает за технический результат.",
        decision_rights=("Определяет критерии приемки.",),
        required=True,
        priority=RolePriority.CRITICAL,
        scope=RoleScope.ACCOUNT,
        reason="Необходим для подтверждения ценности.",
        expected_evidence=("Публично подтвержденная зона ответственности.",),
        exclusions=("Консультативная роль без ответственности.",),
    )


def _minimal_role(*, required: bool = True) -> SemanticBuyingRole:
    return SemanticBuyingRole(
        role_code="minimal_owner",
        display_name="Outcome owner",
        business_responsibility="Owns the purchase or implementation outcome.",
        required=required,
        scope=RoleScope.ACCOUNT,
    )


def _draft() -> SalesPlaybookDraft:
    return SalesPlaybookDraft(
        product_id="product-test",
        draft_revision=1,
        product=ProductDefinition(
            product_code="test-product",
            name="Test product",
            short_description="Short description",
            customer_problem="Customer problem",
            value_proposition="Measurable value",
            use_contexts=("Industrial context",),
        ),
        buying_roles=(_role(),),
        access_playbook=AccessPlaybookDefinition(route_rules=(
            AccessRouteRule(
                route_code="technical_route",
                name="Technical route",
                source_role_codes=("technical_owner",),
                target_role_codes=("technical_owner",),
                reason="Evidence-first route.",
            ),
        )),
        updated_at=datetime.now(UTC),
        updated_by="test",
    )


def test_published_roles_require_semantic_fields() -> None:
    payload = _role().model_dump()
    payload["business_responsibility"] = ""
    with pytest.raises(ValidationError):
        SemanticBuyingRole.model_validate(payload)
    assert validate_publishable(_draft()).valid is True


def test_frozen_access_rules_do_not_constrain_role_policy() -> None:
    draft = _draft().model_copy(update={
        "access_playbook": AccessPlaybookDefinition(route_rules=(
            AccessRouteRule(
                route_code="broken_route",
                name="Broken",
                source_role_codes=("missing_role",),
                target_role_codes=("technical_owner",),
                reason="Invalid reference fixture.",
            ),
        ))
    })
    result = validate_publishable(draft)
    assert result.valid is True


def test_minimal_semantic_role_is_publishable() -> None:
    draft = _draft().model_copy(update={"buying_roles": (_minimal_role(),)})

    assert validate_publishable(draft).valid is True
    assert draft.buying_roles[0].decision_rights == ()
    assert draft.buying_roles[0].expected_evidence == ()
    assert draft.buying_roles[0].reason == ""


def test_semantic_role_defaults_follow_requiredness() -> None:
    assert _minimal_role(required=True).priority is RolePriority.HIGH
    assert _minimal_role(required=False).priority is RolePriority.NORMAL


def test_title_hypothesis_cannot_mutate_role_policy() -> None:
    with pytest.raises(ValidationError):
        AccountRoleTitleHypothesis.model_validate({
            "hypothesis_id": "hyp-1",
            "account_id": "account-1",
            "semantic_role_code": "technical_owner",
            "title_variants": ["Technical function title"],
            "reason": "Account-specific wording.",
            "required": False,
        })


def test_product_publish_activate_restore_and_archive(tmp_path) -> None:
    engine = create_database_engine(database_url=f"sqlite:///{(tmp_path / 'sales.db').as_posix()}")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    with session_scope(factory) as session:
        service = SalesPlaybookService(SqlAlchemySalesPlaybookRepository(session))
        service.create_from_draft(_draft())
        version = service.publish("product-test", published_by="test", activate=True)
        assert service.get_product("product-test").active_version_id == version.version_id
        restored = service.restore_as_draft("product-test", version.version_id, requester="reviewer")
        assert restored.base_version_id == version.version_id
        assert service.archive("product-test").lifecycle.value == "archived"
        assert version.access_playbook_version_id is None
        assert version.access_playbook is None
        assert legacy_playbook(version).allowed_routes == ()


def test_new_publication_has_no_access_playbook_dependency(tmp_path) -> None:
    engine = create_database_engine(database_url=f"sqlite:///{(tmp_path / 'no-access.db').as_posix()}")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    with session_scope(factory) as session:
        service = SalesPlaybookService(SqlAlchemySalesPlaybookRepository(session))
        service.create_from_draft(_draft())
        version = service.publish("product-test", published_by="test", activate=True)

        assert version.access_playbook_version_id is None
        assert version.access_playbook is None
        assert session.query(AccessPlaybookVersionModel).count() == 0


def test_historical_access_playbook_version_remains_readable(tmp_path) -> None:
    engine = create_database_engine(database_url=f"sqlite:///{(tmp_path / 'legacy-access.db').as_posix()}")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    with session_scope(factory) as session:
        service = SalesPlaybookService(SqlAlchemySalesPlaybookRepository(session))
        service.create_from_draft(_draft())
        now = datetime.now(UTC)
        session.add(ProductDefinitionVersionModel(
            version_id="product-definition-legacy",
            product_id="product-test",
            version_number=1,
            payload_json=_draft().product.model_dump(mode="json"),
            published_by="legacy",
            published_at=now,
        ))
        session.add(BuyingRolePolicyVersionModel(
            version_id="buying-role-policy-legacy",
            product_id="product-test",
            version_number=1,
            payload_json=[_role().model_dump(mode="json")],
            published_by="legacy",
            published_at=now,
        ))
        session.add(AccessPlaybookVersionModel(
            version_id="access-playbook-legacy",
            product_id="product-test",
            version_number=1,
            payload_json=_draft().access_playbook.model_dump(mode="json"),
            published_by="legacy",
            published_at=now,
        ))
        session.add(SalesPlaybookDefinitionVersionModel(
            version_id="sales-playbook-legacy",
            product_id="product-test",
            version_number=1,
            product_definition_version_id="product-definition-legacy",
            buying_role_policy_version_id="buying-role-policy-legacy",
            access_playbook_version_id="access-playbook-legacy",
            published_by="legacy",
            published_at=now,
        ))
        session.flush()

        version = service.get_version("product-test", "sales-playbook-legacy")
        assert version.access_playbook_version_id == "access-playbook-legacy"
        assert legacy_playbook(version).allowed_routes == ("technical_route",)


def test_sales_playbook_has_no_provider_dependency() -> None:
    import power_web_os.application.sales_playbook.service as module

    source = inspect.getsource(module)
    assert "openrouter" not in source.casefold()
    assert "candidate_discovery" not in source
    assert "signal_monitoring" not in source


def test_smartdiagnostics_contract_has_eight_semantic_roles(tmp_path) -> None:
    engine = create_database_engine(database_url=f"sqlite:///{(tmp_path / 'seed.db').as_posix()}")
    Base.metadata.create_all(engine)
    factory = create_session_factory(engine)
    with session_scope(factory) as session:
        service = SalesPlaybookService(SqlAlchemySalesPlaybookRepository(session))
        assert seed_smartdiagnostics(service) is True
        assert seed_smartdiagnostics(service) is False
        version = service.list_versions(SMARTDIAGNOSTICS_PRODUCT_ID)[0]
        assert len(version.buying_roles) == 8
        assert all(role.business_responsibility for role in version.buying_roles)
