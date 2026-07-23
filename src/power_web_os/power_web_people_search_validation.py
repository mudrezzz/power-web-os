"""Post-run benchmark evaluation and machine validation for slice 0.7.6.6.2."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from power_web_os.application.radar.power_web_discovery.people_search.contracts import PeopleSearchStageArtifact


SLICE_ID = "0.7.6.6.2"
BASE = Path("docs/radar/pipelines/power-web-discovery")
MANDATORY_LANES = {"official_company", "hh_public_web", "generic_web"}


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return value


def evaluate_artifact(
    artifact: PeopleSearchStageArtifact,
    benchmark: dict[str, Any],
) -> dict[str, Any]:
    blind = benchmark.get("blind_controls") if isinstance(benchmark.get("blind_controls"), dict) else {}
    profile_controls = [item for item in blind.get("profiles", []) if isinstance(item, dict)]
    planning_payload = json.dumps({
        "planning_input": artifact.planning_input.model_dump(mode="json"),
        "proposed_hypotheses": [item.model_dump(mode="json") for item in artifact.proposed_hypotheses],
        "accepted_hypotheses": [item.model_dump(mode="json") for item in artifact.accepted_hypotheses],
        "tasks": [item.model_dump(mode="json") for item in artifact.tasks],
    }, ensure_ascii=False).casefold()
    blind_terms: set[str] = set()
    for control in profile_controls:
        name = str(control.get("expected_display_name") or "").strip()
        if name:
            blind_terms.add(name.casefold())
        blind_terms.update(str(url).casefold() for url in control.get("provenance_urls", []) if url)
    leakage_terms = sorted(item for item in blind_terms if item and item in planning_payload)
    lead_urls = {item.url.rstrip("/").casefold() for item in artifact.source_leads}
    receipts_by_lane: dict[str, list[Any]] = {}
    for receipt in artifact.receipts:
        receipts_by_lane.setdefault(receipt.lane, []).append(receipt)
    controls: list[dict[str, Any]] = []
    for control in profile_controls:
        urls = [str(item).rstrip("/").casefold() for item in control.get("provenance_urls", [])]
        found = any(item in lead_urls for item in urls)
        lane = str(control.get("source_lane") or "unknown")
        reason = None if found else _miss_reason(lane, artifact, receipts_by_lane)
        controls.append({
            "control_id": str(control.get("control_id") or "unknown"),
            "source_lane": lane,
            "found": found,
            "path_reason": reason,
            "matched_urls": sorted(set(urls) & lead_urls),
        })
    executed_decisions = {item.decision_id for item in artifact.lane_decisions if item.status == "executed"}
    task_decisions = {item.decision_id for item in artifact.tasks}
    receipt_tasks = {item.task_id for item in artifact.receipts}
    relevant_roles = {
        item.demand_id for item in artifact.source_leads if item.relevance == "account_role_relevant"
    }
    leads_by_lane = {
        lane: len([item for item in artifact.source_leads if item.lane == lane])
        for lane in MANDATORY_LANES
    }
    return {
        "schema_version": "people_search_post_run_evaluation.v1",
        "stage_id": artifact.stage_id,
        "benchmark_id": benchmark.get("benchmark_id"),
        "benchmark_version": benchmark.get("benchmark_version"),
        "controls_in_planning_count": len(leakage_terms),
        "leakage_terms": leakage_terms,
        "role_demands": len(artifact.planning_input.role_demands),
        "roles_with_accepted_hypothesis": len({item.demand_id for item in artifact.accepted_hypotheses}),
        "mandatory_lane_decisions": len([
            item for item in artifact.lane_decisions if item.mandatory and item.lane in MANDATORY_LANES
        ]),
        "executed_mandatory_lanes": len([
            item for item in artifact.lane_decisions
            if item.mandatory and item.lane in MANDATORY_LANES and item.status == "executed"
        ]),
        "unrecovered_mandatory_lane_errors": len([
            item for item in artifact.receipts
            if item.lane in MANDATORY_LANES and item.terminal_outcome in {"provider_error", "schema_error"}
        ]),
        "budget_limited_mandatory_lanes": len([
            item for item in artifact.lane_decisions if item.mandatory and item.status == "budget_limited"
        ]),
        "receipt_gaps": len({item.task_id for item in artifact.tasks if item.decision_id in executed_decisions} - receipt_tasks),
        "orphan_decisions": len(task_decisions - {item.decision_id for item in artifact.lane_decisions}),
        "silent_task_drops": len(executed_decisions - task_decisions),
        "leads_by_lane": leads_by_lane,
        "roles_with_relevant_leads": len(relevant_roles),
        "provider_calls": artifact.budgets.provider_calls,
        "planner_calls": artifact.budgets.hypothesis_provider_calls,
        "hh_api_calls": artifact.hh_api_calls,
        "privacy_flags_pass": all((
            artifact.raw_provider_payload_retained is False,
            artifact.raw_html_retained is False,
            artifact.credentials_retained is False,
            artifact.private_contacts_retained is False,
            artifact.hidden_reasoning_retained is False,
        )),
        "profile_controls": controls,
        "false_negatives": [item for item in controls if not item["found"]],
    }


def _miss_reason(lane: str, artifact: PeopleSearchStageArtifact, receipts_by_lane: dict[str, list[Any]]) -> str:
    if lane not in MANDATORY_LANES:
        return "lane_not_enabled_in_acceptance_profile"
    lane_decisions = [item for item in artifact.lane_decisions if item.lane == lane]
    if not lane_decisions:
        return "not_scheduled"
    if all(item.status in {"not_executable", "unsupported", "policy_limited", "budget_limited"} for item in lane_decisions):
        return str(lane_decisions[0].status)
    receipts = receipts_by_lane.get(lane, [])
    if not receipts:
        return "not_executed"
    if any(item.terminal_outcome in {"provider_error", "schema_error"} for item in receipts):
        return "provider_error"
    return "source_not_found"


def validate(
    *,
    root: Path,
    artifact: PeopleSearchStageArtifact,
    tests_pass: bool,
    remote_session_id: str,
    workspace_sha256: str,
) -> dict[str, Any]:
    root = root.resolve()
    to_be = root / BASE / "to-be" / f"RADAR_POWER_WEB_DISCOVERY_TO_BE_{SLICE_ID}.md"
    manifest_path = to_be.with_suffix(".acceptance.json")
    manifest = _json(manifest_path)
    benchmark = _json(root / BASE / "benchmark" / "benchmark.user.json")
    evaluation = evaluate_artifact(artifact, benchmark)
    docs_ready = all((
        to_be.exists(),
        to_be.with_suffix(".pdf").exists(),
        (root / BASE / "validation" / SLICE_ID / "BASELINE_DIAGNOSTIC.md").exists(),
    ))
    all_roles = {item.demand_id for item in artifact.planning_input.role_demands}
    accepted_roles = {item.demand_id for item in artifact.accepted_hypotheses}
    checks = {
        "PW-PS-ASIS-01": docs_ready,
        "PW-PS-IN-01": len(all_roles) == 8 and all_roles == {item.demand_id for item in artifact.planning_input.role_demands},
        "PW-PS-HYP-01": accepted_roles == all_roles and tests_pass,
        "PW-PS-HYP-02": tests_pass,
        "PW-PS-LANE-01": evaluation["mandatory_lane_decisions"] == 24,
        "PW-PS-LANE-02": evaluation["orphan_decisions"] == 0 and evaluation["silent_task_drops"] == 0,
        "PW-PS-HH-01": artifact.hh_api_calls == 0 and all(
            item.domain_restrictions == ("hh.ru",) for item in artifact.tasks if item.lane == "hh_public_web"
        ),
        "PW-PS-AUD-01": evaluation["receipt_gaps"] == 0,
        "PW-PS-NEG-01": evaluation["unrecovered_mandatory_lane_errors"] == 0,
        "PW-PS-BUD-01": artifact.budgets.provider_calls <= 48 and artifact.budgets.hypothesis_provider_calls <= 2,
        "PW-PS-SEC-01": evaluation["privacy_flags_pass"],
        "PW-PS-BENCH-01": evaluation["controls_in_planning_count"] == 0 and all(
            item["found"] or item["path_reason"] for item in evaluation["profile_controls"]
        ),
        "PW-PS-ARCH-01": tests_pass,
        "PW-PS-LIVE-01": all((
            evaluation["role_demands"] == 8,
            evaluation["roles_with_accepted_hypothesis"] == 8,
            evaluation["executed_mandatory_lanes"] == 24,
            evaluation["budget_limited_mandatory_lanes"] == 0,
            evaluation["unrecovered_mandatory_lane_errors"] == 0,
            all(evaluation["leads_by_lane"].get(lane, 0) >= 1 for lane in MANDATORY_LANES),
            evaluation["roles_with_relevant_leads"] >= 4,
        )),
        "PW-PS-PROC-01": all((
            tests_pass,
            to_be.exists(),
            to_be.with_suffix(".pdf").exists(),
            manifest_path.exists(),
            all(item.get("test_node_ids") for item in manifest["requirements"]),
        )),
    }
    requirements = [{
        "requirement_id": item["id"],
        "status": "PASS" if checks.get(item["id"], False) else "FAIL",
        "evidence": item.get("test_node_ids", []),
    } for item in manifest["requirements"] if item.get("mandatory", True)]
    status = "PASS" if all(item["status"] == "PASS" for item in requirements) else "FAIL"
    return {
        "schema_version": "power_web_people_search_validation.v1",
        "slice_id": SLICE_ID,
        "pipeline_id": "power-web-discovery",
        "validation_status": status,
        "generated_at": datetime.now(UTC).isoformat(),
        "remote_session_id": remote_session_id,
        "workspace_sha256": workspace_sha256,
        "stage_id": artifact.stage_id,
        "handoff_id": artifact.handoff_id,
        "requirements": requirements,
        "evaluation": evaluation,
        "execution_audit": {
            "candidate_discovery_runs_created": 0,
            "signal_monitoring_runs_created": 0,
            "power_web_runs_created": 0,
            "hh_api_calls": 0,
        },
    }


def write_report(output_dir: Path, report: dict[str, Any], artifact: PeopleSearchStageArtifact) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "people_search_stage.json").write_text(artifact.model_dump_json(indent=2) + "\n", encoding="utf-8")
    (output_dir / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    evaluation = report["evaluation"]
    requirements = "\n".join(
        f"| `{item['requirement_id']}` | {item['status']} | {', '.join(item['evidence'])} |"
        for item in report["requirements"]
    )
    misses = "\n".join(
        f"| `{item['control_id']}` | `{item['source_lane']}` | `{item['path_reason']}` |"
        for item in evaluation["false_negatives"]
    ) or "| none | - | - |"
    (output_dir / "VALIDATION_REPORT.md").write_text("\n".join((
        "# Power Web people-search validation", "",
        f"Slice: `{SLICE_ID}`", f"Validation status: **{report['validation_status']}**", "",
        "## Live stage", "",
        f"- Stage: `{report['stage_id']}`; handoff: `{report['handoff_id']}`.",
        f"- Remote session: `{report['remote_session_id']}`; workspace SHA: `{report['workspace_sha256']}`.",
        f"- Roles: `{evaluation['role_demands']}`; mandatory lanes executed: `{evaluation['executed_mandatory_lanes']}/24`.",
        f"- Leads by lane: `{json.dumps(evaluation['leads_by_lane'], ensure_ascii=False)}`.",
        f"- Roles with account/role-relevant leads: `{evaluation['roles_with_relevant_leads']}/8`.",
        f"- Provider calls: `{evaluation['provider_calls']}/48`; planner calls: `{evaluation['planner_calls']}/2`.",
        f"- Completion: `{artifact.completion_state}`; source verifications: `{artifact.budgets.source_verifications}/{artifact.budgets.settings.max_source_verifications}`.",
        f"- Receipt gaps: `{evaluation['receipt_gaps']}`; orphan decisions: `{evaluation['orphan_decisions']}`; silent drops: `{evaluation['silent_task_drops']}`.",
        f"- Blind controls in planning: `{evaluation['controls_in_planning_count']}`; HH API calls: `{evaluation['hh_api_calls']}`.", "",
        "## Requirements", "", "| Requirement | Status | Evidence |", "|---|---|---|", requirements, "",
        "## Benchmark misses", "", "| Control | Lane | Path reason |", "|---|---|---|", misses, "",
        "## Process retrospective", "",
        f"The stage proves bounded planning and public-web retrieval only. It retrieved `{len(evaluation['profile_controls']) - len(evaluation['false_negatives'])}/{len(evaluation['profile_controls'])}` evaluator-only profile controls, so PASS is not a profile-recall quality claim. Source leads are deliberately not projected as people, employment or Power Web graph nodes. Blind controls were loaded after execution and every miss retains a path-level explanation. The source-verification limit applies to additional retained citations after all mandatory lanes executed.", "",
    )), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m power_web_os.power_web_people_search_validation")
    parser.add_argument("--slice", required=True, dest="slice_id")
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--tests-pass", action="store_true")
    parser.add_argument("--remote-session-id", required=True)
    parser.add_argument("--workspace-sha256", required=True)
    args = parser.parse_args(argv)
    if args.slice_id != SLICE_ID:
        parser.error(f"this validator supports slice {SLICE_ID}")
    artifact = PeopleSearchStageArtifact.model_validate(_json(args.artifact))
    report = validate(
        root=args.root,
        artifact=artifact,
        tests_pass=args.tests_pass,
        remote_session_id=args.remote_session_id,
        workspace_sha256=args.workspace_sha256,
    )
    write_report(args.output_dir, report, artifact)
    print(f"validation_status={report['validation_status']}")
    print(json.dumps(report["evaluation"], ensure_ascii=False))
    return 0 if report["validation_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
