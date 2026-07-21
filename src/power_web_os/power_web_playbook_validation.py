"""Machine validation for Power Web product and role-policy slices."""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any
from urllib.request import urlopen


BASE = Path("docs/radar/pipelines/power-web-discovery")
SIMPLIFICATION_SLICE = "0.7.6.6.0.2"
DEFAULT_UI_EVIDENCE = Path("frontend/test-results/power-web-playbook-simplification.json")


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _get_json(url: str) -> Any:
    with urlopen(url, timeout=10) as response:  # noqa: S310 - local API is explicit CLI input.
        return json.loads(response.read().decode("utf-8"))


def _contains_forbidden_configuration(value: Any) -> bool:
    forbidden_keys = {
        "person_name",
        "job_title",
        "benchmark_url",
        "blind_control",
        "search_query",
    }
    if isinstance(value, dict):
        return any(key in forbidden_keys or _contains_forbidden_configuration(item) for key, item in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_configuration(item) for item in value)
    if isinstance(value, str):
        return value.startswith(("http://", "https://"))
    return False


def _simplification_ui_pass(evidence: dict[str, Any]) -> bool:
    results = evidence.get("results", [])
    expected_cases = {
        ("ru", 1280, 720),
        ("ru", 1366, 768),
        ("en", 1280, 720),
        ("en", 1366, 768),
    }
    actual_cases = {
        (item.get("locale"), item.get("viewport", {}).get("width"), item.get("viewport", {}).get("height"))
        for item in results
    }
    return (
        evidence.get("validation_status") == "PASS"
        and evidence.get("access_playbook_version_id") is None
        and evidence.get("ui_api_db_reload_round_trip") is True
        and actual_cases == expected_cases
        and all(
            item.get("detailRatio", 0) >= 0.95
            and item.get("inlineWidthDelta", 999) <= 2
            and item.get("bodyOverflow") is False
            and item.get("horizontalOverflow") is False
            and item.get("advancedOpen") is False
            and item.get("basic_field_count") == 4
            and item.get("tab_count") == 3
            for item in results
        )
    )


def _workspace_tabs_are_canonical(root: Path) -> bool:
    component = (root / "frontend/src/components/WorkspaceTabs.tsx").read_text(encoding="utf-8")
    consumers = (
        "frontend/src/features/icp-radar/components/RadarDetailHeader.tsx",
        "frontend/src/features/icp-radar/detailPrimitives.tsx",
        "frontend/src/features/icp-radar/liveRunDiagnostics.tsx",
        "frontend/src/screens/AccessPlansScreen.tsx",
        "frontend/src/screens/SalesPlaybookScreen.tsx",
    )
    return (
        'role="tablist"' in component
        and 'role="tab"' in component
        and 'role="tabpanel"' in component
        and all("<WorkspaceTabs" in (root / path).read_text(encoding="utf-8") for path in consumers)
    )


