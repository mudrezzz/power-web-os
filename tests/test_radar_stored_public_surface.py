from __future__ import annotations

from power_web_os.application.radar.candidate_discovery.execution.stored_public_surface import (
    StoredCandidatePublicSurfaceProjector,
)


def test_stored_public_surface_prefers_execution_rows_and_merges_duplicates() -> None:
    surface = StoredCandidatePublicSurfaceProjector().project(
        artifact_payload={
            "run_metadata": {
                "execution_results": {
                    "user_visible_candidates": [
                        {
                            "candidate_id": "candidate-a",
                            "legal_name": "Candidate A",
                            "evidence_refs": ["source-a"],
                        },
                        {
                            "candidate_id": "candidate-a",
                            "legal_name": "Candidate A duplicate",
                            "candidate_surface_status": "accepted_product_candidate",
                            "evidence_refs": ["source-b"],
                        },
                        {"candidate_id": "candidate-b", "legal_name": "Candidate B"},
                        {"candidate_id": "", "legal_name": ""},
                        {
                            "candidate_id": "noise",
                            "legal_name": "Noise",
                            "upstream_discovery_outcome": "rejected_noise",
                        },
                    ]
                }
            },
            "candidates": [{"candidate_id": "ignored", "legal_name": "Ignored"}],
        },
        candidates_payload=[{"candidate_id": "legacy", "legal_name": "Legacy"}],
    )

    assert surface.candidate_ids == ("candidate-a", "candidate-b")
    assert surface.candidate_count == 2
    assert surface.accepted_count == 1
    assert surface.review_needed_count == 1
    assert surface.rows[0]["evidence_refs"] == ["source-a", "source-b"]
    assert surface.rows[1]["candidate_surface_status"] == "review_needed_candidate"
    assert {item["reason"] for item in surface.diagnostics} == {
        "invalid_public_candidate_identity",
        "explicitly_rejected_public_candidate",
    }


def test_stored_public_surface_falls_back_to_legacy_rows_and_dedupes_names() -> None:
    surface = StoredCandidatePublicSurfaceProjector().project(
        artifact_payload={},
        candidates_payload=[
            {"legal_name": "AO Example", "entity_type": "legal_entity"},
            {"legal_name": "AO  Example", "entity_type": "legal_entity"},
        ],
    )

    assert surface.candidate_count == 1
    assert surface.accepted_count == 0
    assert surface.review_needed_count == 1
    assert surface.candidate_ids == ("legal_entity:aoexample",)
