"""Definition vocabulary defaults for legacy signal criteria."""

from __future__ import annotations


def signal_criterion_vocabulary(*, name: str, description: str = "") -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Infer legacy defaults by criterion meaning, never by criterion code."""

    text = f"{name} {description}".casefold()
    if any(value in text for value in ("toir", "reliability", "maintenance", "repair", "turnaround")):
        search = (
            "остановочный ремонт",
            "капитальный ремонт",
            "пусконаладочные работы",
            "ремонтная кампания",
            "техническое обслуживание",
            "надежность оборудования",
            "плановый ремонт",
            "техническое перевооружение",
        )
        evidence = (
            "остановочный ремонт",
            "капитальный ремонт",
            "пусконаладочные работы",
            "ремонтная кампания",
            "техническое обслуживание",
            "надежность",
            "ремонт",
        )
        return search, evidence
    if any(value in text for value in ("modernization", "capacity", "investment", "equipment")):
        search = (
            "модернизация",
            "новое производство",
            "строительство производства",
            "запуск производства",
            "инвестиции",
            "завершил строительство",
            "пусконаладочные работы",
            "реконструкция",
            "увеличение мощности",
            "АСУТП",
            "техническое перевооружение",
            "новое оборудование",
            "автоматизация",
        )
        evidence = (
            "модернизация",
            "новое производство",
            "новый завод",
            "строительство",
            "запуск производства",
            "инвестиции",
            "оборудование",
            "автоматизация",
            "реконструкция",
            "увеличение мощности",
            "АСУТП",
            "завершил строительство",
            "пусконаладочные работы",
        )
        return search, evidence
    return (), ()
