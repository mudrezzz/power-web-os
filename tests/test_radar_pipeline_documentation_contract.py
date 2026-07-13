from __future__ import annotations

import json
from pathlib import Path

from pypdf import PdfReader


AS_IS_MD = Path("docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md")
AS_IS_PDF = Path("docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.pdf")
PIPELINE_REGISTRY = Path("docs/radar/pipelines/README.md")
TO_BE_036_MD = Path("docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_0.7.6.3.6.md")
TO_BE_036_PDF = Path("docs/radar/to-be/RADAR_SEARCH_PIPELINE_TO_BE_0.7.6.3.6.pdf")
SIGNAL_TO_BE_MD = Path(
    "docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.1.md"
)
SIGNAL_TO_BE_PDF = Path(
    "docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.1.pdf"
)
SIGNAL_AS_IS_MD = Path("docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.md")
SIGNAL_AS_IS_PDF = Path("docs/radar/pipelines/signal-monitoring/RADAR_SIGNAL_MONITORING_AS_IS.pdf")
SIGNAL_1821_TO_BE_MD = Path(
    "docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.1.md"
)
SIGNAL_1821_ACCEPTANCE = SIGNAL_1821_TO_BE_MD.with_suffix(".acceptance.json")
SIGNAL_1821_VALIDATION = Path(
    "docs/radar/pipelines/signal-monitoring/validation/0.7.6.4.18.2.1/validation.json"
)
SIGNAL_1822_TO_BE_MD = Path(
    "docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.2.2.md"
)
SIGNAL_1822_ACCEPTANCE = SIGNAL_1822_TO_BE_MD.with_suffix(".acceptance.json")
SIGNAL_1822_VALIDATION = Path(
    "docs/radar/pipelines/signal-monitoring/validation/0.7.6.4.18.2.2/validation.json"
)
SIGNAL_1831_TO_BE_MD = Path(
    "docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_0.7.6.4.18.3.1.md"
)
SIGNAL_1831_ACCEPTANCE = SIGNAL_1831_TO_BE_MD.with_suffix(".acceptance.json")
SIGNAL_1831_VALIDATION = Path(
    "docs/radar/pipelines/signal-monitoring/validation/0.7.6.4.18.3.1/validation.json"
)
PIPELINE_SPLIT_UI_CONTRACT = Path("docs/radar/pipelines/RADAR_PIPELINE_SPLIT_UI_CONTRACT.md")
PIPELINE_SPLIT_VALIDATION = Path("docs/radar/pipelines/validation/0.7.6.4.18.3/validation.json")
SIGNAL_SURFACE_RCA = Path(
    "docs/radar/pipelines/signal-monitoring/rca/SIGNAL_MONITORING_SURFACE_RCA_0.7.6.4.18.3.2.md"
)
SIGNAL_SURFACE_VALIDATION = Path(
    "docs/radar/pipelines/validation/0.7.6.4.18.3.2/validation.json"
)
SKILL_PATHS = [
    Path(".agents/skills/radar-pipeline-to-be-design/SKILL.md"),
    Path(".agents/skills/radar-pipeline-as-is-sync/SKILL.md"),
    Path(".agents/skills/radar-pipeline-to-as-is-finalize/SKILL.md"),
]

REQUIRED_SECTIONS = [
    "## 5. Backend Roles",
    "## 7. Planning Loop",
    "## 9. Retrieval, Extraction, And Recovery Loop",
    "## 10. Registry Lookup Loop",
    "## 11. Search Expansion Loop",
    "## 13. Checkpoints And Adaptive Actions",
    "## 14. Signal-Monitoring Handoff",
    "## 15. Budget Model",
    "## 16. Source Lifecycle",
    "## 19. Context Management",
    "## 20. Extension Points",
    "## 21. Test Map",
    "## 22. AS IS / TO BE Maintenance Lifecycle",
]

FORBIDDEN_PRODUCT_MARKERS = (
    "OPENROUTER_API_KEY",
    "DADATA_API_KEY",
    "DADATA_SECRET_KEY",
    "Authorization",
    "Bearer ",
    "chain_of_thought",
    "hidden_reasoning",
    "internal_thoughts",
)

FORBIDDEN_PDF_MERMAID_MARKERS = (
    "```mermaid",
    "flowchart TD",
    "flowchart LR",
    "sequenceDiagram",
    "stateDiagram-v2",
)


def test_radar_pipeline_as_is_markdown_has_required_contract_sections() -> None:
    text = AS_IS_MD.read_text(encoding="utf-8")

    assert "Status: AS IS" in text
    assert "Generated PDF: `docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.pdf`" in text
    for section in REQUIRED_SECTIONS:
        assert section in text
    for marker in FORBIDDEN_PRODUCT_MARKERS:
        assert marker not in text


