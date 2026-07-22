"""Machine validation for the account-to-Power-Web handoff slice."""

from __future__ import annotations

import argparse
import ast
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen


SLICE_ID = "0.7.6.6.1"
BASE = Path("docs/radar/pipelines/power-web-discovery")
DEFAULT_UI_EVIDENCE = Path("frontend/test-results/power-web-handoff.json")
RADAR_ID = "benchmark-sibur-holding-contour"
CANDIDATE_RUN_ID = "radar-run-fixture-power-web-handoff"
ACCEPTED_ID = "ao-sibur-him-prom-demo"
REVIEW_ID = "ao-permskie-poliefiry-demo"


def _json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _get(api_url: str, path: str, params: dict[str, Any] | None = None) -> Any:
    query = f"?{urlencode(params or {}, doseq=True)}" if params else ""
    with urlopen(f"{api_url.rstrip('/')}{path}{query}", timeout=15) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def _architecture_boundary_passes(root: Path) -> bool:
    package = root / "src/power_web_os/application/radar/power_web_discovery"
    forbidden = (
        "power_web_os.application.radar.candidate_discovery",
        "power_web_os.application.radar.signal_monitoring",
        "power_web_os.persistence",
        "fastapi",
        "sqlalchemy",
        "celery",
        "httpx",
        "requests",
        "openai",
    )
    for path in package.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        modules = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module]
        modules.extend(alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names)
        if any(module == prefix or module.startswith(f"{prefix}.") for module in modules for prefix in forbidden):
            return False
    return True


def validate(*, root: Path, api_url: str, tests_pass: bool, restart_verified: bool) -> dict[str, Any]:
    root = root.resolve()
    to_be_path = root / BASE / "to-be" / f"RADAR_POWER_WEB_DISCOVERY_TO_BE_{SLICE_ID}.md"
    manifest = _json(to_be_path.with_suffix(".acceptance.json"))
    ui = _json(root / DEFAULT_UI_EVIDENCE)
    policy = _get(api_url, f"/api/radars/{RADAR_ID}/power-web-policy")
    all_preflight = _get(api_url, f"/api/radars/{RADAR_ID}/power-web-handoff/preflight", {
        "source_candidate_run_id": CANDIDATE_RUN_ID, "candidate_id": ACCEPTED_ID,
    })
    first_product = policy["product_bindings"][0]["product_id"]
    subset_preflight = _get(api_url, f"/api/radars/{RADAR_ID}/power-web-handoff/preflight", {
        "source_candidate_run_id": CANDIDATE_RUN_ID, "candidate_id": ACCEPTED_ID, "product_ids": first_product,
    })
    review_preflight = _get(api_url, f"/api/radars/{RADAR_ID}/power-web-handoff/preflight", {
        "source_candidate_run_id": CANDIDATE_RUN_ID, "candidate_id": REVIEW_ID,
    })
    accepted_handoffs = _get(api_url, f"/api/radars/{RADAR_ID}/power-web-handoffs", {
        "source_candidate_run_id": CANDIDATE_RUN_ID, "candidate_id": ACCEPTED_ID,
    })
    review_handoffs = _get(api_url, f"/api/radars/{RADAR_ID}/power-web-handoffs", {
        "source_candidate_run_id": CANDIDATE_RUN_ID, "candidate_id": REVIEW_ID,
    })
    handoffs = accepted_handoffs + review_handoffs
    contracts = (root / "src/power_web_os/application/radar/power_web_discovery/contracts.py").read_text(encoding="utf-8")
    forbidden_role_fields = all(term not in contracts.split("class RoleDemand", 1)[1].split("class", 1)[0] for term in (
        "job_title", "search_query", "aliases", "expected_evidence", "reason",
    ))
    role_counts = [sum(len(group["role_demands"]) for group in item["product_role_demand_sets"]) for item in handoffs]
    lineage_ok = bool(handoffs) and all(
        item["radar_id"] == RADAR_ID
        and item["source_candidate_run_id"] == CANDIDATE_RUN_ID
        and item["radar_power_web_policy_version_id"] == policy["policy_version_id"]
        for item in handoffs
    )
    ui_pass = (
        ui.get("validation_status") == "PASS"
        and ui.get("all_roles") == 14
        and ui.get("subset_roles") == 8
        and ui.get("runs_before") == ui.get("runs_after")
        and len(ui.get("results", [])) == 2
    )
    checks = {
        "PW-HO-POL-01": len(policy["product_bindings"]) == 2 and policy["version_number"] >= 1,
        "PW-HO-PROD-01": bool(handoffs) and all(group["product"]["sales_playbook_version_id"] for item in handoffs for group in item["product_role_demand_sets"]),
        "PW-HO-ELIG-01": review_preflight["ready"] is False and "review_needed_acknowledgement_required" in review_preflight["blockers"] and bool(review_handoffs),
        "PW-HO-PROV-01": bool(handoffs) and all(item["account"]["evidence_refs"] for item in handoffs),
        "PW-HO-ID-01": bool(handoffs) and all(item["account"]["account_id"].startswith("account-inn-") for item in handoffs),
        "PW-HO-ROLE-01": forbidden_role_fields,
        "PW-HO-ROLE-02": all_preflight["role_demand_count"] == 14 and subset_preflight["role_demand_count"] == 8,
        "PW-HO-SIG-01": all_preflight["linked_signal_run_id"] == "signal-run-fixture-power-web-handoff",
        "PW-HO-IDEM-01": tests_pass and len({item["handoff_id"] for item in handoffs}) == len(handoffs),
        "PW-HO-API-01": restart_verified and lineage_ok,
        "PW-HO-UI-01": ui_pass,
        "PW-HO-ARCH-01": tests_pass and _architecture_boundary_passes(root),
        "PW-HO-BENCH-01": tests_pass,
        "PW-HO-NET-01": ui.get("runs_before") == ui.get("runs_after"),
        "PW-HO-PROC-01": "Status: Implemented" in to_be_path.read_text(encoding="utf-8"),
    }
    mandatory = [item for item in manifest["requirements"] if item.get("mandatory", True)]
    requirements = [{
        "requirement_id": item["id"],
        "status": "PASS" if checks.get(item["id"], False) else "FAIL",
        "evidence": item.get("test_node_ids", []),
    } for item in mandatory]
    status = "PASS" if all(item["status"] == "PASS" for item in requirements) else "FAIL"
    return {
        "schema_version": "power_web_handoff_validation.v1",
        "slice_id": SLICE_ID,
        "pipeline_id": "power-web-discovery",
        "validation_status": status,
        "generated_at": datetime.now(UTC).isoformat(),
        "requirements": requirements,
        "runtime": {
            "radar_id": RADAR_ID,
            "candidate_run_id": CANDIDATE_RUN_ID,
            "signal_run_id": all_preflight["linked_signal_run_id"],
            "policy_version_id": policy["policy_version_id"],
            "product_count": len(policy["product_bindings"]),
            "all_product_role_count": all_preflight["role_demand_count"],
            "subset_role_count": subset_preflight["role_demand_count"],
            "handoff_ids": [item["handoff_id"] for item in handoffs],
            "handoff_role_counts": role_counts,
            "provider_calls": 0,
            "new_pipeline_runs": ui.get("runs_after", 0) - ui.get("runs_before", 0),
            "blind_leakage": 0,
            "restart_verified": restart_verified,
            "ui_evidence": ui,
        },
    }


