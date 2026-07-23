from __future__ import annotations

import pytest
from pydantic import ValidationError

from power_web_os.application.radar.power_web_discovery.people_search.contracts import PeopleSearchStageArtifact
from test_power_web_people_search_pipeline import _artifact


def test_people_search_artifact_rejects_private_or_raw_fields() -> None:
    artifact, _ = _artifact()
    payload = artifact.model_dump(mode="json")
    payload["raw_html"] = "<html/>"
    with pytest.raises(ValidationError):
        PeopleSearchStageArtifact.model_validate(payload)
