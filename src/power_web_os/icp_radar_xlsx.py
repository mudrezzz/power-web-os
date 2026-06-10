from __future__ import annotations

from pathlib import Path
from typing import Any
import warnings

from openpyxl import load_workbook

from power_web_os.icp_radar import (
    CRITERION_CODES,
    ICPProfile,
    ICPRadar,
    ICPRadarArtifact,
    ICPRadarCandidate,
    SignalCriterion,
    EvidenceSource,
)

warnings.filterwarnings("ignore", category=UserWarning, message=".*extension is not supported.*")

REQUIRED_SHEETS = ("Summary", "ICP Matrix", "Criteria", "Sources")


class ICPRadarWorkbookError(ValueError):
    pass


def load_icp_radar_workbook(path: Path) -> ICPRadarArtifact:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        workbook = load_workbook(path, data_only=True, read_only=True)
        return _artifact_from_workbook(workbook, path)


def _artifact_from_workbook(workbook: Any, path: Path) -> ICPRadarArtifact:
    missing_sheets = [name for name in REQUIRED_SHEETS if name not in workbook.sheetnames]
    if missing_sheets:
        raise ICPRadarWorkbookError(f"ICP Radar workbook misses sheets: {', '.join(missing_sheets)}")

    criteria = _read_criteria(workbook["Criteria"])
    sources = _read_sources(workbook["Sources"])
    summary_overlay = _read_summary_overlay(workbook["Summary"])
    source_refs_by_url = {source.url: source.source_id for source in sources if source.url}
    radar = ICPRadar()
    candidates = []

    for row_index, row in enumerate(_value_rows(workbook["ICP Matrix"], min_row=2), start=1):
        legal_name = _text(_get(row, 2))
        if not legal_name:
            continue

        number = _text(_get(row, 1)) or str(row_index)
        criteria_scores = {
            code: _to_int(_get(row, 16 + offset))
            for offset, code in enumerate(CRITERION_CODES)
        }
        score = radar.build_score(criteria_scores)
        source_urls = tuple(_split_lines(_text(_get(row, 10))))
        evidence_refs = tuple(source_refs_by_url.get(url, url) for url in source_urls)
        overlay = summary_overlay.get(number) or summary_overlay.get(legal_name) or {}

        candidates.append(
            ICPRadarCandidate(
                rank=0,
                account_id=f"icp-sibur-{_stable_number(number):03d}",
                ppo=_text(_get(row, 1)),
                legal_name=legal_name,
                account_type=_text(_get(row, 3)),
                description=_text(_get(row, 4)),
                inn=_text(_get(row, 5)),
                revenue=_text(_get(row, 6)),
                site=_text(_get(row, 7)),
                confidence=_text(_get(row, 8)),
                signal_summary=_text(_get(row, 9)),
                main_signal=str(overlay.get("main_signal") or _text(_get(row, 9))),
                comment=str(overlay.get("comment") or ""),
                source_urls=source_urls,
                evidence_refs=evidence_refs,
                criteria_scores=criteria_scores,
                score=score,
            )
        )

    ranked_candidates = radar.rank(candidates)
    return ICPRadarArtifact(
        profile=_profile(path),
        criteria=tuple(criteria),
        sources=tuple(sources),
        candidates=ranked_candidates,
        workflow_metadata={
            "workflow_name": "ICPRadarXlsxImport",
            "artifact_version": "0.6.2",
            "source_workbook": path.name,
            "sheet_names": list(workbook.sheetnames),
            "candidate_count": len(ranked_candidates),
            "criteria_count": len(criteria),
            "source_count": len(sources),
            "scoring": "workbook-compatible deterministic formula",
        },
    )


def _profile(path: Path) -> ICPProfile:
    return ICPProfile(
        profile_id="toir-sibur",
        name="ТОиР automation ICP Radar",
        product="Автоматизация ТОиР",
        holding="СИБУР",
        run_mode="fixture_import",
        source_workbook=path.name,
        scoring_formula={
            "fit_score": "C13 + C14 + C15 + C16 + C17",
            "intent_score": "C1..C9 + C18 + C19",
            "trigger_score": "C10 + C11 + C12 + C20",
            "total_score": "sum(C1..C20)",
            "tiers": {
                "Tier 1": ">=38",
                "Tier 2": ">=25",
                "Tier 3": ">=15",
                "Monitor": "<15",
            },
        },
    )


def _read_criteria(sheet: Any) -> list[SignalCriterion]:
    criteria = []
    for row in _value_rows(sheet, min_row=2):
        code = _text(_get(row, 0))
        if not code:
            continue
        criteria.append(
            SignalCriterion(
                code=code,
                name=_text(_get(row, 1)),
                description=_text(_get(row, 2)),
                scoring_guidance=_text(_get(row, 3)),
            )
        )
    return criteria


def _read_sources(sheet: Any) -> list[EvidenceSource]:
    sources = []
    for row_index, row in enumerate(_value_rows(sheet, min_row=2), start=1):
        source_id = _text(_get(row, 0)) or f"S{row_index}"
        url = _text(_get(row, 1))
        if not url:
            continue
        sources.append(
            EvidenceSource(
                source_id=source_id,
                url=url,
                usage=_text(_get(row, 2)),
            )
        )
    return sources


def _read_summary_overlay(sheet: Any) -> dict[str, dict[str, str]]:
    overlay: dict[str, dict[str, str]] = {}
    for row in _value_rows(sheet, min_row=2):
        number = _text(_get(row, 1))
        legal_name = _text(_get(row, 2))
        data = {
            "main_signal": _text(_get(row, 6)),
            "comment": _text(_get(row, 7)),
        }
        if number:
            overlay[number] = data
        if legal_name:
            overlay[legal_name] = data
    return overlay


def _value_rows(sheet: Any, *, min_row: int) -> Any:
    return sheet.iter_rows(min_row=min_row, values_only=True)


def _get(row: tuple[Any, ...], index: int) -> Any:
    return row[index] if index < len(row) else None


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _to_int(value: Any) -> int:
    if value is None or value == "":
        return 0
    return int(float(value))


def _split_lines(value: str) -> list[str]:
    return [item.strip() for item in value.replace(";", "\n").splitlines() if item.strip()]


def _stable_number(value: str) -> int:
    try:
        return int(float(value))
    except ValueError:
        return abs(hash(value)) % 100000