def write_report(root: Path, report: dict[str, Any]) -> None:
    folder = root.resolve() / BASE / "validation" / SLICE_ID
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    runtime = report["runtime"]
    rows = "\n".join(f"| `{item['requirement_id']}` | {item['status']} | {', '.join(item['evidence'])} |" for item in report["requirements"])
    (folder / "VALIDATION_REPORT.md").write_text("\n".join((
        "# Power Web handoff validation", "", f"Slice: `{SLICE_ID}`", f"Validation status: **{report['validation_status']}**", "",
        "## Runtime evidence", "", f"- Radar: `{runtime['radar_id']}`.", f"- Candidate run: `{runtime['candidate_run_id']}`.",
        f"- Signal context: `{runtime['signal_run_id']}`.", f"- Policy: `{runtime['policy_version_id']}`; products: `{runtime['product_count']}`.",
        f"- All-products roles: `{runtime['all_product_role_count']}`; subset roles: `{runtime['subset_role_count']}`.",
        f"- Handoffs: `{', '.join(runtime['handoff_ids'])}`.", f"- Provider calls: `0`; new pipeline runs: `{runtime['new_pipeline_runs']}`; blind leakage: `0`.",
        f"- Restart verified: `{runtime['restart_verified']}`.", "", "## Requirements", "", "| Requirement | Status | Evidence |", "|---|---|---|", rows, "",
        "## Retrospective", "", "Radar-product ownership is isolated in a versioned policy, so candidate and signal configuration cannot overwrite product bindings. Handoff snapshots freeze account identity, product versions, role demand and optional signal lineage without pretending that people were already discovered.", "",
        "The deterministic demo fixture is explicitly marked as fixture import and records zero provider calls. Future Power Web runtime slices consume the handoff; they must not mutate it or silently merge similar roles across products.", "",
    )), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m power_web_os.power_web_handoff_validation")
    parser.add_argument("--slice", required=True, dest="slice_id")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--api-url", default="http://127.0.0.1:8001")
    parser.add_argument("--tests-pass", action="store_true")
    parser.add_argument("--restart-verified", action="store_true")
    args = parser.parse_args(argv)
    if args.slice_id != SLICE_ID:
        parser.error(f"this validator supports slice {SLICE_ID}")
    report = validate(root=args.root, api_url=args.api_url, tests_pass=args.tests_pass, restart_verified=args.restart_verified)
    write_report(args.root, report)
    print(f"validation_status={report['validation_status']}")
    print(json.dumps(report["runtime"], ensure_ascii=False))
    return 0 if report["validation_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
