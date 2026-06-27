from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Flowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "docs" / "radar" / "RADAR_SEARCH_PIPELINE_AS_IS.md"
DEFAULT_OUTPUT = ROOT / "docs" / "radar" / "RADAR_SEARCH_PIPELINE_AS_IS.pdf"
FONT_CANDIDATES = [
    Path("C:/Windows/Fonts/arial.ttf"),
    Path("C:/Windows/Fonts/segoeui.ttf"),
    Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
]


class DiagramFlowable(Flowable):
    def __init__(self, diagram_id: str, width: float) -> None:
        super().__init__()
        self.diagram_id = diagram_id
        self.width = width
        self.height = 6.2 * cm

    def wrap(self, available_width: float, available_height: float) -> tuple[float, float]:
        self.width = available_width
        return available_width, self.height

    def draw(self) -> None:
        draw_methods = {
            "high_level_pipeline": self._draw_high_level_pipeline,
            "planner_sequence": self._draw_planner_sequence,
            "checkpoint_loop": self._draw_checkpoint_loop,
            "source_lifecycle": self._draw_source_lifecycle,
            "context_data_flow": self._draw_context_data_flow,
            "as_is_to_be_lifecycle": self._draw_as_is_to_be_lifecycle,
        }
        draw_methods.get(self.diagram_id, self._draw_unknown)()

    def _box(self, x: float, y: float, w: float, h: float, label: str, fill=colors.whitesmoke) -> None:
        self.canv.setFillColor(fill)
        self.canv.setStrokeColor(colors.HexColor("#4B5563"))
        self.canv.roundRect(x, y, w, h, 6, stroke=1, fill=1)
        self.canv.setFillColor(colors.HexColor("#111827"))
        self.canv.setFont("DocFont", 7)
        lines = _wrap_label(label, max(10, int(w / 5.2)))
        line_y = y + h - 12
        for line in lines[:3]:
            self.canv.drawCentredString(x + w / 2, line_y, line)
            line_y -= 8

    def _arrow(self, x1: float, y1: float, x2: float, y2: float) -> None:
        self.canv.setStrokeColor(colors.HexColor("#6B7280"))
        self.canv.line(x1, y1, x2, y2)
        angle = 1 if x2 >= x1 else -1
        self.canv.line(x2, y2, x2 - angle * 5, y2 + 3)
        self.canv.line(x2, y2, x2 - angle * 5, y2 - 3)

    def _title(self, title: str) -> None:
        self.canv.setFont("DocFont-Bold", 9)
        self.canv.setFillColor(colors.HexColor("#111827"))
        self.canv.drawString(0, self.height - 12, title)

    def _draw_high_level_pipeline(self) -> None:
        self._title("Rendered diagram: high-level Radar pipeline")
        labels = [
            "API run",
            "Active definition",
            "Source cards",
            "Planner",
            "Validation",
            "Discovery",
            "Extraction",
            "Entity resolution",
            "Checkpoint",
            "Signals",
            "Projection",
            "Evaluation",
        ]
        cols = 4
        box_w = self.width / cols - 10
        box_h = 30
        x0 = 0
        y0 = self.height - 58
        positions = []
        for idx, label in enumerate(labels):
            row = idx // cols
            col = idx % cols
            x = x0 + col * (box_w + 10)
            y = y0 - row * 50
            self._box(x, y, box_w, box_h, label)
            positions.append((x, y, box_w, box_h))
            if idx and col:
                px, py, pw, ph = positions[idx - 1]
                self._arrow(px + pw, py + ph / 2, x, y + box_h / 2)
        for row_end in (3, 7):
            if row_end + 1 < len(positions):
                x, y, w, h = positions[row_end]
                nx, ny, nw, nh = positions[row_end + 1]
                self._arrow(x + w / 2, y, nx + nw / 2, ny + nh)

    def _draw_planner_sequence(self) -> None:
        self._title("Rendered diagram: planner and validation sequence")
        lanes = ["Worker", "Definition", "Profiles", "Planner", "Validator", "Executor"]
        lane_w = self.width / len(lanes)
        top = self.height - 40
        for i, lane in enumerate(lanes):
            x = i * lane_w + lane_w / 2
            self.canv.setFont("DocFont-Bold", 7)
            self.canv.drawCentredString(x, top + 10, lane)
            self.canv.setStrokeColor(colors.HexColor("#D1D5DB"))
            self.canv.line(x, top, x, 20)
        steps = [
            (0, 1, "load active definition"),
            (1, 2, "compile capabilities"),
            (1, 3, "planning input + source cards"),
            (3, 4, "proposed plan"),
            (4, 3, "revision errors if needed"),
            (4, 5, "accepted plan"),
        ]
        y = top - 16
        for start, end, label in steps:
            x1 = start * lane_w + lane_w / 2
            x2 = end * lane_w + lane_w / 2
            self._arrow(x1, y, x2, y)
            self.canv.setFont("DocFont", 6.5)
            self.canv.drawCentredString((x1 + x2) / 2, y + 4, label)
            y -= 20

    def _draw_checkpoint_loop(self) -> None:
        self._title("Rendered diagram: checkpoint loop")
        box_w = self.width / 3 - 12
        items = [
            ("Checkpoint input", 0, 0),
            ("Decision", 1, 0),
            ("Continue", 2, 0),
            ("Expand search", 0, 1),
            ("Repair extraction", 1, 1),
            ("Stop or block", 2, 1),
            ("Merge results", 1, 2),
        ]
        pos = {}
        for label, col, row in items:
            x = col * (box_w + 12)
            y = self.height - 64 - row * 48
            self._box(x, y, box_w, 28, label, colors.HexColor("#EEF2FF") if label == "Decision" else colors.whitesmoke)
            pos[label] = (x, y, box_w, 28)
        self._arrow_between(pos, "Checkpoint input", "Decision")
        self._arrow_between(pos, "Decision", "Continue")
        self._arrow_between(pos, "Decision", "Expand search")
        self._arrow_between(pos, "Decision", "Repair extraction")
        self._arrow_between(pos, "Decision", "Stop or block")
        self._arrow_between(pos, "Expand search", "Merge results")
        self._arrow_between(pos, "Repair extraction", "Merge results")
        self._arrow_between(pos, "Merge results", "Checkpoint input")

    def _draw_source_lifecycle(self) -> None:
        self._title("Rendered diagram: source lifecycle")
        labels = ["retrieved", "analyzed", "parsed", "linked", "used"]
        box_w = self.width / len(labels) - 8
        y = self.height - 58
        prev = None
        for i, label in enumerate(labels):
            x = i * (box_w + 8)
            self._box(x, y, box_w, 28, label)
            if prev:
                px, py, pw, ph = prev
                self._arrow(px + pw, py + ph / 2, x, y + 14)
            prev = (x, y, box_w, 28)
        rejects = ["schema_rejected", "linking_failed", "verification_failed", "analyzed_only", "budget_limited"]
        y2 = self.height - 112
        for i, label in enumerate(rejects):
            x = i * (box_w + 8)
            self._box(x, y2, box_w, 28, label, colors.HexColor("#FEF3C7"))

    def _draw_context_data_flow(self) -> None:
        self._title("Rendered diagram: context and data-flow guard")
        left = ["Active definition", "Source policy", "Connector profiles", "Runtime budgets"]
        middle = ["Planner cards", "Task cards", "Observations", "Checkpoints"]
        right = ["Dossier", "Candidate universe", "Product candidates", "Evaluation"]
        self._column(0, left, colors.HexColor("#ECFDF5"))
        self._column(self.width / 3, middle, colors.HexColor("#EFF6FF"))
        self._column(self.width * 2 / 3, right, colors.HexColor("#F9FAFB"))
        self._arrow(self.width / 3 - 10, self.height - 90, self.width / 3 + 10, self.height - 90)
        self._arrow(self.width * 2 / 3 - 10, self.height - 90, self.width * 2 / 3 + 10, self.height - 90)
        self.canv.setFont("DocFont-Bold", 7)
        self.canv.setFillColor(colors.HexColor("#B91C1C"))
        self.canv.drawString(0, 18, "Never pass secrets, raw hidden reasoning, or raw provider dumps.")

    def _draw_as_is_to_be_lifecycle(self) -> None:
        self._title("Rendered diagram: AS IS / TO BE maintenance lifecycle")
        labels = ["AS IS", "TO BE design", "User review", "Implement", "Validate", "Finalize AS IS", "Regenerate PDF"]
        box_w = self.width / 4 - 10
        positions = []
        for idx, label in enumerate(labels):
            col = idx % 4
            row = idx // 4
            x = col * (box_w + 10)
            y = self.height - 58 - row * 52
            self._box(x, y, box_w, 30, label)
            positions.append((x, y, box_w, 30))
            if idx and col:
                px, py, pw, ph = positions[idx - 1]
                self._arrow(px + pw, py + ph / 2, x, y + 15)
        if len(positions) > 4:
            x, y, w, h = positions[3]
            nx, ny, nw, nh = positions[4]
            self._arrow(x + w / 2, y, nx + nw / 2, ny + nh)

    def _draw_unknown(self) -> None:
        self._title(f"Rendered diagram: {self.diagram_id}")

    def _arrow_between(self, pos: dict[str, tuple[float, float, float, float]], a: str, b: str) -> None:
        x, y, w, h = pos[a]
        x2, y2, w2, h2 = pos[b]
        self._arrow(x + w / 2, y + h / 2, x2 + w2 / 2, y2 + h2 / 2)

    def _column(self, x: float, labels: list[str], fill) -> None:
        box_w = self.width / 3 - 12
        y = self.height - 48
        for label in labels:
            self._box(x + 4, y, box_w, 24, label, fill)
            y -= 32


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