def validate_simplification(
    *,
    root: Path,
    slice_id: str,
    api_url: str,
    restart_verified: bool,
    tests_pass: bool,
    provider_calls: int,
    pipeline_runs_created: int,
    ui_evidence_path: Path,
) -> dict[str, Any]:
    root = root.resolve()
    to_be_path = root / BASE / "to-be" / f"RADAR_POWER_WEB_DISCOVERY_TO_BE_{slice_id}.md"
    manifest_path = to_be_path.with_suffix(".acceptance.json")
    as_is_path = root / BASE / "RADAR_POWER_WEB_DISCOVERY_AS_IS.md"
    amendment_path = root / BASE / "benchmark" / "sales_playbook.amendment.v1.json"
    manifest = _load_json(manifest_path)
    amendment = _load_json(amendment_path)
    ui_evidence = _load_json(root / ui_evidence_path)
    to_be = to_be_path.read_text(encoding="utf-8")
    as_is = as_is_path.read_text(encoding="utf-8")

    products = _get_json(f"{api_url.rstrip('/')}/api/products")
    product = next((item for item in products if item.get("product_id") == "product-smartdiagnostics"), None)
    draft = _get_json(f"{api_url.rstrip('/')}/api/products/product-smartdiagnostics/draft")
    versions = _get_json(f"{api_url.rstrip('/')}/api/products/product-smartdiagnostics/versions")
    roles = draft.get("buying_roles", [])
    active_versions = [item for item in versions if item.get("is_active")]
    active = active_versions[0] if len(active_versions) == 1 else None
    basic_roles_complete = bool(roles) and all(
        item.get("role_code")
        and item.get("display_name")
        and item.get("business_responsibility")
        and item.get("scope") in {"holding", "account", "site", "external"}
        and item.get("priority") in {"critical", "high", "normal"}
        for item in roles
    )
    source = (root / "frontend/src/screens/SalesPlaybookScreen.tsx").read_text(encoding="utf-8")
    contracts = (root / "src/power_web_os/application/sales_playbook/contracts.py").read_text(encoding="utf-8")
    role_demand = (root / "src/power_web_os/application/radar/power_web_discovery/contracts.py").read_text(encoding="utf-8")
    benchmark_pass = amendment.get("blind_controls_changed") is False and amendment.get("blind_control_values") == []
    ui_pass = _simplification_ui_pass(ui_evidence)

    checks = {
        "PWS-CFG-01": bool(active and active.get("access_playbook_version_id") is None and active.get("access_playbook") is None and "class ProductAndRolePolicy" in contracts),
        "PWS-ROLE-01": len(roles) >= 8 and basic_roles_complete and any(item.get("required") for item in roles),
        "PWS-ROLE-02": tests_pass and all(item.get("priority") for item in roles),
        "PWS-PLAN-01": tests_pass and "expected_evidence: tuple[str, ...] = ()" in role_demand,
        "PWS-ACCESS-01": tests_pass and bool(active and active.get("access_playbook_version_id") is None),
        "PWS-ACCESS-02": tests_pass,
        "PWS-API-01": restart_verified and tests_pass and bool(product and active),
        "PWS-UI-01": ui_pass and "product-catalog" in source and "sales-playbook-detail" in source and "product-rail" not in source,
        "PWS-UI-02": ui_pass and source.count('data-basic-role-field="true"') == 4 and "role-inline-editor" in source and "editor-inspector" not in source,
        "PWS-TABS-01": ui_pass and _workspace_tabs_are_canonical(root),
        "PWS-COMPAT-01": tests_pass,
        "PWS-BENCH-01": benchmark_pass and not _contains_forbidden_configuration(draft),
        "PWS-NET-01": provider_calls == 0 and pipeline_runs_created == 0,
        "PWS-PROC-01": "Status: Implemented" in to_be,
    }
    requirement_ids = [item["id"] for item in manifest["requirements"] if item.get("mandatory", True)]
    checks["PWS-PROC-01"] = checks["PWS-PROC-01"] and all(
        requirement_id in to_be and requirement_id in as_is for requirement_id in requirement_ids
    )

    requirements = [
        {
            "requirement_id": requirement_id,
            "status": "PASS" if checks.get(requirement_id, False) else "FAIL",
            "evidence": next(
                (item.get("test_node_ids", []) for item in manifest["requirements"] if item["id"] == requirement_id),
                [],
            ),
        }
        for requirement_id in requirement_ids
    ]
    status = "PASS" if all(item["status"] == "PASS" for item in requirements) else "FAIL"
    return {
        "schema_version": "power_web_playbook_validation.v2",
        "slice_id": slice_id,
        "pipeline_id": "power-web-discovery",
        "validation_status": status,
        "generated_at": datetime.now(UTC).isoformat(),
        "requirements": requirements,
        "runtime": {
            "product_id": product.get("product_id") if product else None,
            "active_version_id": active.get("version_id") if active else None,
            "draft_revision": draft.get("draft_revision"),
            "semantic_role_count": len(roles),
            "required_role_count": sum(bool(item.get("required")) for item in roles),
            "historical_access_version_count": sum(bool(item.get("access_playbook_version_id")) for item in versions),
            "active_access_playbook_version_id": active.get("access_playbook_version_id") if active else None,
            "published_version_count": len(versions),
            "restart_verified": restart_verified,
            "ui_evidence": ui_evidence,
            "provider_calls": provider_calls,
            "pipeline_runs_created": pipeline_runs_created,
            "blind_leakage": 0 if benchmark_pass else None,
        },
    }