def test_radar_pipeline_as_is_pdf_exists_and_uses_rendered_diagrams() -> None:
    assert AS_IS_PDF.exists()
    reader = PdfReader(str(AS_IS_PDF))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    assert "Radar Search Pipeline AS IS" in text
    assert "Figure 1. End-to-end Radar execution flow" in text
    assert "Figure 6. AS IS / TO BE maintenance cycle" in text
    assert "| Term |" not in text
    assert "| Role |" not in text
    for marker in FORBIDDEN_PDF_MERMAID_MARKERS:
        assert marker not in text
    for marker in FORBIDDEN_PRODUCT_MARKERS:
        assert marker not in text


def test_radar_pipeline_documentation_skills_are_discoverable() -> None:
    for path in SKILL_PATHS:
        text = path.read_text(encoding="utf-8")
        assert text.startswith("---\nname: radar-pipeline-")
        assert "pipeline=<pipeline_id>" in text
        for pipeline_id in ["candidate-discovery", "signal-monitoring", "power-web-discovery"]:
            assert pipeline_id in text

    to_be = SKILL_PATHS[0].read_text(encoding="utf-8")
    as_is = SKILL_PATHS[1].read_text(encoding="utf-8")
    finalize = SKILL_PATHS[2].read_text(encoding="utf-8")
    assert "Do not implement production code" in to_be
    assert "RADAR_SIGNAL_MONITORING_TO_BE_<slice>.pdf" in to_be
    assert "docs/radar/pipelines/signal-monitoring/to-be/" in to_be
    assert "--source <selected-to-be.md> --output <selected-to-be.pdf>" in to_be
    assert "--source <selected-as-is.md> --output <selected-as-is.pdf>" in as_is
    assert "Do not mark a TO BE behavior as AS IS unless it is implemented" in finalize


def test_radar_pipeline_registry_defines_pipeline_paths() -> None:
    text = PIPELINE_REGISTRY.read_text(encoding="utf-8")

    for pipeline_id in ["candidate-discovery", "signal-monitoring", "power-web-discovery"]:
        assert f"`{pipeline_id}`" in text
    assert "pipeline=<pipeline_id>" in text
    assert "docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md" in text
    assert "docs/radar/pipelines/signal-monitoring/to-be/RADAR_SIGNAL_MONITORING_TO_BE_<slice>.md" in text
    assert "docs/radar/pipelines/power-web-discovery/to-be/RADAR_POWER_WEB_DISCOVERY_TO_BE_<slice>.md" in text


def test_current_radar_pipeline_to_be_pdf_exists_and_is_rendered() -> None:
    assert TO_BE_036_MD.exists()
    assert TO_BE_036_PDF.exists()
    reader = PdfReader(str(TO_BE_036_PDF))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    assert "Radar Search Pipeline TO BE: 0.7.6.3.6" in text
    assert "Figure 1. Source-profile-driven recall expansion flow" in text
    assert "Figure 2. Expansion target queue flow" in text
    for marker in FORBIDDEN_PDF_MERMAID_MARKERS:
        assert marker not in text
    for marker in FORBIDDEN_PRODUCT_MARKERS:
        assert marker not in text


def test_signal_monitoring_to_be_exists_and_is_rendered() -> None:
    assert SIGNAL_TO_BE_MD.exists()
    assert SIGNAL_TO_BE_PDF.exists()

    markdown = SIGNAL_TO_BE_MD.read_text(encoding="utf-8")
    assert "Pipeline id: `signal-monitoring`" in markdown
    assert '`not_observed` must never mean "we did not search"' in markdown
    assert "Runtime signal monitoring" in markdown

    reader = PdfReader(str(SIGNAL_TO_BE_PDF))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    assert "Radar Signal Monitoring TO BE: 0.7.6.4.1" in text
    assert "Figure 1. End-to-end Radar execution flow" in text
    for marker in FORBIDDEN_PDF_MERMAID_MARKERS:
        assert marker not in text
    for marker in FORBIDDEN_PRODUCT_MARKERS:
        assert marker not in text


def test_signal_monitoring_as_is_exists_after_recorded_runtime_slice() -> None:
    assert SIGNAL_AS_IS_MD.exists()
    assert SIGNAL_AS_IS_PDF.exists()

    markdown = SIGNAL_AS_IS_MD.read_text(encoding="utf-8")
    assert "Status: AS IS" in markdown
    assert "Pipeline id: `signal-monitoring`" in markdown
    assert "run-recorded-signal-monitoring" in markdown
    assert "`not_observed` never means" in markdown

    reader = PdfReader(str(SIGNAL_AS_IS_PDF))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)

    assert "Radar Signal Monitoring AS IS" in text
    assert "Figure 1. End-to-end Radar execution flow" in text
    assert "| Signal code |" not in text
    for marker in FORBIDDEN_PDF_MERMAID_MARKERS:
        assert marker not in text
    for marker in FORBIDDEN_PRODUCT_MARKERS:
        assert marker not in text


