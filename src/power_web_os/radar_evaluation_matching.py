"""Name and entity-type matching helpers for offline Radar evaluation."""

from __future__ import annotations

import re


def normalize_name(value: str) -> str:
    cyrillic_range = "\u0430-\u044f"
    legal_forms = "|".join((
        "\u043e\u043e\u043e",
        "\u0430\u043e",
        "\u043f\u0430\u043e",
        "\u0437\u0430\u043e",
        "\u043e\u0430\u043e",
        "\u043d\u043a\u043e",
        "llc",
        "jsc",
        "pjsc",
        "ltd",
        "public joint stock company",
        "joint stock company",
    ))
    value = value.lower().replace("\u0451", "\u0435")
    value = re.sub(r"[\"'\u00ab\u00bb\u201c\u201d()]", " ", value)
    value = re.sub(rf"\b({legal_forms})\b", " ", value)
    value = re.sub(rf"[^a-z{cyrillic_range}0-9]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def contains_strong_name(observed_name: str, baseline_name: str) -> bool:
    if len(baseline_name) >= 5 and f" {baseline_name} " in f" {observed_name} ":
        return True
    if len(observed_name) < 6 or len(baseline_name) < 6:
        return False
    return observed_name in baseline_name or baseline_name in observed_name


def entity_type_compatible(*, baseline_entity_type: str, observed_entity_type: str) -> bool:
    if baseline_entity_type == "legal_entity":
        return True
    return observed_entity_type in {"branch", "production_site", "asset", "project"}


def review_entity_name_match(*, baseline_names: set[str], observed_name: str) -> bool:
    observed_tokens = _meaningful_review_tokens(observed_name)
    if not observed_tokens:
        return False
    for name in baseline_names:
        baseline_tokens = _meaningful_review_tokens(name)
        if len(baseline_tokens) >= 2 and baseline_tokens.issubset(observed_tokens):
            return True
        if len(baseline_tokens & observed_tokens) >= 3:
            return True
    return False


def match_rank(match_type: str, confidence: str) -> int:
    type_rank = {"inn": 40, "ogrn": 40, "normalized_name": 30, "source_backed_partial": 20}
    confidence_rank = {"high": 3, "medium": 2, "ambiguous": 1}
    return type_rank.get(match_type, 0) + confidence_rank.get(confidence, 0)


def _meaningful_review_tokens(value: str) -> set[str]:
    stop_words = {
        "\u0441\u0438\u0431\u0443\u0440",
        "sibur",
        "\u043a\u043e\u043c\u043f\u0430\u043d\u0438\u044f",
        "\u043a\u043e\u043c\u043f\u0430\u043d\u0438\u0438",
        "\u0434\u0438\u0440\u0435\u043a\u0446\u0438\u044f",
        "\u043f\u0440\u043e\u0438\u0437\u0432\u043e\u0434\u0441\u0442\u0432\u0435\u043d\u043d\u0430\u044f",
        "\u043f\u0440\u043e\u043c\u044b\u0448\u043b\u0435\u043d\u043d\u0430\u044f",
    }
    return {token for token in value.split() if len(token) >= 4 and token not in stop_words}
