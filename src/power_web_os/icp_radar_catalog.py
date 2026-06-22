from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from power_web_os.icp_radar import (
    AccountQualificationModel,
    AtomicRule,
    GlobalSearchPolicy,
    IntentSignalDefinition,
    MonitoringPolicy,
    RadarDefinition,
    RadarDefinitionValidator,
    RadarMetadata,
    RadarScoringModel,
    RadarValidationReport,
    RuleGroup,
    SignalScoreRule,
    SignalCriterion,
    SignalScoringRubric,
    SourceDefinition,
    SourcePolicy,
    radar_definition_to_payload,
)


@dataclass(frozen=True, slots=True)
class ICPRadarCatalogItem:
    radar_id: str
    name: str
    status: str
    owner: str
    profile: dict[str, Any]
    summary: dict[str, Any]
    definition: RadarDefinition
    artifact_path: str | None


@dataclass(frozen=True, slots=True)
class ICPRadarCatalogArtifact:
    radars: tuple[ICPRadarCatalogItem, ...]
    workflow_metadata: dict[str, Any]


def build_icp_radar_catalog(active_radar_payload: dict[str, Any]) -> dict[str, Any]:
    active_definition = active_radar_payload["radar"]["definition"]
    active_definition_model = _definition_from_payload(active_definition)
    active_signal_criteria = _criteria_from_signals(active_definition_model.intent_signals)
    active_candidates = active_radar_payload.get("candidates", [])
    radars = (
        ICPRadarCatalogItem(
            radar_id="toir-sibur",
            name=active_definition_model.metadata.name,
            status=active_definition_model.metadata.status,
            owner=active_definition_model.metadata.owner,
            profile={
                "icp_profile": active_radar_payload["radar"]["profile"]["name"],
                "product": "Автоматизация ТОиР",
                "segment": "Нефтехимия и производственные активы",
                "scope": active_definition_model.metadata.description,
            },
            summary={
                "cadence": active_definition_model.monitoring_policy.cadence,
                "last_run": "2026-06-11",
                "candidate_count": len(active_candidates),
                "needs_review_count": len(active_candidates),
                "accepted_count": 0,
                "run_mode": active_definition_model.monitoring_policy.run_mode,
            },
            definition=active_definition_model,
            artifact_path="/demo/icp_radar.json",
        ),
        ICPRadarCatalogItem(
            radar_id="toir-quick-live",
            name="ТОиР Quick Live Radar",
            status="configured",
            owner="ABM Research",
            profile={
                "icp_profile": "Живой мини-радар ТОиР для СИБУР",
                "product": "Автоматизация ТОиР",
                "segment": "Промышленные и нефтехимические активы СИБУР",
                "scope": "CLI-запуск с live web search через OpenRouter. Результаты требуют проверки человеком.",
            },
            summary={
                "cadence": "manual",
                "last_run": "not_run",
                "candidate_count": 0,
                "needs_review_count": 0,
                "accepted_count": 0,
                "run_mode": "live_cli",
            },
            definition=_live_quick_definition(),
            artifact_path="/demo/live_mini_icp_radar_run.json",
        ),
        ICPRadarCatalogItem(
            radar_id="mining-toir",
            name="ТОиР / Горнодобыча",
            status="configured",
            owner="Industrial ABM",
            profile={
                "icp_profile": "ТОиР для горнодобывающих активов",
                "product": "Автоматизация ремонтов и надежности",
                "segment": "Горнодобывающие предприятия",
                "scope": "Крупные производственные площадки с карьерной, обогатительной или транспортной инфраструктурой.",
            },
            summary={
                "cadence": "monthly",
                "last_run": "not_run",
                "candidate_count": 0,
                "needs_review_count": 0,
                "accepted_count": 0,
                "run_mode": "configured_not_generated",
            },
            definition=_planned_definition(
                definition_id="radar-def-mining-toir",
                product="Автоматизация ремонтов и надежности",
                segment="Горнодобывающие предприятия",
                holding="Рынок РФ / горнодобыча",
                market_scope="Юрлица с производственными активами, тяжелым оборудованием и публичными сигналами по ремонтам.",
                criteria=_merge_criteria(
                    active_signal_criteria,
                    (
                    ("C1", "ТОиР / EAM", "Упоминание ремонтов, надежности, EAM или планирования ТОиР"),
                    ("C2", "Тяжелое оборудование", "Парк карьерной, дробильной, конвейерной или энергетической техники"),
                    ("C3", "Простои и надежность", "Сигналы о снижении простоев, OEE или повышении надежности"),
                    ("C4", "Цифровизация производства", "Программы цифровизации промышленных процессов"),
                    ("C5", "Закупочная активность", "Тендеры или закупки по диагностике, ремонтам, датчикам или аналитике"),
                    ),
                ),
            ),
            artifact_path=None,
        ),
        ICPRadarCatalogItem(
            radar_id="retail-energy-efficiency",
            name="Энергоэффективность / Ритейл",
            status="planned",
            owner="Growth Team",
            profile={
                "icp_profile": "Энергоэффективность распределенной сети",
                "product": "Энергомониторинг и управление объектами",
                "segment": "Федеральный ритейл и склады",
                "scope": "Компании с распределенной сетью магазинов, складов или холодильной инфраструктуры.",
            },
            summary={
                "cadence": "weekly",
                "last_run": "not_scheduled",
                "candidate_count": 0,
                "needs_review_count": 0,
                "accepted_count": 0,
                "run_mode": "planned",
            },
            definition=_planned_definition(
                definition_id="radar-def-retail-energy",
                product="Энергомониторинг и управление объектами",
                segment="Федеральный ритейл и склады",
                holding="Рынок РФ / ритейл",
                market_scope="Операторы сетей с большим количеством объектов и затратами на энергоресурсы.",
                criteria=_merge_criteria(
                    active_signal_criteria,
                    (
                    ("C1", "Распределенная сеть", "Большое число торговых, складских или холодильных объектов"),
                    ("C2", "Энергозатраты", "Публичные сигналы об оптимизации энергопотребления"),
                    ("C3", "ESG / устойчивость", "Заявленные программы устойчивого развития или снижения выбросов"),
                    ("C4", "IoT / диспетчеризация", "Интерес к удаленному мониторингу инженерной инфраструктуры"),
                    ("C5", "Бюджетный триггер", "Открытые закупки или проекты по энергоэффективности"),
                    ),
                ),
            ),
            artifact_path=None,
        ),
    )
    return icp_radar_catalog_to_payload(
        ICPRadarCatalogArtifact(
            radars=radars,
            workflow_metadata={
                "workflow_name": "ICPRadarCatalog",
                "artifact_version": "0.6.5.2",
                "active_fixture_radar_id": "toir-sibur",
                "radar_count": len(radars),
            },
        )
    )


