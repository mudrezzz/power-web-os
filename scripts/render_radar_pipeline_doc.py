from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    Flowable,
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "docs" / "radar" / "RADAR_SEARCH_PIPELINE_AS_IS.md"
DEFAULT_OUTPUT = ROOT / "docs" / "radar" / "RADAR_SEARCH_PIPELINE_AS_IS.pdf"

DIAGRAM_SECTION_TITLES = {
    "4. High-Level Pipeline",
    "7. Planning Loop",
    "11. Search Expansion Loop",
    "16. Source Lifecycle",
    "19. Context Management",
    "22. AS IS / TO BE Maintenance Lifecycle",
}

FONT_CANDIDATES = [
    Path("C:/Windows/Fonts/segoeui.ttf"),
    Path("C:/Windows/Fonts/arial.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
]

ACCENT = colors.HexColor("#2563EB")
INK = colors.HexColor("#111827")
MUTED = colors.HexColor("#6B7280")
BORDER = colors.HexColor("#CBD5E1")
SOFT_BLUE = colors.HexColor("#EFF6FF")
SOFT_GREEN = colors.HexColor("#ECFDF5")
SOFT_AMBER = colors.HexColor("#FEF3C7")
SOFT_RED = colors.HexColor("#FEE2E2")
SOFT_GRAY = colors.HexColor("#F8FAFC")


@dataclass(frozen=True)
class DiagramSpec:
    caption: str
    kind: str


DIAGRAMS = {
    "high_level_pipeline": DiagramSpec("Figure 1. End-to-end Radar execution flow", "timeline"),
    "planner_sequence": DiagramSpec("Figure 2. Planner, source cards, and backend validation", "swimlane"),
    "checkpoint_loop": DiagramSpec("Figure 3. Checkpoint decision and recovery loop", "checkpoint"),
    "source_lifecycle": DiagramSpec("Figure 4. Source lifecycle and rejection branches", "source_lifecycle"),
    "context_data_flow": DiagramSpec("Figure 5. Context boundaries across pipeline roles", "context"),
    "as_is_to_be_lifecycle": DiagramSpec("Figure 6. AS IS / TO BE maintenance cycle", "lifecycle"),
    "to_be_strategy_pipeline": DiagramSpec("Figure 1. Source-profile-driven recall expansion flow", "strategy_pipeline"),
    "to_be_expansion_target_queue": DiagramSpec("Figure 2. Expansion target queue flow", "target_queue"),
}


class RadarDiagram(Flowable):
    """Small controlled diagrams for the AS IS PDF.

    The source Markdown keeps Mermaid blocks for GitHub readability. The PDF
    intentionally uses these explicit reportlab diagrams so PDF output remains
    stable without Mermaid/Chromium/Graphviz dependencies.
    """

    def __init__(self, diagram_id: str, width: float) -> None:
        super().__init__()
        self.diagram_id = diagram_id
        self.width = width
        self.height = 7.0 * cm

    def wrap(self, available_width: float, available_height: float) -> tuple[float, float]:
        self.width = available_width
        if self.diagram_id in {"high_level_pipeline", "planner_sequence", "checkpoint_loop", "to_be_strategy_pipeline"}:
            self.height = 11.6 * cm
        elif self.diagram_id in {"as_is_to_be_lifecycle", "to_be_expansion_target_queue"}:
            self.height = 10.2 * cm
        elif self.diagram_id == "context_data_flow":
            self.height = 7.2 * cm
        else:
            self.height = 7.2 * cm
        return available_width, self.height

    def draw(self) -> None:
        spec = DIAGRAMS.get(self.diagram_id, DiagramSpec(f"Figure. {self.diagram_id}", "unknown"))
        self._caption(spec.caption)
        {
            "timeline": self._draw_timeline,
            "swimlane": self._draw_swimlane,
            "checkpoint": self._draw_checkpoint,
            "source_lifecycle": self._draw_source_lifecycle,
            "context": self._draw_context,
            "lifecycle": self._draw_as_is_lifecycle,
            "strategy_pipeline": self._draw_strategy_pipeline,
            "target_queue": self._draw_target_queue,
        }.get(spec.kind, self._draw_unknown)()

    def _caption(self, text: str) -> None:
        self.canv.setFillColor(INK)
        self.canv.setFont("DocFont-Bold", 10)
        self.canv.drawString(0, self.height - 12, text)

    def _box(self, x: float, y: float, w: float, h: float, title: str, body: str = "", fill=SOFT_GRAY) -> None:
        self.canv.setFillColor(fill)
        self.canv.setStrokeColor(BORDER)
        self.canv.roundRect(x, y, w, h, 5, stroke=1, fill=1)
        self.canv.setFillColor(INK)
        self.canv.setFont("DocFont-Bold", 7.2)
        self.canv.drawString(x + 6, y + h - 12, title)
        if body:
            self.canv.setFont("DocFont", 6.4)
            yy = y + h - 22
            for line in _wrap_label(body, max(14, int(w / 4.4)))[:3]:
                self.canv.drawString(x + 6, yy, line)
                yy -= 8

    def _arrow(self, x1: float, y1: float, x2: float, y2: float, label: str = "") -> None:
        self.canv.setStrokeColor(MUTED)
        self.canv.setLineWidth(1.0)
        self.canv.line(x1, y1, x2, y2)
        dx = 1 if x2 >= x1 else -1
        self.canv.line(x2, y2, x2 - dx * 5, y2 + 3)
        self.canv.line(x2, y2, x2 - dx * 5, y2 - 3)
        if label:
            self.canv.setFillColor(MUTED)
            self.canv.setFont("DocFont", 6.2)
            self.canv.drawCentredString((x1 + x2) / 2, y1 + 4, label)

    def _draw_timeline(self) -> None:
        steps = [
            ("1. Start run", "API creates a queued durable Radar run.", SOFT_BLUE),
            ("2. Prepare runtime", "Worker loads active definition and compiles source cards.", SOFT_GREEN),
            ("3. Plan and validate", "Planner suggests; backend validates capabilities and obligations.", SOFT_AMBER),
            ("4. Discover and resolve", "Retrieval, registry enrichment, extraction repair, entity resolution.", SOFT_BLUE),
            ("5. Review checkpoint", "Continue, expand, repair, revise, stop, or block.", SOFT_AMBER),
            ("6. Signal search", "Runs only after pre-signal checkpoint allows it.", SOFT_GREEN),
            ("7. Project and evaluate", "Dossier, source lifecycle, candidate projection, benchmark metrics.", SOFT_GRAY),
        ]
        box_w = self.width
        box_h = 34
        top_y = self.height - 72
        last_y = None
        for idx, (title, body, fill) in enumerate(steps):
            y = top_y - idx * 43
            self._box(0, y, box_w, box_h, title, body, fill)
            if last_y is not None:
                self._arrow(self.width / 2, last_y, self.width / 2, y + box_h)
            last_y = y

    def _draw_swimlane(self) -> None:
        steps = [
            ("Worker", "loads queued run id and active Radar definition", SOFT_BLUE),
            ("Definition adapter", "builds canonical runtime payload", SOFT_GREEN),
            ("Connector registry", "compiles connector profiles into source cards", SOFT_GREEN),
            ("Planner", "proposes structured execution plan", SOFT_BLUE),
            ("Backend validator", "rejects incompatible source use and policy violations", SOFT_AMBER),
            ("Executor", "runs only accepted bounded tasks", SOFT_GRAY),
        ]
        y = self.height - 72
        w = self.width
        h = 34
        for idx, (role, note, fill) in enumerate(steps):
            self._box(0, y, w, h, f"{idx + 1}. {role}", note, fill)
            if idx:
                self._arrow(self.width / 2, y + h + 4, self.width / 2, y + h)
            y -= 43
        self._box(0, 8, self.width, 22, "Guardrail", "Planner suggests. Backend validates. Execution never trusts source ids blindly.", SOFT_AMBER)

    def _draw_checkpoint(self) -> None:
        y0 = self.height - 64
        self._box(0, y0, self.width, 40, "Checkpoint input", "candidate universe, source counts, obligations, extraction/linking issues, budget state", SOFT_BLUE)
        self._arrow(self.width / 2, y0, self.width / 2, y0 - 12)
        self._box(0, y0 - 54, self.width, 40, "Backend decision", "continue, recover, stop for review, or fail hard", SOFT_AMBER)

        self.canv.setFont("DocFont-Bold", 7.4)
        self.canv.setFillColor(INK)
        self.canv.drawString(0, y0 - 76, "Recovery actions are mutually exclusive and bounded:")
        actions = [
            ("Retry same source", "same bounded task"),
            ("Expand search", "allowed official/open web"),
            ("Repair extraction", "deterministic repair or bounded retry"),
            ("Revise plan", "only plan/policy strategy failure"),
            ("Continue", "next stage or signal search"),
            ("Stop / block", "explicit diagnostic terminal state"),
        ]
        start_y = y0 - 128
        box_w = (self.width - 12) / 2
        for idx, (title, body) in enumerate(actions):
            col = idx % 2
            row = idx // 2
            x = col * (box_w + 12)
            y = start_y - row * 43
            fill = SOFT_GREEN if title == "Continue" else SOFT_RED if "Stop" in title else SOFT_GRAY
            self._box(x, y, box_w, 35, title, body, fill)
        self._box(0, 4, self.width, 28, "Loop rule", "Recovery is budgeted, policy-checked, merged, and re-reviewed. No blind continuation.", SOFT_GREEN)

    def _draw_source_lifecycle(self) -> None:
        main = ["retrieved", "analyzed", "parsed", "linked", "used"]
        gap = 10
        box_w = (self.width - gap * (len(main) - 1)) / len(main)
        y = self.height - 72
        prev = None
        for label in main:
            x = 0 if prev is None else prev[0] + box_w + gap
            self._box(x, y, box_w, 34, label, "", SOFT_GREEN if label == "used" else SOFT_BLUE)
            if prev:
                self._arrow(prev[0] + box_w, y + 17, x, y + 17)
            prev = (x, y)
        branches = [
            ("schema_rejected", "invalid extraction shape"),
            ("linking_failed", "evidence refs unresolved"),
            ("verification_failed", "URL/source verification risk"),
            ("analyzed_only", "inspected but not used"),
            ("budget_limited", "not executed or capped"),
        ]
        y2 = y - 74
        for idx, (title, body) in enumerate(branches):
            x = idx * (box_w + gap)
            self._box(x, y2, box_w, 42, title, body, SOFT_AMBER)
        self.canv.setFont("DocFont-Bold", 7)
        self.canv.setFillColor(MUTED)
        self.canv.drawString(0, 20, "Product source list includes only 'used'. Dossier lifecycle keeps all diagnostic states.")

    def _draw_context(self) -> None:
        headers = [("Inputs", SOFT_GREEN), ("Application decisions", SOFT_BLUE), ("Outputs", SOFT_GRAY)]
        col_w = self.width
        x_positions = [0, 0, 0]
        rows = [
            ["Active definition", "Planner cards", "Dossier"],
            ["Source policy", "Task cards", "Candidate universe"],
            ["Connector profiles", "Observations", "Product candidates"],
            ["Runtime budgets", "Checkpoints", "Evaluation"],
        ]
        top = self.height - 58
        y = top
        for col, (header, fill) in enumerate(headers):
            values = ", ".join(row[col] for row in rows)
            self._box(0, y, col_w, 36, header, values, fill)
            if col < len(headers) - 1:
                self._arrow(self.width / 2, y, self.width / 2, y - 9)
            y -= 48
        self._box(0, 10, self.width, 24, "Forbidden context", "Never pass secrets, raw hidden reasoning, headers, tokens, or raw provider dumps.", SOFT_RED)

    def _draw_as_is_lifecycle(self) -> None:
        steps = [
            ("1 AS IS", "current implementation"),
            ("2 TO BE", "planned pipeline change"),
            ("3 Review", "user and developer alignment"),
            ("4 Implement", "slice code and tests"),
            ("5 Validate", "fixtures, smoke, evaluation"),
            ("6 Finalize", "update AS IS and PDF"),
        ]
        y = self.height - 62
        box_w = self.width
        box_h = 32
        for title, body in steps:
            self._box(0, y, box_w, box_h, title, body, SOFT_BLUE if title != "6 Finalize" else SOFT_GREEN)
            if title != steps[-1][0]:
                self._arrow(self.width / 2, y, self.width / 2, y - 7)
            y -= 42
        self._box(0, 8, self.width, 24, "Rule", "A substantial Radar pipeline slice is Done only after implemented behavior is reflected in AS IS Markdown/PDF.", SOFT_AMBER)

    def _draw_strategy_pipeline(self) -> None:
        steps = [
            ("1. Compile profiles", "selected sources -> capability cards", SOFT_GREEN),
            ("2. Enrich source cards", "best-for, not-for, inputs, facts, obligations", SOFT_BLUE),
            ("3. Plan and validate", "planner suggests; backend rejects incompatible use", SOFT_AMBER),
            ("4. Build target queue", "holding, subsidiaries, sites, aliases, source-backed gaps", SOFT_BLUE),
            ("5. Reserve budgets", "registry, recall expansion, official/open-web probes, signals", SOFT_AMBER),
            ("6. Execute by priority", "provider-neutral actions under capability and reserve guards", SOFT_GREEN),
            ("7. Explain outcome", "dossier/report show targets, skipped reasons, reserve spend", SOFT_GRAY),
        ]
        box_w = self.width
        box_h = 34
        top_y = self.height - 72
        previous_y = None
        for idx, (title, body, fill) in enumerate(steps):
            y = top_y - idx * 43
            self._box(0, y, box_w, box_h, title, body, fill)
            if previous_y is not None:
                self._arrow(self.width / 2, previous_y, self.width / 2, y + box_h)
            previous_y = y

    def _draw_target_queue(self) -> None:
        self._box(0, self.height - 56, self.width, 31, "Checkpoint says recall is weak", "source-backed gaps, coverage risk, budget snapshot", SOFT_AMBER)
        self._arrow(self.width / 2, self.height - 56, self.width / 2, self.height - 69)
        self._box(0, self.height - 99, self.width, 31, "Collect candidate targets", "retrieved names, unresolved gaps, aliases, benchmark-only misses", SOFT_BLUE)
        self._arrow(self.width / 2, self.height - 99, self.width / 2, self.height - 113)

        targets = [
            ("1. Holding/group", "highest priority"),
            ("2. Subsidiary/legal entity", "source-backed or expected"),
            ("3. Site/branch/asset", "review-needed upstream"),
            ("4. Alias/language variant", "Russian/legal-form/English"),
            ("5. Registry suggestion", "capped lower-priority fan-out"),
        ]
        box_w = (self.width - 12) / 2
        target_h = 28
        start_y = self.height - 137
        for idx, (title, body) in enumerate(targets):
            col = idx % 2
            row = idx // 2
            x = col * (box_w + 12)
            y = start_y - row * 32
            self._box(x, y, box_w, target_h, title, body, SOFT_GRAY)
        self._box(0, 5, self.width, 22, "Execution rule", "Run targets by priority and reserve availability. Persist not-searched reasons for every skipped target.", SOFT_GREEN)

    def _draw_unknown(self) -> None:
        self._box(0, self.height - 70, self.width, 40, "Unknown diagram", self.diagram_id, SOFT_RED)


def _wrap_label(text: str, width: int) -> list[str]:
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        proposed = f"{current} {word}".strip()
        if len(proposed) > width and current:
            lines.append(current)
            current = word
        else:
            current = proposed
    if current:
        lines.append(current)
    return lines or [text]


def _register_fonts() -> str:
    for candidate in FONT_CANDIDATES:
        if candidate.exists():
            pdfmetrics.registerFont(TTFont("DocFont", str(candidate)))
            pdfmetrics.registerFont(TTFont("DocFont-Bold", str(candidate)))
            return "DocFont"
    return "Helvetica"


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace("`", "")
    )


