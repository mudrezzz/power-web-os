from __future__ import annotations

from datetime import date
import json
from pathlib import Path

import pytest

from power_web_os.application.radar.power_web_discovery.benchmark import (
    EmploymentControl,
    IdentityPairControl,
    PowerWebBenchmark,
    PowerWebBenchmarkFreeze,
    PowerWebBenchmarkPlanningContext,
    PowerWebBenchmarkRoleDemand,
    PowerWebBlindControls,
    ProfileControl,
    RelationshipControl,
    benchmark_sha256,
    verify_benchmark_freeze,
)


def _benchmark() -> PowerWebBenchmark:
    as_of = date(2026, 7, 17)
    profiles = tuple(
        ProfileControl(
            control_id=f"profile-control-{index}",
            profile_ref=f"blind-person-profile-{index}",
            anonymous=index == 0,
            expected_display_name=None if index == 0 else f"Hidden person {index}",
            expected_employer="Hidden employer control",
            expected_title="Hidden title control",
            source_lane="generic_web",
            expected_public_facts=("A source-backed public role is present.",),
            provenance_urls=(f"https://evidence.example/profile/{index}",),
            expected_role_demand_ids=(f"role-{index % 8}",),
            as_of=as_of,
            expected_state="retained_profile",
        )
        for index in range(10)
    )
    pairs = tuple(
        IdentityPairControl(
            control_id=f"pair-{index}",
            left_profile_ref=f"blind-person-profile-{index % 5}",
            right_profile_ref=f"blind-person-profile-{(index % 5) + 5}",
            expected_state="probable" if index < 4 else "confirmed_different",
            provenance_urls=(f"https://evidence.example/pair/{index}",),
            as_of=as_of,
        )
        for index in range(8)
    )
    employment = tuple(
        EmploymentControl(
            control_id=f"employment-{state}",
            subject_ref=f"blind-person-profile-{index}",
            employer="Hidden employer control",
            title="Hidden title control",
            expected_state=state,
            provenance_urls=(f"https://evidence.example/employment/{state}",),
            as_of=as_of,
        )
        for index, state in enumerate(("current", "former", "unknown"))
    )
    relationships = tuple(
        RelationshipControl(
            control_id=f"relationship-{index}",
            source_ref=f"blind-person-profile-{index + 3}",
            target_ref=f"role-{index}",
            relationship_type="reports_to",
            expected_state="confirmed",
            provenance_urls=(f"https://evidence.example/relationship/{index}",),
            as_of=as_of,
        )
        for index in range(3)
    )
    return PowerWebBenchmark(
        benchmark_id="user-benchmark-example",
        benchmark_version="1.0.0",
        as_of=as_of,
        status="user_accepted",
        planning_context=PowerWebBenchmarkPlanningContext(
            account_id="account-1",
            account_name="Visible planning account",
            product_context="Industrial product",
            role_policy=tuple(
                PowerWebBenchmarkRoleDemand(
                    demand_id=f"role-{index}",
                    role=f"Required role {index}",
                    required=True,
                    scope="account",
                    reason="Visible benchmark role policy.",
                )
                for index in range(8)
            ),
            allowed_source_lanes=("hh_public_web", "official_company", "generic_web"),
        ),
        blind_controls=PowerWebBlindControls(
            profiles=profiles,
            identity_pairs=pairs,
            employment=employment,
            relationships=relationships,
        ),
    )


def test_blind_controls_never_enter_planning_payload() -> None:
    benchmark = _benchmark()
    payload = benchmark.planning_payload(guided=False)

    benchmark.assert_no_blind_leakage(payload)
    encoded = json.dumps(payload, ensure_ascii=False)
    assert "blind_controls" not in payload
    assert "blind-person-profile" not in encoded
    assert "evidence.example" not in encoded

    with pytest.raises(ValueError, match="leaked"):
        benchmark.assert_no_blind_leakage({
            **payload,
            "accidental_control_ref": "blind-person-profile-0",
        })


def test_benchmark_contract_requires_all_control_classes() -> None:
    payload = _benchmark().model_dump(mode="json")
    payload["blind_controls"]["profiles"] = payload["blind_controls"]["profiles"][:9]

    with pytest.raises(ValueError):
        PowerWebBenchmark.model_validate(payload)


