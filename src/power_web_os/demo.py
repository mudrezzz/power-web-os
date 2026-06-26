from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from power_web_os.domain import Account, Playbook
from power_web_os.icp_radar import icp_radar_artifact_to_payload
from power_web_os.icp_radar_catalog import build_icp_radar_catalog
from power_web_os.icp_radar_xlsx import load_icp_radar_workbook
from power_web_os.live_icp_radar import (
    OpenRouterWebSearchProvider,
    OpenRouterDiscoveryPlanner,
    build_live_mini_radar_artifact,
    build_live_mini_radar_definition,
    build_live_mini_radar_search_plan_artifact,
)
from power_web_os.demo_preflight import build_radar_preflight_report, print_preflight_report
from power_web_os.planner import DeterministicAccessPlanner
from power_web_os.radar import AccountRadar
from power_web_os.application.radar_runtime_config import build_effective_runtime_config_report
from power_web_os.radar_benchmark import generate_radar_benchmark_report
from power_web_os.serialization import (
    access_plan_from_payload,
    account_from_payload,
    access_plan_to_payload,
    playbook_from_payload,
)
from power_web_os.workflow import AccessPlanningState, AccessPlanningWorkflow


def load_demo_account(path: Path) -> tuple[Account, Playbook]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return account_from_payload(payload["account"]), playbook_from_payload(payload["playbook"])


def build_demo_plan(path: Path) -> dict[str, Any]:
    account, playbook = load_demo_account(path)
    plan = DeterministicAccessPlanner().build_plan(account, playbook)
    return access_plan_to_payload(plan)