def _criteria_from_signals(signals: tuple[IntentSignalDefinition, ...]) -> tuple[tuple[str, str, str], ...]:
    return tuple((signal.code, signal.name, signal.description) for signal in signals)


def _merge_criteria(
    base: tuple[tuple[str, str, str], ...],
    overrides: tuple[tuple[str, str, str], ...],
) -> tuple[tuple[str, str, str], ...]:
    by_code = {code: (code, name, description) for code, name, description in base}
    for code, name, description in overrides:
        by_code[code] = (code, name, description)
    return tuple(by_code[code] for code, _, _ in base)


def icp_radar_catalog_to_payload(artifact: ICPRadarCatalogArtifact) -> dict[str, Any]:
    return {
        "artifact_type": "icp_radar_catalog",
        "artifact_version": "0.6.5.2",
        "radars": [catalog_item_to_payload(item) for item in artifact.radars],
        "workflow_metadata": artifact.workflow_metadata,
    }


def catalog_item_to_payload(item: ICPRadarCatalogItem) -> dict[str, Any]:
    return {
        "radar_id": item.radar_id,
        "name": item.name,
        "status": item.status,
        "owner": item.owner,
        "profile": item.profile,
        "summary": item.summary,
        "definition": radar_definition_to_payload(item.definition),
        "artifact_path": item.artifact_path,
    }


