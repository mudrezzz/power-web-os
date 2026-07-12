"""Machine-check acceptance evidence for behavior-changing Radar slices."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

from power_web_os.application.radar.validation.contracts import (
    RadarPipelineAcceptanceManifest,
    RadarPipelineRequirementResult,
    RadarPipelineValidationReport,
)
from power_web_os.application.radar.validation.signal_monitoring_quality import (
    _list,
    control_match_summary as _control_match_summary,
    evaluate_signal_report as _evaluate_signal_report,
)


class RadarPipelineSliceValidator:
    """Validate tests, documentation traceability, and persisted runtime evidence."""

    def __init__(self, *, root: Path = Path(".")) -> None:
        self.root = root.resolve()

    def validate(
        self,
        *,
        manifest_path: Path,
        first_live_report: dict[str, Any] | None = None,
        second_live_report: dict[str, Any] | None = None,
        baseline_run_id: str = "",
        run_tests: bool = True,
        write_report: bool = True,
    ) -> RadarPipelineValidationReport:
        manifest = RadarPipelineAcceptanceManifest.load(self._path(manifest_path))
        test_exit_code, test_output = self._run_tests(manifest) if run_tests else (None, "tests_skipped")
        runtime_results, runtime_summary = self._runtime_results(
            manifest,
            first_live_report or {},
            second_live_report or {},
        )
        results: list[RadarPipelineRequirementResult] = []
        for requirement in manifest.requirements:
            static = self._static_result(manifest, requirement.id)
            runtime = runtime_results.get(requirement.id)
            evidence = [*static.evidence, *(runtime.evidence if runtime else [])]
            failed = static.status != "PASS" or (runtime is not None and runtime.status != "PASS")
            if requirement.test_node_ids and test_exit_code not in {0, None}:
                failed = True
                evidence.append(f"required pytest node set failed: {test_output}")
            results.append(RadarPipelineRequirementResult(
                requirement_id=requirement.id,
                status="FAIL" if failed else "PASS",
                evidence=evidence or [test_output],
                message=(runtime.message if runtime and runtime.message else static.message),
            ))
        validation_status = "PASS" if all(
            item.status == "PASS"
            for item in results
            if next(req for req in manifest.requirements if req.id == item.requirement_id).mandatory
        ) else "FAIL"
        report = RadarPipelineValidationReport(
            slice_id=manifest.slice_id,
            pipeline_id=manifest.pipeline_id,
            validation_status=validation_status,
            generated_at=_now(),
            baseline_run_id=baseline_run_id,
            first_live_run_id=str((first_live_report or {}).get("run_id") or (first_live_report or {}).get("signal_run_id") or ""),
            second_live_run_id=str((second_live_report or {}).get("run_id") or (second_live_report or {}).get("signal_run_id") or ""),
            test_exit_code=test_exit_code,
            requirements=results,
            runtime_summary=runtime_summary,
            deviations=manifest.retrospective,
        )
        if write_report:
            self._write_reports(manifest, report)
        return report

    def _run_tests(self, manifest: RadarPipelineAcceptanceManifest) -> tuple[int, str]:
        node_ids = list(dict.fromkeys(
            node_id for requirement in manifest.requirements for node_id in requirement.test_node_ids
        ))
        if not node_ids:
            return 1, "acceptance manifest has no test node IDs"
        completed = subprocess.run(
            [sys.executable, "-m", "pytest", *node_ids, "-q"],
            cwd=self.root,
            text=True,
            capture_output=True,
            check=False,
        )
        tail = "\n".join((completed.stdout + completed.stderr).splitlines()[-12:])
        return completed.returncode, tail or "pytest completed"

    def _static_result(
        self,
        manifest: RadarPipelineAcceptanceManifest,
        requirement_id: str,
    ) -> RadarPipelineRequirementResult:
        required_paths = [
            manifest.to_be_markdown,
            manifest.to_be_pdf,
            manifest.as_is_markdown,
            manifest.as_is_pdf,
            manifest.baseline_diagnostic,
        ]
        missing = [path for path in required_paths if path and not self._path(Path(path)).exists()]
        to_be = self._read(manifest.to_be_markdown)
        as_is = self._read(manifest.as_is_markdown)
        acceptance = self._path(Path(manifest.to_be_markdown).with_suffix(".acceptance.json"))
        traceable = requirement_id in to_be and requirement_id in acceptance.read_text(encoding="utf-8")
        if requirement_id in {"SM-PROC-01", "SM-PROC-02"}:
            traceable = traceable and manifest.slice_id in as_is and "Status: Implemented" in to_be
        if missing or not traceable:
            return RadarPipelineRequirementResult(
                requirement_id=requirement_id,
                status="FAIL",
                evidence=[*(f"missing:{item}" for item in missing)],
                message="Documentation traceability is incomplete.",
            )
        return RadarPipelineRequirementResult(
            requirement_id=requirement_id,
            status="PASS",
            evidence=[manifest.to_be_markdown, manifest.as_is_markdown],
        )

    def _runtime_results(
        self,
        manifest: RadarPipelineAcceptanceManifest,
        first: dict[str, Any],
        second: dict[str, Any],
    ) -> tuple[dict[str, RadarPipelineRequirementResult], dict[str, Any]]:
        if manifest.pipeline_id != "signal-monitoring":
            return {}, {}
        live = manifest.live_acceptance
        negative_controls = live.get("negative_controls", [])
        positive_controls = live.get("positive_controls", [])
        unknown_date_controls = live.get("unknown_date_controls", [])
        first_result = _evaluate_signal_report(first, negative_controls=negative_controls)
        second_result = _evaluate_signal_report(second, negative_controls=negative_controls)
        results: dict[str, RadarPipelineRequirementResult] = {}

        def result(requirement_id: str, ok: bool, *evidence: str) -> None:
            results[requirement_id] = RadarPipelineRequirementResult(
                requirement_id=requirement_id,
                status="PASS" if ok else "FAIL",
                evidence=list(evidence),
            )

        has_live = bool(first and second)
        result("SM-PLAN-01", has_live and first_result["orphan_decisions"] == 0, f"orphan_decisions={first_result['orphan_decisions']}")
        result("SM-SRC-01", has_live and first_result["opaque_known_tasks"] == 0, f"opaque_known_tasks={first_result['opaque_known_tasks']}")
        result("SM-SRC-02", has_live and first_result["unrestricted_official_tasks"] == 0, f"unrestricted_official_tasks={first_result['unrestricted_official_tasks']}")
        result("SM-SRC-03", has_live and first_result["open_web_task_count"] > 0, f"open_web_tasks={first_result['open_web_task_count']}")
        result("SM-AUD-01", has_live and first_result["receipt_gap_count"] == 0, f"receipt_gap_count={first_result['receipt_gap_count']}")
        result("SM-OBS-01", has_live and first_result["false_not_observed_count"] == 0, f"false_not_observed={first_result['false_not_observed_count']}")
        result("SM-WIN-01", has_live and first_result["initial_lookback_days"] == manifest.live_acceptance.get("initial_lookback_days", 365), f"initial_lookback_days={first_result['initial_lookback_days']}")
        result("SM-WIN-02", has_live and second_result["incremental_window_count"] > 0, f"incremental_windows={second_result['incremental_window_count']}")
        result("SM-WIN-03", has_live and second_result["failed_watermark_advances"] == 0, f"failed_watermark_advances={second_result['failed_watermark_advances']}")
        result("SM-VAL-01", has_live and first_result["observed_count"] >= manifest.live_acceptance.get("minimum_known_events_found", 2), f"observed_count={first_result['observed_count']}")
        result(
            "SM-VAL-02",
            has_live
            and first_result["rejected_observed_count"] == 0
            and first_result["negative_control_tested_count"] >= min(2, len(negative_controls))
            and first_result["negative_control_false_positive_count"] == 0,
            f"rejected_observed_count={first_result['rejected_observed_count']}",
            f"negative_controls_tested={first_result['negative_control_tested_count']}",
            f"negative_control_false_positives={first_result['negative_control_false_positive_count']}",
        )
        result(
            "SM-DED-01",
            has_live
            and second_result["previous_source_key_count"] > 0
            and second_result["duplicate_count"] > 0
            and second_result["republished_previous_source_count"] == 0,
            f"previous_source_keys={second_result['previous_source_key_count']}",
            f"duplicates_suppressed={second_result['duplicate_count']}",
            f"previous_sources_republished={second_result['republished_previous_source_count']}",
        )
        result("SM-TIME-01", has_live and first_result["retrieved_at_as_fresh_count"] == 0, f"retrieved_at_as_fresh={first_result['retrieved_at_as_fresh_count']}")
        result("SM-TIME-02", has_live and first_result["unknown_date_review_count"] >= len(unknown_date_controls), f"unknown_date_reviews={first_result['unknown_date_review_count']}")
        result("SM-TIME-03", has_live and first_result["out_of_window_confirmed_count"] == 0, f"out_of_window_confirmed={first_result['out_of_window_confirmed_count']}")
        result("SM-CAP-01", has_live and first_result["sources_without_capability_count"] == 0, f"sources_without_capability={first_result['sources_without_capability_count']}")
        result("SM-BIND-01", has_live and first_result["cross_entity_known_task_count"] == 0, f"cross_entity_known_tasks={first_result['cross_entity_known_task_count']}")
        result("SM-BIND-02", has_live and first_result["identity_confirmed_signal_count"] == 0, f"identity_confirmed={first_result['identity_confirmed_signal_count']}")
        result("SM-QUERY-01", has_live and first_result["alternate_query_count"] >= first_result["task_count"], f"alternate_queries={first_result['alternate_query_count']}/{first_result['task_count']}")
        retry_proven = first_result["transport_retry_proven"] + second_result["transport_retry_proven"]
        unretried_transport_errors = (
            first_result["unretried_transport_error_count"]
            + second_result["unretried_transport_error_count"]
        )
        result(
            "SM-RETRY-01",
            has_live and (retry_proven > 0 or unretried_transport_errors == 0),
            f"transport_retry_proven={retry_proven}",
            f"unretried_transport_errors={unretried_transport_errors}",
        )
        result("SM-SCORE-01", has_live and first_result["zero_score_observed_count"] == 0, f"zero_score_observed={first_result['zero_score_observed_count']}")
        result(
            "SM-BENCH-01",
            has_live
            and first_result["candidate_count"] == live.get("accepted_candidate_count", 0) + live.get("review_candidate_count", 0)
            and first_result["accepted_candidate_count"] == live.get("accepted_candidate_count", 0)
            and first_result["review_candidate_count"] == live.get("review_candidate_count", 0)
            and first_result["signal_rule_count"] == len(live.get("signal_codes", []))
            and first_result["candidate_signal_pair_count"] == first_result["candidate_count"] * first_result["signal_rule_count"],
            f"candidate_count={first_result['candidate_count']}",
            f"accepted={first_result['accepted_candidate_count']}",
            f"review={first_result['review_candidate_count']}",
            f"pairs={first_result['candidate_signal_pair_count']}",
        )
        positive_match = _control_match_summary(first, _list(positive_controls), expected="confirmed")
        negative_match = _control_match_summary(first, _list(negative_controls), expected="negative")
        unknown_match = _control_match_summary(first, _list(unknown_date_controls), expected="unknown")
        result(
            "SM-BENCH-02",
            has_live and positive_match["matched"] == len(_list(positive_controls)),
            f"positive_controls={positive_match['matched']}/{len(_list(positive_controls))}",
            f"missing={','.join(positive_match['missing'])}",
        )
        result(
            "SM-BENCH-03",
            has_live
            and negative_match["matched"] >= min(2, len(_list(negative_controls)))
            and unknown_match["matched"] >= len(_list(unknown_date_controls)),
            f"negative_controls={negative_match['matched']}/{len(_list(negative_controls))}",
            f"unknown_date_controls={unknown_match['matched']}/{len(_list(unknown_date_controls))}",
        )
        result(
            "SM-DED-02",
            has_live
            and second_result["previous_source_key_count"] > 0
            and second_result["republished_previous_source_count"] == 0
            and second_result["duplicate_count"] + second_result["duplicate_review_count"] > 0,
            f"previous_source_keys={second_result['previous_source_key_count']}",
            f"duplicates={second_result['duplicate_count']}",
            f"duplicate_reviews={second_result['duplicate_review_count']}",
            f"previous_sources_republished={second_result['republished_previous_source_count']}",
        )
        result("SM-AUD-02", has_live and first_result["unreasoned_retained_item_count"] == 0, f"unreasoned_items={first_result['unreasoned_retained_item_count']}")
        result("SM-ARCH-02", True, "architecture guardrails covered by pytest nodes")
        result("SM-PROC-02", has_live, f"first_run={bool(first)}", f"second_run={bool(second)}")
        summary = {"first_live": first_result, "second_live": second_result}
        return results, summary

    def _write_reports(
        self,
        manifest: RadarPipelineAcceptanceManifest,
        report: RadarPipelineValidationReport,
    ) -> None:
        json_path = self._path(Path(manifest.validation_json))
        markdown_path = self._path(Path(manifest.validation_markdown))
        json_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        lines = [
            f"# Validation Report: {report.slice_id}",
            "",
            f"Validation status: `{report.validation_status}`",
            "",
            f"Pipeline: `{report.pipeline_id}`",
            f"First live run: `{report.first_live_run_id or 'missing'}`",
            f"Second live run: `{report.second_live_run_id or 'missing'}`",
            "",
            "## Requirement Results",
            "",
            "| Requirement | Status | Evidence |",
            "|---|---|---|",
        ]
        lines.extend(
            f"| `{item.requirement_id}` | `{item.status}` | {'; '.join(item.evidence)} |"
            for item in report.requirements
        )
        lines.extend(["", "## Runtime Summary", "", "```json", json.dumps(report.runtime_summary, ensure_ascii=False, indent=2), "```", ""])
        if report.deviations:
            lines.extend(["## Process Retrospective", ""])
            lines.extend(
                f"- `{item.get('code', 'finding')}`: {item.get('finding', '')} Resolution: {item.get('resolution', '')}"
                for item in report.deviations
            )
            lines.append("")
        markdown_path.write_text("\n".join(lines), encoding="utf-8")

    def _path(self, path: Path) -> Path:
        return path if path.is_absolute() else self.root / path

    def _read(self, path: str) -> str:
        target = self._path(Path(path))
        return target.read_text(encoding="utf-8") if target.exists() else ""


def _now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
