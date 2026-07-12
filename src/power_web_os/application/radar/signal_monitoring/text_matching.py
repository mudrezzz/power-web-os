"""Generic text matching helpers for signal-monitoring entity binding."""

from __future__ import annotations

from difflib import SequenceMatcher
import re


_CYRILLIC_TRANSLITERATION = str.maketrans({
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "kh",
    "ц": "ts",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
})


def compact(value: str) -> str:
    return "".join(character for character in str(value).casefold() if character.isalnum())


def compact_variants(value: str) -> set[str]:
    normalized = str(value or "").casefold()
    variants = {compact(normalized)}
    transliterated = normalized.translate(_CYRILLIC_TRANSLITERATION)
    variants.add(compact(transliterated))
    return {item for item in variants if len(item) >= 4}


def entity_match_keys(values: list[str]) -> set[str]:
    keys: set[str] = set()
    for value in values:
        keys.update(item for item in compact_variants(value) if len(item) >= 6)
    return keys


def text_matches_entity(*, values: list[str], text: str, min_ratio: float = 0.7) -> bool:
    keys = entity_match_keys(values)
    if not keys:
        return False
    searchable = " ".join(compact_variants(text))
    if any(key in searchable for key in keys):
        return True
    tokens = [
        token
        for raw in re.split(r"[/_.?=&\-\s]+", str(text or ""))
        for token in compact_variants(raw)
        if len(token) >= 6
    ]
    return any(
        SequenceMatcher(None, key, token).ratio() >= min_ratio
        for key in keys
        for token in tokens
    )