def _markdown_to_story(source: Path, styles: dict[str, ParagraphStyle], page_width: float) -> list:
    story: list = []
    in_mermaid = False
    diagram_pattern = re.compile(r"<!--\s*diagram:\s*([a-zA-Z0-9_-]+)\s*-->")
    for raw_line in source.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip()
        diagram_match = diagram_pattern.match(line.strip())
        if diagram_match:
            story.append(Spacer(1, 0.15 * cm))
            story.append(DiagramFlowable(diagram_match.group(1), page_width))
            story.append(Spacer(1, 0.25 * cm))
            continue
        if line.strip().startswith("```mermaid"):
            in_mermaid = True
            continue
        if in_mermaid:
            if line.strip().startswith("```"):
                in_mermaid = False
            continue
        if not line.strip():
            story.append(Spacer(1, 0.08 * cm))
            continue
        if line.startswith("# "):
            story.append(Paragraph(_escape(line[2:]), styles["Title"]))
            story.append(Spacer(1, 0.2 * cm))
        elif line.startswith("## "):
            story.append(Paragraph(_escape(line[3:]), styles["Heading2"]))
            story.append(Spacer(1, 0.08 * cm))
        elif line.startswith("### "):
            story.append(Paragraph(_escape(line[4:]), styles["Heading3"]))
        elif line.startswith("|"):
            story.append(Paragraph(_escape(line), styles["TableLine"]))
        elif line.startswith("- "):
            story.append(Paragraph("• " + _escape(line[2:]), styles["Body"]))
        elif re.match(r"^\d+\. ", line):
            story.append(Paragraph(_escape(line), styles["Body"]))
        else:
            story.append(Paragraph(_escape(line), styles["Body"]))
    return story