def _inline_code(text: str) -> str:
    return re.sub(r"`([^`]+)`", r"<font name='DocFont-Bold'>\1</font>", _escape(text))


def _is_table_line(line: str) -> bool:
    return line.strip().startswith("|") and line.strip().endswith("|")


def _is_separator_line(line: str) -> bool:
    stripped = line.strip().strip("|")
    return bool(stripped) and all(set(cell.strip()) <= {"-", ":"} for cell in stripped.split("|"))


def _split_table_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def _table_flowables(rows: list[list[str]], styles: dict[str, ParagraphStyle], available_width: float) -> list:
    if not rows:
        return []
    columns = len(rows[0])
    if columns > 2:
        return _card_flowables_for_wide_table(rows, styles, available_width)
    if columns == 2:
        widths = [available_width * 0.24, available_width * 0.76]
    else:
        widths = [available_width / columns for _ in range(columns)]
    data = []
    for row_index, row in enumerate(rows):
        style = styles["TableHeader"] if row_index == 0 else styles["TableCell"]
        padded = [*row, *[""] * (columns - len(row))]
        data.append([Paragraph(_inline_code(cell), style) for cell in padded[:columns]])
    table = Table(data, colWidths=widths, repeatRows=1, splitByRow=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E5E7EB")),
                ("TEXTCOLOR", (0, 0), (-1, 0), INK),
                ("GRID", (0, 0), (-1, -1), 0.35, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ]
        )
    )
    return [table]