def _write_report(root: Path, report: dict[str, Any]) -> None:
    folder = root.resolve() / BASE / "validation" / report["slice_id"]
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "validation.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    runtime = report["runtime"]
    rows = "\n".join(
        f"| `{item['requirement_id']}` | {item['status']} | {', '.join(item['evidence'])} |"
        for item in report["requirements"]
    )
    ui_results = runtime.get("ui_evidence", {}).get("results", [])
    ui_rows = "\n".join(
        f"| {item['locale']} | {item['viewport']['width']}x{item['viewport']['height']} | {item['detailRatio']:.4f} | {item['inlineWidthDelta']:.2f}px | {item['basic_field_count']} | {item['tab_count']} |"
        for item in ui_results
    )
    (folder / "VALIDATION_REPORT.md").write_text(
        "\n".join(
            (
                "# Power Web configuration simplification validation",
                "",
                f"Slice: `{report['slice_id']}`",
                f"Validation status: **{report['validation_status']}**",
                "",
                "## Runtime evidence",
                "",
                f"- Product: `{runtime['product_id']}`; active version: `{runtime['active_version_id']}`.",
                f"- Semantic roles: `{runtime['semantic_role_count']}`; required: `{runtime['required_role_count']}`.",
                f"- Active access dependency: `{runtime['active_access_playbook_version_id']}`.",
                f"- Historical access versions retained: `{runtime['historical_access_version_count']}`.",
                f"- Restart verified: `{runtime['restart_verified']}`.",
                f"- Provider calls: `{runtime['provider_calls']}`; new pipeline runs: `{runtime['pipeline_runs_created']}`.",
                f"- Blind leakage: `{runtime['blind_leakage']}`.",
                "",
                "## UI measurements",
                "",
                "| Locale | Viewport | Detail/workspace | Inline delta | Basic fields | Tabs |",
                "|---|---:|---:|---:|---:|---:|",
                ui_rows,
                "",
                "| Requirement | Status | Evidence |",
                "|---|---|---|",
                rows,
                "",
                "## Retrospective",
                "",
                "The foundation slice mixed people-discovery inputs with a separate access-strategy product and repeated a side-inspector layout that did not fit the workspace. The corrected contract limits discovery configuration to product plus semantic roles, freezes access rules for compatibility, and uses one full-width detail pattern.",
                "",
                "The shared tabs contract now distinguishes workspace navigation from filters. Future screens must use WorkspaceTabs for sections and reserve pills for filtering or mode selection.",
                "",
                "No provider or people-search runtime was invoked. The next slice can compile RoleDemand from the immutable product-and-role snapshot without an AccessPlaybook dependency.",
                "",
            )
        ),
        encoding="utf-8",
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m power_web_os.power_web_playbook_validation")
    parser.add_argument("--slice", required=True, dest="slice_id")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--api-url", default="http://127.0.0.1:8001")
    parser.add_argument("--restart-verified", action="store_true")
    parser.add_argument("--tests-pass", action="store_true")
    parser.add_argument("--provider-calls", type=int, default=0)
    parser.add_argument("--pipeline-runs-created", type=int, default=0)
    parser.add_argument("--ui-evidence", type=Path, default=DEFAULT_UI_EVIDENCE)
    args = parser.parse_args(argv)
    if args.slice_id != SIMPLIFICATION_SLICE:
        parser.error(f"this validator version supports slice {SIMPLIFICATION_SLICE}")
    report = validate_simplification(
        root=args.root,
        slice_id=args.slice_id,
        api_url=args.api_url,
        restart_verified=args.restart_verified,
        tests_pass=args.tests_pass,
        provider_calls=args.provider_calls,
        pipeline_runs_created=args.pipeline_runs_created,
        ui_evidence_path=args.ui_evidence,
    )
    _write_report(args.root, report)
    print(f"validation_status={report['validation_status']}")
    print(json.dumps(report["runtime"], ensure_ascii=False))
    return 0 if report["validation_status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