def _styles(font_name: str) -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "Title": ParagraphStyle(
            "DocTitle",
            parent=base["Title"],
            fontName=font_name,
            fontSize=20,
            leading=24,
            spaceAfter=8,
            alignment=TA_LEFT,
        ),
        "Heading2": ParagraphStyle(
            "DocHeading2",
            parent=base["Heading2"],
            fontName=font_name,
            fontSize=13,
            leading=16,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "Heading3": ParagraphStyle(
            "DocHeading3",
            parent=base["Heading3"],
            fontName=font_name,
            fontSize=11,
            leading=14,
            spaceBefore=6,
            spaceAfter=3,
        ),
        "Body": ParagraphStyle(
            "DocBody",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=8.5,
            leading=11.5,
            spaceAfter=2,
        ),
        "TableLine": ParagraphStyle(
            "DocTableLine",
            parent=base["Code"],
            fontName=font_name,
            fontSize=6.5,
            leading=8,
            textColor=colors.HexColor("#374151"),
        ),
    }


def render(source: Path = DEFAULT_SOURCE, output: Path = DEFAULT_OUTPUT) -> None:
    font_name = _register_fonts()
    output.parent.mkdir(parents=True, exist_ok=True)
    page_width, _ = A4
    left_margin = right_margin = 1.45 * cm
    doc = SimpleDocTemplate(
        str(output),
        pagesize=A4,
        leftMargin=left_margin,
        rightMargin=right_margin,
        topMargin=1.35 * cm,
        bottomMargin=1.35 * cm,
        title="Radar Search Pipeline AS IS",
        author="Power Web OS",
    )
    styles = _styles(font_name)
    story = _markdown_to_story(source, styles, page_width - left_margin - right_margin)
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)


def _footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("DocFont", 7)
    canvas.setFillColor(colors.HexColor("#6B7280"))
    canvas.drawString(doc.leftMargin, 0.7 * cm, "Power Web OS - Radar Search Pipeline AS IS")
    canvas.drawRightString(A4[0] - doc.rightMargin, 0.7 * cm, f"Page {doc.page}")
    canvas.restoreState()


def main(argv: Iterable[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Render the Radar search pipeline AS IS PDF.")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args(list(argv) if argv is not None else None)
    render(args.source, args.output)


if __name__ == "__main__":
    main()