def _card_flowables_for_wide_table(rows: list[list[str]], styles: dict[str, ParagraphStyle], available_width: float) -> list:
    headers = rows[0]
    cards: list = []
    field_width = available_width * 0.24
    value_width = available_width * 0.76
    for row in rows[1:]:
        padded = [*row, *[""] * (len(headers) - len(row))]
        title = padded[0]
        body_rows = [
            [
                Paragraph(_inline_code(header), styles["TableHeader"]),
                Paragraph(_inline_code(value), styles["TableCell"]),
            ]
            for header, value in zip(headers[1:], padded[1:], strict=False)
            if value.strip()
        ]
        card_title = Paragraph(_inline_code(title), styles["CardTitle"])
        table = Table(body_rows, colWidths=[field_width, value_width], splitByRow=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#F1F5F9")),
                    ("GRID", (0, 0), (-1, -1), 0.3, BORDER),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                    ("TOPPADDING", (0, 0), (-1, -1), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ]
            )
        )
        cards.append(KeepTogether([card_title, table, Spacer(1, 0.12 * cm)]))
    return cards


def _styles(font_name: str) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle("Title", parent=base["Title"], fontName=font_name, fontSize=22, leading=26, alignment=TA_LEFT, textColor=INK),
        "Subtitle": ParagraphStyle("Subtitle", parent=base["BodyText"], fontName=font_name, fontSize=9.5, leading=12, textColor=MUTED),
        "Heading2": ParagraphStyle("Heading2", parent=base["Heading2"], fontName=font_name, fontSize=15, leading=18, spaceBefore=10, spaceAfter=5, textColor=INK),
        "Heading3": ParagraphStyle("Heading3", parent=base["Heading3"], fontName=font_name, fontSize=11.5, leading=14, spaceBefore=8, spaceAfter=3, textColor=INK),
        "Body": ParagraphStyle("Body", parent=base["BodyText"], fontName=font_name, fontSize=8.8, leading=12, spaceAfter=3, textColor=colors.HexColor("#1F2937")),
        "Bullet": ParagraphStyle("Bullet", parent=base["BodyText"], fontName=font_name, fontSize=8.5, leading=11.5, leftIndent=10, firstLineIndent=-7, spaceAfter=2),
        "TableHeader": ParagraphStyle("TableHeader", parent=base["BodyText"], fontName=font_name, fontSize=7.2, leading=9.2, textColor=INK),
        "TableCell": ParagraphStyle("TableCell", parent=base["BodyText"], fontName=font_name, fontSize=6.7, leading=8.5, textColor=colors.HexColor("#1F2937")),
        "CardTitle": ParagraphStyle("CardTitle", parent=base["BodyText"], fontName=font_name, fontSize=8.2, leading=10, textColor=INK, spaceBefore=4, spaceAfter=2),
    }