def test_signal_monitoring_slice_acceptance_is_traceable_to_finalized_as_is() -> None:
    manifest = json.loads(SIGNAL_1821_ACCEPTANCE.read_text(encoding="utf-8"))
    validation = json.loads(SIGNAL_1821_VALIDATION.read_text(encoding="utf-8"))
    to_be = SIGNAL_1821_TO_BE_MD.read_text(encoding="utf-8")
    as_is = SIGNAL_AS_IS_MD.read_text(encoding="utf-8")
    requirement_ids = {item["id"] for item in manifest["requirements"] if item["mandatory"]}
    validation_results = {item["requirement_id"]: item["status"] for item in validation["requirements"]}

    assert "Status: Implemented" in to_be
    assert "0.7.6.4.18.2.1" in as_is
    assert validation["validation_status"] == "PASS"
    assert requirement_ids
    assert all(requirement_id in to_be for requirement_id in requirement_ids)
    assert all(requirement_id in as_is for requirement_id in requirement_ids)
    assert all(validation_results.get(requirement_id) == "PASS" for requirement_id in requirement_ids)
    assert all(item.get("test_node_ids") for item in manifest["requirements"] if item["mandatory"])


def test_signal_monitoring_quality_slice_is_traceable_to_finalized_as_is() -> None:
    manifest = json.loads(SIGNAL_1822_ACCEPTANCE.read_text(encoding="utf-8"))
    to_be = SIGNAL_1822_TO_BE_MD.read_text(encoding="utf-8")
    as_is = SIGNAL_AS_IS_MD.read_text(encoding="utf-8")
    requirement_ids = {item["id"] for item in manifest["requirements"] if item.get("mandatory", True)}

    assert manifest["slice_id"] == "0.7.6.4.18.2.2"
    assert "SM-PROC-02" in requirement_ids
    assert requirement_ids
    assert all(requirement_id in to_be for requirement_id in requirement_ids)
    assert all(item.get("test_node_ids") for item in manifest["requirements"] if item.get("mandatory", True))
    if "Status: Implemented" in to_be:
        assert SIGNAL_1822_VALIDATION.exists()
        validation = json.loads(SIGNAL_1822_VALIDATION.read_text(encoding="utf-8"))
        validation_results = {item["requirement_id"]: item["status"] for item in validation["requirements"]}
        assert validation["validation_status"] == "PASS"
        assert "0.7.6.4.18.2.2" in as_is
        assert all(requirement_id in as_is for requirement_id in requirement_ids)
        assert all(validation_results.get(requirement_id) == "PASS" for requirement_id in requirement_ids)


def test_signal_monitoring_settings_slice_is_traceable_to_finalized_as_is() -> None:
    manifest = json.loads(SIGNAL_1831_ACCEPTANCE.read_text(encoding="utf-8"))
    validation = json.loads(SIGNAL_1831_VALIDATION.read_text(encoding="utf-8"))
    to_be = SIGNAL_1831_TO_BE_MD.read_text(encoding="utf-8")
    as_is = SIGNAL_AS_IS_MD.read_text(encoding="utf-8")
    requirement_ids = {item["id"] for item in manifest["requirements"] if item.get("mandatory", True)}
    validation_results = {item["requirement_id"]: item["status"] for item in validation["requirements"]}

    assert "Status: Implemented" in to_be
    assert validation["validation_status"] == "PASS"
    assert validation["runtime"]["cold_open_passes"] == 10
    assert validation["runtime"]["detail_bytes"] <= 250_000
    assert validation["runtime"]["history_bytes"] <= 250_000
    assert all(requirement_id in to_be for requirement_id in requirement_ids)
    assert all(requirement_id in as_is for requirement_id in requirement_ids)
    assert all(validation_results.get(requirement_id) == "PASS" for requirement_id in requirement_ids)


def test_radar_pipeline_split_ui_contract_is_validated() -> None:
    contract = PIPELINE_SPLIT_UI_CONTRACT.read_text(encoding="utf-8")
    validation = json.loads(PIPELINE_SPLIT_VALIDATION.read_text(encoding="utf-8"))

    assert "Status: Implemented by slice `0.7.6.4.18.3`" in contract
    assert "source_run_id" in contract
    assert "Candidate and signal budget counters" in contract
    assert validation["validation_status"] == "PASS"
    assert validation["candidate_run_id"].startswith("radar-run-")
    assert len(validation["signal_run_ids"]) >= 2
    assert all(status == "PASS" for status in validation["checks"].values())


def test_signal_monitoring_product_surface_is_semantically_validated() -> None:
    contract = PIPELINE_SPLIT_UI_CONTRACT.read_text(encoding="utf-8")
    rca = SIGNAL_SURFACE_RCA.read_text(encoding="utf-8")
    validation = json.loads(SIGNAL_SURFACE_VALIDATION.read_text(encoding="utf-8"))

    assert "candidate-criterion check is never presented as a found signal" in contract
    assert "incremental report was a delta" in rca
    assert validation["validation_status"] == "PASS"
    assert validation["pair_count"] == 12
    assert validation["initial"] == {"confirmed": 4, "review": 3, "searched_negative": 5}
    assert validation["incremental"]["new_confirmed"] == 0
    assert validation["incremental"]["cumulative_confirmed"] == 4
    assert validation["unresolved_retained_evidence_count"] == 0
    assert all(status == "PASS" for status in validation["checks"].values())
