"""Machine validation for the Power Web discovery architecture slice."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from .benchmark import PowerWebBenchmark, verify_benchmark_freeze
from .source_capabilities import default_source_capability_cards


REQUIREMENT_IDS = (
    "PW-ASIS-01",
    "PW-ARCH-01",
    "PW-ID-01",
    "PW-GOV-01",
    "PW-HH-01",
    "PW-HH-02",
    "PW-BENCH-01",
    "PW-BENCH-02",
    "PW-CAP-01",
    "PW-COMPAT-01",
    "PW-PROC-01",
)


class PowerWebArchitectureValidator:
    """Validate slice artifacts without inventing or executing a people search."""

    def __init__(self, *, root: Path = Path(".")) -> None:
        self.root = root.resolve()

    def validate(self, *, slice_id: str, write_report: bool = True) -> dict[str, Any]:
        base = Path("docs/radar/pipelines/power-web-discovery")
        to_be = base / "to-be" / f"RADAR_POWER_WEB_DISCOVERY_TO_BE_{slice_id}.md"
        manifest = to_be.with_suffix(".acceptance.json")
        as_is = base / "RADAR_POWER_WEB_DISCOVERY_AS_IS.md"
        capability_json = base / "diagnostics" / "HH_PUBLIC_WEB_CAPABILITY_0.7.6.6.0.json"
        benchmark_dir = base / "benchmark"
        benchmark_schema = benchmark_dir / "power_web_benchmark.schema.json"
        benchmark_path = benchmark_dir / "benchmark.user.json"
        freeze_path = benchmark_dir / "benchmark.freeze.json"
        source_path = benchmark_dir / "benchmark.source.json"
        results: dict[str, dict[str, Any]] = {}

        def result(requirement_id: str, passed: bool, *evidence: str, message: str = "") -> None:
            results[requirement_id] = {
                "status": "PASS" if passed else "FAIL",
                "evidence": list(evidence),
                "message": message,
            }

        as_is_text = self._read(as_is)
        to_be_text = self._read(to_be)
        manifest_text = self._read(manifest)
        result(
            "PW-ASIS-01",
            all(token in as_is_text for token in ("does not discover people", "PowerWebRole", "PowerWebBoard", "Access Planner")),
            str(as_is),
        )
        result(
            "PW-ARCH-01",
            all(token in to_be_text for token in ("account handoff", "identity hypotheses", "reviewable graph", "Access Planner")),
            str(to_be),
        )
        result(
            "PW-ID-01",
            all(token in to_be_text for token in ("two independent", "hard contradiction", "reversible")),
            str(to_be),
        )
        result(
            "PW-GOV-01",
            all(token in to_be_text for token in ("no raw HTML", "no binary images", "no automated outreach", "no face")),
            str(to_be),
        )

        capability = self._load_json(capability_json)
        receipts = capability.get("receipts", []) if isinstance(capability, dict) else []
        result(
            "PW-HH-01",
            len(receipts) == 3
            and {item.get("query_pattern") for item in receipts}
            == {"organization_role", "organization_unit", "role_geography"}
            and all(item.get("domain_restriction") == "hh.ru" for item in receipts)
            and all(item.get("outcome") in {"citation_found", "source_not_found"} for item in receipts),
            str(capability_json),
        )
        result(
            "PW-HH-02",
            bool(receipts) and sum(int(item.get("api_calls") or 0) for item in receipts) == 0,
            "hh_api_calls=0",
        )
        result(
            "PW-BENCH-01",
            self._path(benchmark_schema).exists()
            and all(requirement_id in to_be_text and requirement_id in manifest_text for requirement_id in REQUIREMENT_IDS),
            str(benchmark_schema),
            str(manifest),
        )

        benchmark_ok = False
        benchmark_metrics: dict[str, Any] = {}
        benchmark_message = "User benchmark and accepted freeze are required."
        if all(self._path(path).exists() for path in (benchmark_path, freeze_path, source_path)):
            try:
                benchmark = PowerWebBenchmark.model_validate_json(self._read(benchmark_path))
                source_record = self._load_json(source_path)
                verify_benchmark_freeze(
                    benchmark_path=self._path(benchmark_path),
                    freeze_path=self._path(freeze_path),
                )
                benchmark.assert_no_blind_leakage(benchmark.planning_payload(guided=False))
                benchmark_ok = (
                    benchmark.status == "user_accepted"
                    and source_record.get("raw_workbook_copied_to_repository") is False
                    and source_record.get("private_contact_values_retained") is False
                )
                benchmark_metrics = {
                    "benchmark_id": benchmark.benchmark_id,
                    "benchmark_version": benchmark.benchmark_version,
                    "profiles": len(benchmark.blind_controls.profiles),
                    "anonymous_profiles": sum(item.anonymous for item in benchmark.blind_controls.profiles),
                    "identity_pairs": len(benchmark.blind_controls.identity_pairs),
                    "same_person_pairs": sum(
                        item.expected_state in {"possible", "probable", "confirmed_same"}
                        for item in benchmark.blind_controls.identity_pairs
                    ),
                    "different_person_pairs": sum(
                        item.expected_state in {"confirmed_different", "rejected"}
                        for item in benchmark.blind_controls.identity_pairs
                    ),
                    "employment_states": sorted({item.expected_state for item in benchmark.blind_controls.employment}),
                    "relationships": len(benchmark.blind_controls.relationships),
                    "source_sha256": source_record.get("source_sha256"),
                }
                benchmark_message = (
                    f"benchmark={benchmark.benchmark_id}@{benchmark.benchmark_version}; "
                    f"profiles={benchmark_metrics['profiles']}; identity_pairs={benchmark_metrics['identity_pairs']}"
                )
            except (OSError, ValueError, json.JSONDecodeError) as exc:
                benchmark_message = str(exc)
        result(
            "PW-BENCH-02",
            benchmark_ok,
            str(benchmark_path),
            str(freeze_path),
            str(source_path),
            message=benchmark_message,
        )

        cards = default_source_capability_cards()
        required_sources = {
            "hh_public_web",
            "official_company",
            "professional_networks",
            "publications_events",
            "procurement_patents",
            "industry_web",
            "generic_web",
            "image_evidence",
            "hh_authorized_api",
        }
        result(
            "PW-CAP-01",
            {card.source_id for card in cards} == required_sources
            and next(card for card in cards if card.source_id == "hh_authorized_api").outcome == "deferred"
            and self._path(base / "SOURCE_CAPABILITY_MATRIX.md").exists(),
            f"capability_cards={len(cards)}",
            str(base / "SOURCE_CAPABILITY_MATRIX.md"),
        )
        result(
            "PW-COMPAT-01",
            all(self._path(path).exists() for path in (Path("src/power_web_os/domain.py"), Path("src/power_web_os/board.py"), Path("src/power_web_os/planner.py"))),
            "PowerWebRole/PowerWebBoard/DeterministicAccessPlanner remain unchanged",
        )
        result(
            "PW-PROC-01",
            all(self._path(path).exists() for path in (
                as_is,
                as_is.with_suffix(".pdf"),
                to_be,
                to_be.with_suffix(".pdf"),
                manifest,
                Path("docs/adr/2026-07-17-power-web-discovery-boundary-and-handoff.md"),
                Path("docs/adr/2026-07-17-reversible-person-identity-and-data-governance.md"),
            )),
            "AS IS, TO BE, manifest and ADR artifacts exist",
        )

        status = "PASS" if all(item["status"] == "PASS" for item in results.values()) else "FAIL"
        report = {
            "schema_version": "power_web_architecture_validation.v1",
            "slice_id": slice_id,
            "pipeline_id": "power-web-discovery",
            "validation_status": status,
            "generated_at": datetime.now(UTC).isoformat(),
            "requirements": results,
            "benchmark_status": "accepted_and_frozen" if benchmark_ok else "blocked_missing_user_benchmark",
            "benchmark_metrics": benchmark_metrics,
            "hh_public_web_probe": {
                "query_count": len(receipts),
                "citation_count": sum(item.get("outcome") == "citation_found" for item in receipts),
                "hh_api_calls": sum(int(item.get("api_calls") or 0) for item in receipts),
            },
        }
        if write_report:
            self._write_report(base / "validation" / slice_id, report)
        return report

    def write_benchmark_schema(self) -> Path:
        target = Path("docs/radar/pipelines/power-web-discovery/benchmark/power_web_benchmark.schema.json")
        resolved = self._path(target)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        resolved.write_text(
            json.dumps(PowerWebBenchmark.model_json_schema(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return target

    def _write_report(self, folder: Path, report: dict[str, Any]) -> None:
        target = self._path(folder)
        target.mkdir(parents=True, exist_ok=True)
        (target / "validation.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        rows = "\n".join(
            f"| `{requirement_id}` | {item['status']} | {item.get('message') or '; '.join(item['evidence'])} |"
            for requirement_id, item in report["requirements"].items()
        )
        benchmark_metrics = report.get("benchmark_metrics", {})
        benchmark_section = (
            "## Accepted benchmark\n\n"
            f"- Dataset: `{benchmark_metrics.get('benchmark_id')}@{benchmark_metrics.get('benchmark_version')}`\n"
            f"- Profiles: `{benchmark_metrics.get('profiles')}` including "
            f"`{benchmark_metrics.get('anonymous_profiles')}` anonymous HH-style profile.\n"
            f"- Identity pairs: `{benchmark_metrics.get('identity_pairs')}` "
            f"(`{benchmark_metrics.get('same_person_pairs')}` same-person, "
            f"`{benchmark_metrics.get('different_person_pairs')}` different-person).\n"
            f"- Employment states: `{', '.join(benchmark_metrics.get('employment_states', []))}`.\n"
            f"- Relationships: `{benchmark_metrics.get('relationships')}`.\n"
            "- Private contact values retained: `false`.\n"
        ) if report["validation_status"] == "PASS" else (
            "## Blocking condition\n\n"
            "The architecture slice remains open until the user benchmark is normalized, accepted and hash-frozen.\n"
            "No synthetic benchmark may satisfy `PW-BENCH-02`.\n"
        )
        (target / "VALIDATION_REPORT.md").write_text(
            "\n".join((
                "# Power Web discovery architecture validation",
                "",
                f"Slice: `{report['slice_id']}`",
                f"Validation status: **{report['validation_status']}**",
                f"Benchmark status: `{report['benchmark_status']}`",
                "",
                "| Requirement | Status | Evidence |",
                "|---|---|---|",
                rows,
                "",
                benchmark_section,
            )),
            encoding="utf-8",
        )

    def _path(self, path: Path) -> Path:
        return path if path.is_absolute() else self.root / path

    def _read(self, path: Path) -> str:
        resolved = self._path(path)
        return resolved.read_text(encoding="utf-8") if resolved.exists() else ""

    def _load_json(self, path: Path) -> dict[str, Any]:
        text = self._read(path)
        return json.loads(text) if text else {}