def _document_subtitle(title: str) -> str:
    if "TO BE" in title:
        return "Review design for a planned Radar search pipeline change"
    return "Current implementation guide for Radar candidate and signal search"


def _markdown_to_story(source: Path, styles: dict[str, ParagraphStyle], page_width: float) -> tuple[list, str]:
    story: list = []
    lines = source.read_text(encoding="utf-8").splitlines()
    in_mermaid = False
    pending_diagram: str | None = None
    table_rows: list[list[str]] = []
    document_title = "Radar Search Pipeline"
    diagram_pattern = re.compile(r"<!--\s*diagram:\s*([a-zA-Z0-9_-]+)\s*-->")

    def flush_table() -> None:
        nonlocal table_rows
        if table_rows:
            story.append(Spacer(1, 0.08 * cm))
            story.extend(_table_flowables(table_rows, styles, page_width))
            story.append(Spacer(1, 0.16 * cm))
            table_rows = []

    for raw_line in lines:
        line = raw_line.rstrip()
        diagram_match = diagram_pattern.match(line.strip())
        if diagram_match:
            flush_table()
            pending_diagram = diagram_match.group(1)
            continue
        if line.strip().startswith("```mermaid"):
            in_mermaid = True
            continue
        if in_mermaid:
            if line.strip().startswith("```"):
                in_mermaid = False
                if pending_diagram:
                    story.append(Spacer(1, 0.12 * cm))
                    story.append(RadarDiagram(pending_diagram, page_width))
                    story.append(Spacer(1, 0.18 * cm))
                    pending_diagram = None
            continue
        if _is_table_line(line):
            if _is_separator_line(line):
                continue
            table_rows.append(_split_table_row(line))
            continue
        flush_table()
        if not line.strip():
            story.append(Spacer(1, 0.05 * cm))
            continue
        if line.startswith("# "):
            document_title = line[2:].strip()
            story.append(Paragraph(_inline_code(document_title), styles["Title"]))
            story.append(Paragraph(_document_subtitle(document_title), styles["Subtitle"]))
            story.append(HRFlowable(width="100%", thickness=0.7, color=BORDER, spaceBefore=5, spaceAfter=8))
        elif line.startswith("## "):
            title = line[3:]
            if title in DIAGRAM_SECTION_TITLES and story:
                story.append(PageBreak())
            story.append(KeepTogether([Paragraph(_inline_code(title), styles["Heading2"]), HRFlowable(width="100%", thickness=0.4, color=colors.HexColor("#E5E7EB"), spaceAfter=3)]))
        elif line.startswith("### "):
            story.append(Paragraph(_inline_code(line[4:]), styles["Heading3"]))
        elif line.startswith("- "):
            story.append(Paragraph("• " + _inline_code(line[2:]), styles["Bullet"]))
        elif re.match(r"^\d+\. ", line):
            story.append(Paragraph(_inline_code(line), styles["Bullet"]))
        else:
            story.append(Paragraph(_inline_code(line), styles["Body"]))
    flush_table()
    return story, document_title


def _footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("DocFont", 7)
    canvas.setFillColor(MUTED)
    footer_title = getattr(doc, "radar_footer_title", "Radar Search Pipeline")
    canvas.drawString(doc.leftMargin, 0.65 * cm, f"Power Web OS - {footer_title}")
    canvas.drawRightString(A4[0] - doc.rightMargin, 0.65 * cm, f"Page {doc.page}")
    canvas.restoreState()


def render(source: Path = DEFAULT_SOURCE, output: Path = DEFAULT_OUTPUT) -> None:
    font_name = _register_fonts()
    output.parent.mkdir(parents=True, exist_ok=True)
    page_width, _ = A4
    left_margin = right_margin = 1.3 * cm
    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=1.15 * cm,
        bottomMargin=1.05 * cm,
        title=source.stem,
        author="Power Web OS",
    )
    styles = _styles(font_name)
    story, document_title = _markdown_to_story(source, styles, page_width - left_margin - right_margin)
    doc.radar_footer_title = document_title
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Render the Radar search pipeline AS IS PDF.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(list(argv) if argv is not None else None)
    render(args.source, args.output)


if __name__ == "__main__":
    main()
