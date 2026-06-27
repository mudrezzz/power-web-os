"""Recorded DaData fixtures for offline company-registry tests."""

from __future__ import annotations

from typing import Any


def default_recorded_fixtures() -> list[dict[str, Any]]:
    return [
        {
            "source_ref": "dadata_1651025328",
            "legal_name": "ПАО «Нижнекамскнефтехим»",
            "inn": "1651025328",
            "ogrn": "1021602502316",
            "status": "ACTIVE",
            "address": "Республика Татарстан, Нижнекамск",
            "okved": "20.17",
            "registry_url": "https://dadata.ru/suggestions/",
        },
        {
            "source_ref": "dadata_2465014500",
            "legal_name": "АО «Красноярский завод синтетического каучука»",
            "inn": "2465014500",
            "status": "ACTIVE",
            "address": "Красноярский край, Красноярск",
            "okved": "20.17",
            "registry_url": "https://dadata.ru/suggestions/",
        },
    ]
