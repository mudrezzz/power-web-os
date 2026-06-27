from __future__ import annotations

from pathlib import Path

from pypdf import PdfReader


AS_IS_MD = Path("docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.md")
AS_IS_PDF = Path("docs/radar/RADAR_SEARCH_PIPELINE_AS_IS.pdf")
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
    assert "Rendered diagram:" in text
    for marker in FORBIDDEN_PDF_MERMAID_MARKERS:
        assert marker not in text
    for marker in FORBIDDEN_PRODUCT_MARKERS:
        assert marker not in text


def test_radar_pipeline_documentation_skills_are_discoverable() -> None:
    for path in SKILL_PATHS:
        text = path.read_text(encoding="utf-8")
        assert text.startswith("---\nname: radar-pipeline-")
        assert "RADAR_SEARCH_PIPELINE_AS_IS.md" in text or "RADAR_SEARCH_PIPELINE_TO_BE_" in text

    to_be = SKILL_PATHS[0].read_text(encoding="utf-8")
    as_is = SKILL_PATHS[1].read_text(encoding="utf-8")
    finalize = SKILL_PATHS[2].read_text(encoding="utf-8")
    assert "Do not implement production code" in to_be
    assert "python scripts/render_radar_pipeline_doc.py" in as_is
    assert "Do not mark a TO BE behavior as AS IS unless it is implemented" in finalize