def _definition_from_payload(payload: dict[str, Any]) -> RadarDefinition:
    return RadarDefinition(
        definition_id=payload["definition_id"],
        metadata=RadarMetadata(**payload["metadata"]),
        global_search_policy=GlobalSearchPolicy(
            sources=tuple(SourceDefinition(**item) for item in payload["global_search_policy"]["sources"]),
            keywords=tuple(payload["global_search_policy"]["keywords"]),
            exclusions=tuple(payload["global_search_policy"]["exclusions"]),
            allow_system_sources=bool(payload["global_search_policy"]["allow_system_sources"]),
        ),
        account_qualification=AccountQualificationModel(
            rule_group=_rule_group_from_payload(payload["account_qualification"]["rule_group"]),
        ),
        intent_signals=tuple(_intent_signal_from_payload(item) for item in payload["intent_signals"]),
        monitoring_policy=MonitoringPolicy(**payload["monitoring_policy"]),
        scoring_model=RadarScoringModel(
            fit_model=dict(payload["scoring_model"].get("fit_model", {
                "formula_preset": "custom",
                "description": "Legacy fit formula",
                "custom_formula": payload["scoring_model"].get("fit_formula", ""),
                "uses": [],
            })),
            intent_model=dict(payload["scoring_model"].get("intent_model", {
                "formula_preset": "custom",
                "description": "Legacy intent formula",
                "custom_formula": payload["scoring_model"].get("intent_formula", ""),
                "uses": [],
            })),
            tier_model=dict(payload["scoring_model"].get("tier_model", {
                "basis": "fit + intent",
                "description": "Legacy tier model",
            })),
            tier_thresholds=dict(payload["scoring_model"]["tier_thresholds"]),
            confidence_penalties=dict(payload["scoring_model"]["confidence_penalties"]),
        ),
        validation_report=RadarValidationReport(errors=(), warnings=(), info=()),
    )


def _rule_group_from_payload(payload: dict[str, Any]) -> RuleGroup:
    return RuleGroup(
        group_id=payload["group_id"],
        name=payload.get("name", payload["group_id"]),
        operator=payload["operator"],
        rules=tuple(_atomic_rule_from_payload(item) for item in payload["rules"]),
        groups=tuple(_rule_group_from_payload(item) for item in payload["groups"]),
    )


def _atomic_rule_from_payload(payload: dict[str, Any]) -> AtomicRule:
    return AtomicRule(
        rule_id=payload["rule_id"],
        name=payload.get("name", payload["description"]),
        description=payload["description"],
        target_field=payload.get("generated_target_field", payload.get("target_field", "")),
        comparison_operator=payload.get("generated_comparison_operator", payload.get("comparison_operator", "")),
        value=payload.get("generated_value", payload.get("value", "")),
        requirement_level=payload["requirement_level"],
        source_policy=_source_policy_from_payload(payload["source_policy"]),
    )


def _source_policy_from_payload(payload: dict[str, Any]) -> SourcePolicy:
    return SourcePolicy(
        source_ids=tuple(payload["source_ids"]),
        source_logic=payload["source_logic"],
        allow_additional_sources=bool(payload["allow_additional_sources"]),
        fallback_confidence=payload["fallback_confidence"],
        use_global_search_policy=bool(payload.get("use_global_search_policy", True)),
        local_sources=tuple(SourceDefinition(**item) for item in payload.get("local_sources", ())),
    )


def _intent_signal_from_payload(payload: dict[str, Any]) -> IntentSignalDefinition:
    return IntentSignalDefinition(
        signal_id=payload["signal_id"],
        code=payload["code"],
        name=payload["name"],
        description=payload["description"],
        trigger_rule_group=_rule_group_from_payload(payload["trigger_rule_group"]),
        source_policy=_source_policy_from_payload(payload["source_policy"]),
        scoring_rubric=SignalScoringRubric(
            scale=tuple(int(item) for item in payload["scoring_rubric"]["scale"]),
            rules=tuple(
                SignalScoreRule(
                    score=int(item["score"]),
                    description=item["description"],
                    rule_group=_rule_group_from_payload(item["rule_group"]),
                )
                for item in payload["scoring_rubric"]["rules"]
            ),
        ),
    )