def build_access_plan_artifact(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return build_access_plan_artifact_from_payload(
        account_payload=payload["account"],
        playbook_payload=payload["playbook"],
        task_context={
            "task_id": "demo-access-plan",
            "correlation_id": "demo-slice-0.2",
            "requester": "demo",
            "source_path": str(path),
        },
    )


def build_access_plan_artifact_from_payload(
    *,
    account_payload: dict[str, Any],
    playbook_payload: dict[str, Any],
    task_context: dict[str, Any],
) -> dict[str, Any]:
    workflow = AccessPlanningWorkflow()
    state = AccessPlanningState(
        task_context=task_context,
        account_payload=account_payload,
        playbook_payload=playbook_payload,
    )
    result = workflow.invoke(state)
    if result.access_plan is None:
        raise RuntimeError("AccessPlanningWorkflow did not produce an access plan artifact")
    return result.access_plan


def generate_access_plan_artifact(
    *,
    input_path: Path,
    output_path: Path,
    frontend_output_path: Path | None = None,
) -> dict[str, Any]:
    artifact = build_access_plan_artifact(input_path)
    _write_json(output_path, artifact)
    if frontend_output_path is not None:
        _write_json(frontend_output_path, artifact)
    return artifact


def generate_account_radar_artifact(
    *,
    input_path: Path,
    output_path: Path,
    frontend_output_path: Path,
    frontend_access_plans_dir: Path,
) -> dict[str, Any]:
    portfolio_payload = json.loads(input_path.read_text(encoding="utf-8"))
    radar = AccountRadar()
    radar_items = []
    access_plan_artifacts: dict[str, dict[str, Any]] = {}

    for entry in portfolio_payload["portfolio"]:
        account_payload = entry["account"]
        playbook_payload = entry["playbook"]
        account = account_from_payload(account_payload)
        access_plan_artifact = build_access_plan_artifact_from_payload(
            account_payload=account_payload,
            playbook_payload=playbook_payload,
            task_context={
                "task_id": f"demo-access-plan-{account.account_id}",
                "correlation_id": "demo-slice-0.4",
                "requester": "demo",
                "source_path": str(input_path),
            },
        )
        access_plan = access_plan_from_payload(access_plan_artifact["access_plan"])
        access_plan_path = f"/demo/access_plans/{account.account_id}.json"
        radar_items.append(
            radar.build_item(
                account=account,
                access_plan=access_plan,
                stage=str(entry.get("stage", "Mapping")),
                access_plan_path=access_plan_path,
            )
        )
        access_plan_artifacts[account.account_id] = access_plan_artifact

    ranked_items = radar.rank(radar_items)
    artifact = radar.to_payload(
        ranked_items,
        workflow_metadata={
            "workflow_name": "AccountRadar",
            "artifact_version": "0.4",
            "account_count": len(ranked_items),
            "access_workflow": "AccessPlanningWorkflow",
            "planner": "DeterministicAccessPlanner",
            "task_id": "demo-account-radar",
            "correlation_id": "demo-slice-0.4",
        },
    )

    _write_json(output_path, artifact)
    _write_json(frontend_output_path, artifact)
    for account_id, access_plan_artifact in access_plan_artifacts.items():
        _write_json(frontend_access_plans_dir / f"{account_id}.json", access_plan_artifact)
    return artifact


def generate_icp_radar_artifact(
    *,
    input_path: Path,
    output_path: Path,
    frontend_output_path: Path,
    normalized_output_path: Path,
) -> dict[str, Any]:
    artifact = icp_radar_artifact_to_payload(load_icp_radar_workbook(input_path))
    _write_json(output_path, artifact)
    _write_json(frontend_output_path, artifact)
    _write_json(normalized_output_path, artifact)
    return artifact


def generate_icp_radar_catalog_artifact(
    *,
    input_path: Path,
    output_path: Path,
    frontend_output_path: Path,
) -> dict[str, Any]:
    artifact = build_icp_radar_catalog_from_workbook(input_path)
    _write_json(output_path, artifact)
    _write_json(frontend_output_path, artifact)
    return artifact


def build_icp_radar_catalog_from_workbook(input_path: Path) -> dict[str, Any]:
    active_radar_artifact = icp_radar_artifact_to_payload(load_icp_radar_workbook(input_path))
    return build_icp_radar_catalog(active_radar_artifact)


def seed_icp_radar_catalog_database(*, input_path: Path, database_url: str | None = None) -> dict[str, Any]:
    from power_web_os.persistence.config import DatabaseSettings
    from power_web_os.persistence.engine import create_database_engine, create_session_factory, session_scope
    from power_web_os.persistence.seed import seed_radar_catalog

    settings = DatabaseSettings.from_env(database_url=database_url)
    engine = create_database_engine(settings)
    session_factory = create_session_factory(engine)
    catalog = build_icp_radar_catalog_from_workbook(input_path)

    with session_scope(session_factory) as session:
        result = seed_radar_catalog(session, catalog)
    return result.to_payload()


def generate_live_mini_icp_radar_plan(
    *,
    output_path: Path,
) -> dict[str, Any]:
    artifact = build_live_mini_radar_search_plan_artifact()
    _write_json(output_path, artifact)
    return artifact


def generate_live_mini_icp_radar_artifact(
    *,
    output_path: Path,
    frontend_output_path: Path,
) -> dict[str, Any]:
    artifact = build_live_mini_radar_artifact(
        provider=OpenRouterWebSearchProvider(),
        discovery_planner=OpenRouterDiscoveryPlanner(),
        live=True,
    )
    _assert_no_secrets(artifact)
    _write_json(output_path, artifact)
    _write_json(frontend_output_path, artifact)
    return artifact


def generate_persisted_live_mini_icp_radar_artifact(
    *,
    output_path: Path,
    frontend_output_path: Path,
    database_url: str | None = None,
) -> dict[str, Any]:
    from power_web_os.application.persisted_live_radar import (
        PersistedLiveRadarRunCommand,
        PersistedLiveRadarRunService,
    )
    from power_web_os.persistence import (
        SqlAlchemyRadarDefinitionRepository,
        SqlAlchemyRadarRunOutputRepository,
        SqlAlchemyRadarRunRepository,
        SqlAlchemyRadarRunTechnicalTraceRepository,
        create_database_engine,
        create_session_factory,
        session_scope,
    )
    from power_web_os.workflows.live_radar_executor import WorkflowLiveRadarArtifactExecutor
    from power_web_os.integrations.dadata_provider import dadata_source_registry_from_env

    engine = create_database_engine(database_url=database_url)
    session_factory = create_session_factory(engine)

    with session_scope(session_factory) as session:
        service = PersistedLiveRadarRunService(
            run_repository=SqlAlchemyRadarRunRepository(session),
            output_repository=SqlAlchemyRadarRunOutputRepository(session),
            definition_repository=SqlAlchemyRadarDefinitionRepository(session),
            executor=WorkflowLiveRadarArtifactExecutor(
                provider=OpenRouterWebSearchProvider(),
                discovery_planner=OpenRouterDiscoveryPlanner(),
                source_registry=dadata_source_registry_from_env(),
                technical_trace_repository=SqlAlchemyRadarRunTechnicalTraceRepository(session),
            ),
            runtime_config_provider=lambda: _demo_runtime_config_payload(component="worker"),
            technical_tracer=None,
        )
        api_runtime_config = _demo_runtime_config_payload(component="cli")
        result = service.run(PersistedLiveRadarRunCommand(
            live=True,
            task_context=_task_context_from_runtime_config(api_runtime_config),
            api_runtime_config=api_runtime_config,
        ))

    if result.artifact is None:
        raise RuntimeError(f"Persisted live Radar run failed: {result.run.error_message}")
    _assert_no_secrets(result.artifact)
    artifact = result.artifact
    _write_json(output_path, artifact)
    _write_json(frontend_output_path, artifact)
    return artifact


def _demo_runtime_config_payload(*, component: str) -> dict[str, Any]:
    return build_effective_runtime_config_report(
        component=component,
        dotenv_path=Path.cwd() / ".env",
    ).to_payload()


def _task_context_from_runtime_config(runtime_config: dict[str, Any]) -> dict[str, Any]:
    config = runtime_config.get("config") if isinstance(runtime_config.get("config"), dict) else {}
    radar = config.get("radar") if isinstance(config.get("radar"), dict) else {}
    return {
        **{key: value for key, value in radar.items() if value is not None},
        "source": "demo_persisted_cli",
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _assert_no_secrets(payload: dict[str, Any]) -> None:
    serialized = json.dumps(payload, ensure_ascii=False)
    # Env var names are safe in remediation text; secret-looking values are not.
    forbidden = ("Authorization", "Bearer ", "sk-or-")
    if any(token in serialized for token in forbidden):
        raise RuntimeError("Refusing to write live radar artifact containing secret-like content")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(prog="power-web-os-demo")
    parser.add_argument(
        "command",
        nargs="?",
        default="print-plan",
        choices=(
            "print-plan",
            "generate-access-plan",
            "generate-account-radar",
            "generate-icp-radar",
            "generate-icp-radar-catalog",
            "seed-radar-db",
            "run-live-mini-icp-radar",
            "run-live-mini-icp-radar-persisted",
            "preflight-radar",
            "run-radar-benchmark",
        ),
    )
    parser.add_argument("--input", type=Path, default=root / "demo" / "sample_account.json")
    parser.add_argument("--output", type=Path, default=root / "demo" / "output" / "access_plan.json")
    parser.add_argument(
        "--frontend-output",
        type=Path,
        default=root / "frontend" / "public" / "demo" / "access_plan.json",
    )
    parser.add_argument("--portfolio-input", type=Path, default=root / "demo" / "sample_portfolio.json")
    parser.add_argument("--radar-output", type=Path, default=root / "demo" / "output" / "account_radar.json")
    parser.add_argument(
        "--frontend-radar-output",
        type=Path,
        default=root / "frontend" / "public" / "demo" / "account_radar.json",
    )
    parser.add_argument(
        "--frontend-access-plans-dir",
        type=Path,
        default=root / "frontend" / "public" / "demo" / "access_plans",
    )
    parser.add_argument(
        "--icp-radar-input",
        type=Path,
        default=root / "demo" / "fixtures" / "icp_radar" / "sibur_icp_pass1.xlsx",
    )
    parser.add_argument(
        "--icp-radar-output",
        type=Path,
        default=root / "demo" / "output" / "icp_radar.json",
    )
    parser.add_argument(
        "--frontend-icp-radar-output",
        type=Path,
        default=root / "frontend" / "public" / "demo" / "icp_radar.json",
    )
    parser.add_argument(
        "--normalized-icp-radar-output",
        type=Path,
        default=root / "demo" / "fixtures" / "icp_radar" / "toir_sibur_icp_radar.json",
    )
    parser.add_argument(
        "--icp-radar-catalog-output",
        type=Path,
        default=root / "demo" / "output" / "icp_radars.json",
    )
    parser.add_argument(
        "--frontend-icp-radar-catalog-output",
        type=Path,
        default=root / "frontend" / "public" / "demo" / "icp_radars.json",
    )
    parser.add_argument(
        "--live-mini-radar-output",
        type=Path,
        default=root / "demo" / "output" / "live_mini_icp_radar_run.json",
    )
    parser.add_argument(
        "--frontend-live-mini-radar-output",
        type=Path,
        default=root / "frontend" / "public" / "demo" / "live_mini_icp_radar_run.json",
    )
    parser.add_argument(
        "--live-mini-radar-plan-output",
        type=Path,
        default=root / "demo" / "output" / "live_mini_icp_radar_search_plan.json",
    )
    parser.add_argument("--database-url", default=None)
    parser.add_argument("--radar-id", default="toir-quick-live")
    parser.add_argument("--api-url", default="http://127.0.0.1:8001")
    parser.add_argument(
        "--benchmark-output",
        type=Path,
        default=root / "demo" / "output" / "radar_benchmark_report.json",
    )
    parser.add_argument("--benchmark-poll-interval-seconds", type=float, default=5.0)
    parser.add_argument("--benchmark-timeout-seconds", type=float, default=900.0)
    parser.add_argument("--benchmark-profile", choices=("benchmark_smoke", "benchmark_live"), default="benchmark_smoke")
    parser.add_argument("--profile", choices=("static", "recorded", "benchmark_smoke", "benchmark_live"), default="recorded")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--show-runtime-config", action="store_true")
    parser.add_argument("--live-probes", action="store_true")
    parser.add_argument(
        "--probe",
        action="append",
        choices=("dadata", "openrouter-web", "openrouter-perplexity", "extraction-schema", "all"),
        default=[],
    )
    parser.add_argument("--dry-run-plan", action="store_true")
    parser.add_argument("--live", action="store_true")
    args = parser.parse_args()

    if args.command == "generate-access-plan":
        artifact = generate_access_plan_artifact(
            input_path=args.input,
            output_path=args.output,
            frontend_output_path=args.frontend_output,
        )
    elif args.command == "generate-account-radar":
        artifact = generate_account_radar_artifact(
            input_path=args.portfolio_input,
            output_path=args.radar_output,
            frontend_output_path=args.frontend_radar_output,
            frontend_access_plans_dir=args.frontend_access_plans_dir,
        )
    elif args.command == "generate-icp-radar":
        artifact = generate_icp_radar_artifact(
            input_path=args.icp_radar_input,
            output_path=args.icp_radar_output,
            frontend_output_path=args.frontend_icp_radar_output,
            normalized_output_path=args.normalized_icp_radar_output,
        )
    elif args.command == "generate-icp-radar-catalog":
        artifact = generate_icp_radar_catalog_artifact(
            input_path=args.icp_radar_input,
            output_path=args.icp_radar_catalog_output,
            frontend_output_path=args.frontend_icp_radar_catalog_output,
        )
    elif args.command == "seed-radar-db":
        artifact = seed_icp_radar_catalog_database(
            input_path=args.icp_radar_input,
            database_url=args.database_url,
        )
    elif args.command == "run-live-mini-icp-radar":
        if args.dry_run_plan:
            artifact = generate_live_mini_icp_radar_plan(
                output_path=args.live_mini_radar_plan_output,
            )
        elif args.live:
            artifact = generate_live_mini_icp_radar_artifact(
                output_path=args.live_mini_radar_output,
                frontend_output_path=args.frontend_live_mini_radar_output,
            )
        else:
            parser.error("run-live-mini-icp-radar requires --dry-run-plan or --live")
    elif args.command == "run-live-mini-icp-radar-persisted":
        if not args.live:
            parser.error("run-live-mini-icp-radar-persisted requires --live")
        artifact = generate_persisted_live_mini_icp_radar_artifact(
            output_path=args.live_mini_radar_output,
            frontend_output_path=args.frontend_live_mini_radar_output,
            database_url=args.database_url,
        )
    elif args.command == "preflight-radar":
        if args.profile not in {"static", "recorded"}:
            parser.error("preflight-radar --profile must be static or recorded")
        artifact = build_radar_preflight_report(
            radar_id=args.radar_id,
            database_url=args.database_url,
            profile=args.profile,
            show_runtime_config=args.show_runtime_config,
            live_probes=args.live_probes,
            probes=tuple(args.probe),
        )
        _assert_no_secrets(artifact)
        print_preflight_report(artifact, as_json=args.json)
        if not artifact.get("ready_for_live_run"):
            raise SystemExit(1)
        return
    elif args.command == "run-radar-benchmark":
        benchmark_profile = args.profile if args.profile in {"benchmark_smoke", "benchmark_live"} else args.benchmark_profile
        artifact = generate_radar_benchmark_report(
            api_url=args.api_url,
            profile=benchmark_profile,
            radar_id=args.radar_id,
            output_path=args.benchmark_output,
            poll_interval_seconds=args.benchmark_poll_interval_seconds,
            timeout_seconds=args.benchmark_timeout_seconds,
        )
    else:
        artifact = build_demo_plan(args.input)
    print(json.dumps(artifact, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