def test_benchmark_profile_controls_preserve_anonymity_and_referential_integrity() -> None:
    payload = _benchmark().model_dump(mode="json")
    payload["blind_controls"]["profiles"][0]["expected_display_name"] = "Invented name"
    with pytest.raises(ValueError, match="anonymous"):
        PowerWebBenchmark.model_validate(payload)

    payload = _benchmark().model_dump(mode="json")
    payload["blind_controls"]["identity_pairs"][0]["left_profile_ref"] = "missing-profile"
    with pytest.raises(ValueError, match="unknown profiles"):
        PowerWebBenchmark.model_validate(payload)


def test_named_profile_controls_are_hidden_from_blind_planning() -> None:
    benchmark = _benchmark()
    payload = benchmark.planning_payload(guided=False)

    with pytest.raises(ValueError, match="leaked"):
        benchmark.assert_no_blind_leakage({
            **payload,
            "accidental_person_name": "Hidden person 1",
        })


def test_benchmark_freeze_detects_drift(tmp_path) -> None:
    benchmark_path = tmp_path / "benchmark.user.json"
    freeze_path = tmp_path / "benchmark.freeze.json"
    benchmark = _benchmark()
    benchmark_path.write_text(benchmark.model_dump_json(indent=2), encoding="utf-8")
    freeze = PowerWebBenchmarkFreeze(
        benchmark_path=str(benchmark_path),
        benchmark_sha256=benchmark_sha256(benchmark_path),
        benchmark_id=benchmark.benchmark_id,
        benchmark_version=benchmark.benchmark_version,
        accepted_by_user=True,
        accepted_at="2026-07-17T00:00:00Z",
    )
    freeze_path.write_text(freeze.model_dump_json(indent=2), encoding="utf-8")

    verify_benchmark_freeze(benchmark_path=benchmark_path, freeze_path=freeze_path)
    changed = benchmark.model_copy(update={"benchmark_version": "1.0.1"})
    benchmark_path.write_text(changed.model_dump_json(indent=2), encoding="utf-8")

    with pytest.raises(ValueError, match="does not match|changed after freeze"):
        verify_benchmark_freeze(benchmark_path=benchmark_path, freeze_path=freeze_path)


def test_user_benchmark_is_accepted_private_contact_free_and_frozen() -> None:
    benchmark_path = Path("docs/radar/pipelines/power-web-discovery/benchmark/benchmark.user.json")
    freeze_path = benchmark_path.with_name("benchmark.freeze.json")
    source_path = benchmark_path.with_name("benchmark.source.json")

    benchmark = PowerWebBenchmark.model_validate_json(benchmark_path.read_text(encoding="utf-8"))
    verify_benchmark_freeze(benchmark_path=benchmark_path, freeze_path=freeze_path)
    source = json.loads(source_path.read_text(encoding="utf-8"))
    serialized = benchmark_path.read_text(encoding="utf-8").casefold()

    assert benchmark.status == "user_accepted"
    assert len(benchmark.blind_controls.profiles) == 10
    assert len(benchmark.blind_controls.identity_pairs) == 8
    assert {item.expected_state for item in benchmark.blind_controls.employment} == {"current", "former", "unknown"}
    assert source["private_contact_values_retained"] is False
    assert source["raw_workbook_copied_to_repository"] is False
    assert not any(field in serialized for field in ('"phone"', '"email"', '"telegram"', '"outreach_activity"'))


def test_sales_playbook_amendment_has_no_blind_leakage() -> None:
    path = Path("docs/radar/pipelines/power-web-discovery/benchmark/sales_playbook.amendment.v1.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    encoded = json.dumps(payload, ensure_ascii=False).casefold()

    assert payload["product_reference"]["product_id"] == "product-smartdiagnostics"
    assert len(payload["semantic_role_codes"]) == 8
    assert payload["blind_controls_changed"] is False
    assert payload["blind_control_values"] == []
    assert "blind-person-profile" not in encoded
    assert "provenance_url" not in encoded


def test_handoff_contract_has_no_blind_control_fields() -> None:
    from power_web_os.application.radar.power_web_discovery.contracts import PowerWebHandoffSnapshot

    schema = json.dumps(PowerWebHandoffSnapshot.model_json_schema(), ensure_ascii=False).casefold()

    assert "blind_controls" not in schema
    assert "expected_answer" not in schema
    assert "identity_pair" not in schema
    assert "provenance_urls" not in schema
