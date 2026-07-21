"""Deterministic SmartDiagnostics product and playbook seed."""

from __future__ import annotations

from datetime import UTC, datetime

from power_web_os.application.sales_playbook.contracts import (
    AccessPlaybookDefinition,
    AccessRouteRule,
    ProductDefinition,
    RolePriority,
    RoleScope,
    SalesPlaybookDraft,
    SemanticBuyingRole,
)
from power_web_os.application.sales_playbook.service import SalesPlaybookService

SMARTDIAGNOSTICS_PRODUCT_ID = "product-smartdiagnostics"


def seed_smartdiagnostics(service: SalesPlaybookService) -> bool:
    if any(item.product_id == SMARTDIAGNOSTICS_PRODUCT_ID for item in service.list_products()):
        return False
    now = datetime.now(UTC)
    draft = SalesPlaybookDraft(
        product_id=SMARTDIAGNOSTICS_PRODUCT_ID,
        draft_revision=1,
        product=ProductDefinition(
            product_code="smartdiagnostics",
            name="SmartDiagnostics",
            short_description="Диагностика и приоритизация технического состояния промышленного оборудования.",
            customer_problem="Незапланированные простои, позднее обнаружение деградации и фрагментированные данные ТОиР.",
            value_proposition="Сокращение риска отказов и повышение управляемости ремонтов за счет доказательной диагностики.",
            use_contexts=("Надежность оборудования", "Планирование ТОиР", "Модернизация производственных активов"),
        ),
        buying_roles=_smartdiagnostics_roles(),
        access_playbook=_smartdiagnostics_access_playbook(),
        updated_at=now,
        updated_by="demo-seed",
    )
    service.create_from_draft(draft)
    service.publish(SMARTDIAGNOSTICS_PRODUCT_ID, published_by="demo-seed", activate=True)
    return True


def _role(
    code: str,
    name: str,
    responsibility: str,
    decision: str,
    reason: str,
    evidence: str,
    *,
    priority: RolePriority = RolePriority.HIGH,
    required: bool = True,
    scope: RoleScope = RoleScope.ACCOUNT,
    exclusions: tuple[str, ...] = (),
) -> SemanticBuyingRole:
    return SemanticBuyingRole(
        role_code=code,
        display_name=name,
        business_responsibility=responsibility,
        decision_rights=(decision,),
        required=required,
        priority=priority,
        scope=scope,
        reason=reason,
        expected_evidence=(evidence,),
        exclusions=exclusions,
    )


def _smartdiagnostics_roles() -> tuple[SemanticBuyingRole, ...]:
    return (
        _role("technical_reliability_owner", "Владелец технической надежности", "Отвечает за надежность и технический риск оборудования.", "Определяет требования к диагностике и допустимому риску отказа.", "Формирует техническую потребность и критерии доказательности.", "Ответственность за надежность, диагностику или техническое состояние."),
        _role("maintenance_process_owner", "Владелец процесса ТОиР", "Отвечает за стратегию, планы и исполнение технического обслуживания и ремонтов.", "Определяет приоритеты ремонтов и требования к планированию.", "Проверяет применимость результата в процессе ТОиР.", "Ответственность за программы, бюджет или планирование ТОиР."),
        _role("production_continuity_owner", "Владелец непрерывности производства", "Отвечает за выполнение производственной программы и последствия простоев.", "Согласует допустимое влияние работ и риска на производство.", "Связывает технический эффект с производственным результатом.", "Ответственность за выпуск, режим или доступность производственной площадки."),
        _role("economic_sponsor", "Экономический заказчик", "Отвечает за бизнес-результат и экономическую целесообразность инициативы.", "Одобряет финансирование и целевой эффект.", "Без этой функции техническая инициатива не становится приоритетом бизнеса.", "Ответственность за инвестиционное решение, эффект или бюджет.", priority=RolePriority.CRITICAL),
        _role("implementation_integration_owner", "Владелец внедрения и интеграции", "Отвечает за внедрение решения в технологический и ИТ-контур.", "Согласует архитектуру, данные, безопасность и эксплуатационную поддержку.", "Определяет реализуемость и ограничения внедрения.", "Ответственность за интеграцию, промышленную автоматизацию, данные или ИТ-архитектуру."),
        _role("operational_champion", "Операционный эксперт и внутренний проводник", "Знает ежедневную практику и помогает адаптировать решение к реальной работе.", "Влияет на принятие пользователями и подтверждает практическую ценность.", "Обеспечивает доступ к контексту и внутреннюю поддержку.", "Экспертное участие в диагностике, ремонтах или эксплуатации."),
        _role("procurement_compliance_gatekeeper", "Закупочный и комплаенс-контроль", "Обеспечивает соответствие закупочным и договорным требованиям.", "Допускает поставщика и формат сделки к процедуре.", "Может остановить маршрут независимо от технической ценности.", "Ответственность за закупочную процедуру, договор или комплаенс.", required=False, priority=RolePriority.NORMAL),
        _role("external_service_partner", "Внешний сервисный или интеграционный партнер", "Связывает поставщика с действующим сервисным и интеграционным контуром заказчика.", "Влияет на способ входа, совместимость и реализацию.", "Может дать доверенный маршрут и снять барьер доступа.", "Публичное подтверждение сервисной, интеграционной или проектной связи.", required=False, priority=RolePriority.NORMAL, scope=RoleScope.EXTERNAL),
    )


def _smartdiagnostics_access_playbook() -> AccessPlaybookDefinition:
    return AccessPlaybookDefinition(
        route_rules=(
            AccessRouteRule(
                route_code="technical_benchmark",
                name="Технический разбор",
                source_role_codes=("operational_champion",),
                target_role_codes=("technical_reliability_owner", "maintenance_process_owner"),
                allowed_channels=("expert_session", "technical_workshop"),
                required_assets=("diagnostic_methodology", "reference_architecture"),
                reason="Начать с доказуемой технической задачи и владельцев процесса.",
            ),
            AccessRouteRule(
                route_code="business_case",
                name="Экономическое обоснование",
                source_role_codes=("technical_reliability_owner", "maintenance_process_owner"),
                target_role_codes=("economic_sponsor",),
                allowed_channels=("business_review",),
                required_assets=("value_model", "risk_assessment"),
                requires_human_review=True,
                reason="Перевести технический эффект в финансовое решение.",
            ),
            AccessRouteRule(
                route_code="implementation_readiness",
                name="Готовность к внедрению",
                source_role_codes=("technical_reliability_owner",),
                target_role_codes=("implementation_integration_owner",),
                allowed_channels=("architecture_session",),
                required_assets=("integration_checklist",),
                reason="Проверить данные, архитектуру и эксплуатационные ограничения.",
            ),
            AccessRouteRule(
                route_code="partner_intro",
                name="Вход через партнера",
                source_role_codes=("external_service_partner",),
                target_role_codes=("technical_reliability_owner",),
                allowed_channels=("partner_introduction",),
                requires_human_review=True,
                reason="Использовать только подтвержденную партнерскую связь.",
            ),
        ),
        blocked_channels=("unsolicited_private_contact", "unverified_personal_outreach"),
        available_assets=("diagnostic_methodology", "reference_architecture", "value_model", "risk_assessment", "integration_checklist"),
        required_review_for=("partner_intro", "business_case"),
    )
