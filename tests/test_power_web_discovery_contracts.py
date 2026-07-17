from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from power_web_os.application.radar.power_web_discovery.contracts import (
    EmploymentClaim,
    IdentityHypothesis,
    PersonProfile,
    PowerWebArtifact,
    PowerWebGraphNode,
    SourceEvidence,
)
from power_web_os.board import PowerWebBoardBuilder
from power_web_os.domain import Account, Playbook, PowerWebRole
from power_web_os.planner import DeterministicAccessPlanner


def test_anonymous_profile_remains_anonymous() -> None:
    profile = PersonProfile(
        profile_id="hh-anonymous-1",
        source_id="hh_public_web",
        anonymous=True,
        role_titles=("Главный инженер",),
        evidence_refs=("evidence-1",),
    )

    assert profile.display_name is None

    with pytest.raises(ValidationError, match="must not invent"):
        PersonProfile(
            profile_id="hh-anonymous-1",
            source_id="hh_public_web",
            anonymous=True,
            display_name="Invented Person",
            evidence_refs=("evidence-1",),
        )


def test_confirmed_identity_requires_two_dimensions_and_no_hard_conflict() -> None:
    with pytest.raises(ValidationError, match="at least two"):
        IdentityHypothesis(
            hypothesis_id="hyp-1",
            left_profile_id="profile-a",
            right_profile_id="profile-b",
            state="confirmed_same",
            compatible_features=("image_fingerprint",),
            evidence_refs=("evidence-1",),
            reason="Same public image only.",
        )

    with pytest.raises(ValidationError, match="hard contradiction"):
        IdentityHypothesis(
            hypothesis_id="hyp-2",
            left_profile_id="profile-a",
            right_profile_id="profile-b",
            state="confirmed_same",
            compatible_features=("employer", "timeline"),
            hard_contradictions=("overlapping employment",),
            evidence_refs=("evidence-1", "evidence-2"),
            reason="Positive fields conflict with the timeline.",
        )

    confirmed = IdentityHypothesis(
        hypothesis_id="hyp-3",
        left_profile_id="profile-a",
        right_profile_id="profile-b",
        state="confirmed_same",
        compatible_features=("employer_timeline", "publication_author"),
        evidence_refs=("evidence-1", "evidence-2"),
        reason="Two independent public dimensions agree.",
    )
    assert confirmed.reversible is True


def test_artifact_rejects_unsafe_or_unresolved_payloads() -> None:
    evidence = SourceEvidence(
        evidence_id="evidence-1",
        source_id="official_company",
        url="https://example.com/person",
        title="Public company page",
        excerpt="Public role statement.",
        retrieved_at=datetime.now(UTC),
        capability="official_company",
    )
    with pytest.raises(ValidationError, match="unresolved evidence"):
        PowerWebArtifact(
            run_id="power-web-run-1",
            account_id="account-1",
            source_candidate_run_id="radar-run-1",
            as_of=datetime.now(UTC),
            evidence=(evidence,),
            profiles=(PersonProfile(
                profile_id="profile-1",
                source_id="official_company",
                display_name="Public Name",
                evidence_refs=("missing-evidence",),
            ),),
        )

    with pytest.raises(ValidationError):
        PowerWebArtifact.model_validate({
            "run_id": "power-web-run-1",
            "account_id": "account-1",
            "source_candidate_run_id": "radar-run-1",
            "as_of": datetime.now(UTC),
            "raw_html": "<html>not allowed</html>",
        })

    with pytest.raises(ValidationError, match="requires evidence"):
        PowerWebGraphNode(node_id="person-1", node_type="person", label="Person")

    with pytest.raises(ValidationError):
        EmploymentClaim(
            claim_id="employment-1",
            subject_ref="profile-1",
            employer="Example employer",
            title="Chief engineer",
            state="unknown",
            evidence_refs=(),
        )


def test_existing_power_web_contracts_remain_compatible() -> None:
    account = Account(
        account_id="account-1",
        name="Example account",
        icp_fit=0.8,
        roles=(PowerWebRole(
            role="Technical director",
            person_name="Alex Example",
            state="identified",
            influence=0.7,
        ),),
    )

    plan = DeterministicAccessPlanner().build_plan(
        account,
        Playbook(name="baseline", allowed_routes=("dark_stakeholder_discovery",)),
    )
    board = PowerWebBoardBuilder().build(account=account, access_plan=plan)

    assert board.account_id == account.account_id
    assert plan.account_id == account.account_id