def _planned_definition(
    *,
    definition_id: str,
    product: str,
    segment: str,
    holding: str,
    market_scope: str,
    criteria: tuple[tuple[str, str, str], ...],
) -> RadarDefinition:
    sources = (
        SourceDefinition("company_site", "url", "Сайты компаний", "https://", "medium"),
        SourceDefinition("procurement", "url", "Закупочные площадки", "https://zakupki.gov.ru", "medium"),
        SourceDefinition("news", "search_engine", "Новостной поиск", "https://ya.ru/news", "low"),
        SourceDefinition("hiring", "url", "Вакансии", "https://hh.ru", "low"),
    )
    source_ids = tuple(source.source_id for source in sources)
    definition = RadarDefinition(
        definition_id=definition_id,
        metadata=RadarMetadata(
            name=product.replace("Автоматизация ремонтов и надежности", "ТОиР").replace("Энергомониторинг и управление объектами", "Энергоэффективность"),
            description=market_scope,
            owner="Industrial ABM" if "горнодобы" in segment.lower() else "Growth Team",
            status="configured" if "горнодобы" in segment.lower() else "planned",
        ),
        global_search_policy=GlobalSearchPolicy(
            sources=sources,
            keywords=(product, segment, holding),
            exclusions=("Компании без публично наблюдаемых сигналов", "Малые объекты без enterprise-повестки"),
            allow_system_sources=True,
        ),
        account_qualification=AccountQualificationModel(
            rule_group=RuleGroup(
                group_id=f"{definition_id}-qualification",
                operator="AND",
                rules=(
                    AtomicRule(
                        rule_id=f"{definition_id}-segment",
                        description=f"Компания относится к сегменту: {segment}.",
                        target_field="segment",
                        comparison_operator="contains",
                        value=segment,
                        requirement_level="required",
                        source_policy=SourcePolicy(("company_site",), "OR", True, "medium"),
                    ),
                    AtomicRule(
                        rule_id=f"{definition_id}-enterprise",
                        description="Компания имеет enterprise-масштаб и самостоятельную повестку.",
                        target_field="enterprise_fit",
                        comparison_operator="exists",
                        value="true",
                        requirement_level="recommended",
                        source_policy=SourcePolicy(("company_site", "news"), "OR", True, "low"),
                    ),
                ),
            )
        ),
        intent_signals=tuple(
            _planned_signal(
                definition_id=definition_id,
                code=code,
                name=name,
                description=description,
                source_ids=source_ids,
            )
            for code, name, description in criteria
        ),
        monitoring_policy=MonitoringPolicy(
            cadence="monthly",
            lookback_window="90 days",
            run_mode="configured_not_generated",
            deduplication="dedupe_by_source_url_and_signal_code",
            stale_after="180 days",
        ),
        scoring_model=RadarScoringModel(
            fit_model={
                "formula_preset": "weighted_average",
                "description": "Account fit is calculated from account qualification rules.",
                "custom_formula": "",
                "uses": [f"{definition_id}-segment", f"{definition_id}-scale"],
            },
            intent_model={
                "formula_preset": "maximum_signal",
                "description": "Intent is calculated from observed interest signals.",
                "custom_formula": "",
                "uses": [code for code, _, _ in criteria],
            },
            tier_model={
                "basis": "fit + intent",
                "description": "Tier classifies candidates using fit and intent thresholds.",
            },
            tier_thresholds={"Tier 1": ">=38", "Tier 2": ">=25", "Tier 3": ">=15", "Monitor": "<15"},
            confidence_penalties={"low": "-20%", "medium": "-10%", "high": "0%", "none": "exclude"},
        ),
        validation_report=RadarValidationReport(errors=(), warnings=(), info=()),
    )
    report = RadarDefinitionValidator().validate(definition)
    return RadarDefinition(
        definition_id=definition.definition_id,
        metadata=definition.metadata,
        global_search_policy=definition.global_search_policy,
        account_qualification=definition.account_qualification,
        intent_signals=definition.intent_signals,
        monitoring_policy=definition.monitoring_policy,
        scoring_model=definition.scoring_model,
        validation_report=report,
    )


def _planned_signal(
    *,
    definition_id: str,
    code: str,
    name: str,
    description: str,
    source_ids: tuple[str, ...],
) -> IntentSignalDefinition:
    policy = SourcePolicy(source_ids[:3], "OR", True, "low")
    return IntentSignalDefinition(
        signal_id=f"{definition_id}-{code.lower()}",
        code=code,
        name=name,
        description=description,
        trigger_rule_group=RuleGroup(
            group_id=f"{definition_id}-{code.lower()}-trigger",
            operator="OR",
            rules=(
                AtomicRule(
                    rule_id=f"{definition_id}-{code.lower()}-trigger-rule",
                    description=description,
                    target_field="public_evidence",
                    comparison_operator="contains",
                    value=name,
                    requirement_level="recommended",
                    source_policy=policy,
                ),
            ),
        ),
        source_policy=policy,
        scoring_rubric=SignalScoringRubric(
            scale=(0, 1, 2),
            rules=tuple(
                SignalScoreRule(
                    score=score,
                    description=description,
                    rule_group=RuleGroup(
                        group_id=f"{definition_id}-{code.lower()}-score-{score}",
                        operator="AND",
                        rules=(
                            AtomicRule(
                                rule_id=f"{definition_id}-{code.lower()}-score-{score}-rule",
                                description=description,
                                target_field=code,
                                comparison_operator="equals",
                                value=str(score),
                                requirement_level="recommended",
                                source_policy=policy,
                            ),
                        ),
                    ),
                )
                for score, description in (
                    (0, "Сигнал не наблюдается."),
                    (1, "Есть слабое или косвенное наблюдение."),
                    (2, "Сигнал подтвержден релевантным источником."),
                )
            ),
        ),
    )


