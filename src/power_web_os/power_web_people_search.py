"""Explicit CLI for the pre-persistence Power Web people-search stage."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from power_web_os.application.radar.configuration.model_profiles import default_model_profile_registry
from power_web_os.application.radar.power_web_discovery.people_search.contracts import PeopleSearchBudgetSettings
from power_web_os.application.radar.power_web_discovery.people_search.execution import PeopleSearchStageExecutor
from power_web_os.application.radar.power_web_discovery.people_search.planning import PowerWebPeopleSearchPlanningInputBuilder
from power_web_os.application.radar.power_web_discovery.people_search.service import PeopleSearchPlanningService
from power_web_os.integrations.openrouter_people_search import OpenRouterPeopleSearchProvider
from power_web_os.persistence import (
    SqlAlchemyPowerWebHandoffRepository,
    create_database_engine,
    create_session_factory,
    session_scope,
)


MODEL_PROFILE_ID = "power_web_people_search_default"


def run(args: argparse.Namespace) -> dict[str, object]:
    registry = default_model_profile_registry()
    profile = registry.require(MODEL_PROFILE_ID)
    planner_role = profile.roles.get("people_title_planner")
    search_role = profile.roles.get("people_search_extractor")
    if planner_role is None or search_role is None:
        raise ValueError("Power Web model profile is incomplete")
    engine = create_database_engine(database_url=args.database_url)
    factory = create_session_factory(engine)
    with session_scope(factory) as session:
        handoff = SqlAlchemyPowerWebHandoffRepository(session).get(args.handoff_id)
    if handoff is None:
        raise ValueError(f"Unknown Power Web handoff: {args.handoff_id}")
    if handoff.role_demand_count != 8:
        raise ValueError("people_search_quality live scope requires exactly eight RoleDemand")
    planning_input = PowerWebPeopleSearchPlanningInputBuilder().build(
        handoff,
        account_aliases=tuple(args.account_alias or ()),
        official_domains=(args.official_domain,),
        official_domain_evidence_refs=tuple(args.official_domain_evidence_ref),
        geography=args.geography,
        language=args.language,
    )
    provider = OpenRouterPeopleSearchProvider(
        planner_model_id=planner_role.primary_model,
        search_model_id=search_role.primary_model,
        env_path=args.env_path,
    )
    if not provider.credentials_available:
        raise RuntimeError("OPENROUTER_API_KEY is unavailable in the effective runtime environment")
    settings = PeopleSearchBudgetSettings()
    plan = PeopleSearchPlanningService(provider=provider, settings=settings).build(planning_input)
    artifact = PeopleSearchStageExecutor(provider, settings=settings).execute(
        planning_input=planning_input,
        proposals=plan.proposals,
        accepted_hypotheses=plan.accepted_hypotheses,
        acceptance=plan.acceptance,
        lane_decisions=plan.lane_decisions,
        tasks=plan.tasks,
        hypothesis_provider_calls=plan.hypothesis_provider_calls,
        model_profile_id=profile.profile_id,
    )
    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(f"{output.suffix}.tmp")
    temporary.write_text(artifact.model_dump_json(indent=2) + "\n", encoding="utf-8")
    temporary.replace(output)
    return {
        "stage_id": artifact.stage_id,
        "handoff_id": artifact.handoff_id,
        "role_demands": len(artifact.planning_input.role_demands),
        "accepted_hypotheses": len(artifact.accepted_hypotheses),
        "lane_decisions": len(artifact.lane_decisions),
        "tasks": len(artifact.tasks),
        "receipts": len(artifact.receipts),
        "source_leads": len(artifact.source_leads),
        "roles_with_relevant_leads": len({
            item.demand_id for item in artifact.source_leads if item.relevance == "account_role_relevant"
        }),
        "provider_calls": artifact.budgets.provider_calls,
        "planner_calls": artifact.budgets.hypothesis_provider_calls,
        "completion_state": artifact.completion_state,
        "output": str(output),
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(prog="python -m power_web_os.power_web_people_search")
    result.add_argument("--handoff-id", required=True)
    result.add_argument("--official-domain", required=True)
    result.add_argument("--official-domain-evidence-ref", action="append", required=True)
    result.add_argument("--account-alias", action="append")
    result.add_argument("--geography")
    result.add_argument("--language", default="ru")
    result.add_argument("--database-url")
    result.add_argument("--env-path", type=Path, default=Path(".env"))
    result.add_argument("--output", type=Path, required=True)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        summary = run(args)
    except Exception as exc:
        print(f"people_search_failed={type(exc).__name__}:{exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
