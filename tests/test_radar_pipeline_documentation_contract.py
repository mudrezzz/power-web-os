from __future__ import annotations

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
    "## 14. Signal Search",
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