def _live_quick_definition() -> RadarDefinition:
    sources = (
        SourceDefinition("dadata_registry", "company_registry", "DaData company registry", "company_registry:dadata", "high"),
        SourceDefinition("openrouter_web", "search_engine", "OpenRouter web search", "openrouter:web_search", "medium"),
        SourceDefinition("sibur_site", "url", "Сайт СИБУР", "https://www.sibur.ru", "high"),
    )
    source_policy = SourcePolicy(
        source_ids=("dadata_registry", "openrouter_web", "sibur_site"),
        source_logic="OR",
        allow_additional_sources=True,
        fallback_confidence="low",
        use_global_search_policy=True,
    )
    signal_specs = (
        ("S1", "ТОиР / ремонты / надежность", "Найти упоминания ремонтов, надежности, ТОиР или межремонтного интервала."),
        ("S2", "Модернизация / инвестиции / рост мощности", "Найти упоминания модернизации оборудования, инвестиций или роста мощности."),
        ("S3", "Цифровизация / диагностика / предиктивная аналитика", "Найти упоминания цифровизации производства, диагностики или предиктивной аналитики."),
    )
    definition = RadarDefinition(
        definition_id="radar-def-toir-quick-live",
        metadata=RadarMetadata(
            name="ТОиР Quick Live Radar",
            description="Мини-радар для живого поиска производственных активов СИБУР с сигналами по ТОиР, модернизации и цифровизации.",
            owner="ABM Research",
            status="configured",
        ),
        global_search_policy=GlobalSearchPolicy(
            sources=sources,
            keywords=("СИБУР ТОиР", "СИБУР ремонты", "СИБУР модернизация", "СИБУР цифровизация"),
            exclusions=("Сервисные юрлица без производственного актива",),
            allow_system_sources=True,
        ),
        account_qualification=AccountQualificationModel(
            rule_group=RuleGroup(
                group_id="toir-quick-live-qualification",
                operator="AND",
                rules=(
                    AtomicRule(
                        rule_id="q1-sibur-group",
                        name="Компания входит в группу СИБУР",
                        description="Компания входит в группу СИБУР.",
                        target_field="holding",
                        comparison_operator="contains",
                        value="СИБУР",
                        requirement_level="required",
                        source_policy=source_policy,
                    ),
                    AtomicRule(
                        rule_id="q2-industrial-asset",
                        name="Промышленный актив",
                        description="Компания относится к промышленным или нефтехимическим производственным активам.",
                        target_field="asset_type",
                        comparison_operator="contains",
                        value="industrial",
                        requirement_level="required",
                        source_policy=source_policy,
                    ),
                ),
            )
        ),
        intent_signals=tuple(
            _planned_signal(
                definition_id="radar-def-toir-quick-live",
                code=code,
                name=name,
                description=description,
                source_ids=("openrouter_web", "sibur_site"),
            )
            for code, name, description in signal_specs
        ),
        monitoring_policy=MonitoringPolicy(
            cadence="manual",
            lookback_window="90 days",
            run_mode="live_cli",
            deduplication="dedupe_by_source_url_and_signal_code",
            stale_after="90 days",
        ),
        scoring_model=RadarScoringModel(
            fit_model={
                "formula_preset": "arithmetic_mean",
                "description": "Fit is based on Q1/Q2 qualification.",
                "custom_formula": "",
                "uses": ["q1-sibur-group", "q2-industrial-asset"],
            },
            intent_model={
                "formula_preset": "capped_sum",
                "description": "Intent is based on S1-S3 observed signals.",
                "custom_formula": "",
                "uses": ["S1", "S2", "S3"],
            },
            tier_model={
                "basis": "fit + intent",
                "description": "Tier is assigned from confirmed fit and observed intent.",
            },
            tier_thresholds={
                "Tier 1": "fit=2 and intent>=3",
                "Tier 2": "fit>=1 and intent>=1",
                "Monitor": "otherwise",
            },
            confidence_penalties={"low": "-20%", "medium": "-10%", "high": "0%", "none": "exclude"},
        ),
        validation_report=RadarValidationReport(errors=(), warnings=(), info=()),
    )
    report = RadarDefinitionValidator().validate(definition)
    return RadarDefinition(
        definition_id=definition.definition_id,
        metadata=definition.metadata,
        global_search_policy=definition.global_search_policy,
        account_qualification=definition.account_qualification,
        intent_signals=definition.intent_signals,
        monitoring_policy=definition.monitoring_policy,
        scoring_model=definition.scoring_model,
        validation_report=report,
    )
