"""SQLAlchemy adapters for immutable Power Web handoff preparation."""

from __future__ import annotations

from collections.abc import Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from power_web_os.application.radar.candidate_discovery.execution.stored_public_surface import (
    StoredCandidatePublicSurfaceProjector,
)
from power_web_os.application.radar.power_web_discovery.contracts import (
    CandidateHandoffSource,
    PowerWebHandoffSnapshot,
    PowerWebSignalContextSnapshot,
    ProductHandoffSource,
    RadarPowerWebPolicyVersion,
    RadarProductBinding,
    SemanticRoleSnapshot,
    SignalOutcomeSnapshot,
)
from power_web_os.persistence.models import (
    PowerWebHandoffModel,
    RadarPowerWebPolicyHeadModel,
    RadarPowerWebPolicyProductBindingModel,
    RadarPowerWebPolicyVersionModel,
    RadarRunModel,
    RadarRunOutputModel,
    SignalMonitoringRunOutputModel,
    utc_now,
)
from power_web_os.persistence.sales_playbook_repositories import SqlAlchemySalesPlaybookRepository
from power_web_os.persistence.record_mappers import aware_utc


class SqlAlchemyRadarPowerWebPolicyRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_active(self, radar_id: str) -> RadarPowerWebPolicyVersion | None:
        head = self._session.get(RadarPowerWebPolicyHeadModel, radar_id)
        return self._record(head.active_policy_version_id) if head else None

    def list_versions(self, radar_id: str) -> tuple[RadarPowerWebPolicyVersion, ...]:
        rows = self._session.scalars(
            select(RadarPowerWebPolicyVersionModel)
            .where(RadarPowerWebPolicyVersionModel.radar_id == radar_id)
            .order_by(RadarPowerWebPolicyVersionModel.version_number.desc())
        ).all()
        return tuple(self._record(row.policy_version_id) for row in rows)

    def save(self, policy: RadarPowerWebPolicyVersion) -> RadarPowerWebPolicyVersion:
        if self._session.get(RadarPowerWebPolicyVersionModel, policy.policy_version_id):
            raise ValueError("power_web_policy_version_immutable")
        self._session.add(RadarPowerWebPolicyVersionModel(
            policy_version_id=policy.policy_version_id,
            radar_id=policy.radar_id,
            version_number=policy.version_number,
            payload_json=policy.model_dump(mode="json"),
            created_by=policy.created_by,
            created_at=policy.created_at,
        ))
        self._session.flush()
        for binding in policy.product_bindings:
            self._session.add(RadarPowerWebPolicyProductBindingModel(
                policy_version_id=policy.policy_version_id,
                product_id=binding.product_id,
                position=binding.position,
            ))
        # These models intentionally have no ORM relationships, so flush each
        # FK layer explicitly instead of relying on unit-of-work ordering.
        self._session.flush()
        head = self._session.get(RadarPowerWebPolicyHeadModel, policy.radar_id)
        if head is None:
            head = RadarPowerWebPolicyHeadModel(radar_id=policy.radar_id)
            self._session.add(head)
        head.active_policy_version_id = policy.policy_version_id
        head.updated_at = utc_now()
        self._session.flush()
        return self._record(policy.policy_version_id)

    def _record(self, policy_version_id: str) -> RadarPowerWebPolicyVersion:
        model = self._session.get(RadarPowerWebPolicyVersionModel, policy_version_id)
        if model is None:
            raise KeyError(policy_version_id)
        bindings = self._session.scalars(
            select(RadarPowerWebPolicyProductBindingModel)
            .where(RadarPowerWebPolicyProductBindingModel.policy_version_id == policy_version_id)
            .order_by(RadarPowerWebPolicyProductBindingModel.position)
        ).all()
        return RadarPowerWebPolicyVersion(
            policy_version_id=model.policy_version_id,
            radar_id=model.radar_id,
            version_number=model.version_number,
            product_bindings=tuple(
                RadarProductBinding(product_id=item.product_id, position=item.position) for item in bindings
            ),
            created_at=aware_utc(model.created_at),
            created_by=model.created_by,
        )


class SqlAlchemyPowerWebHandoffRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get(self, handoff_id: str) -> PowerWebHandoffSnapshot | None:
        model = self._session.get(PowerWebHandoffModel, handoff_id)
        return PowerWebHandoffSnapshot.model_validate(model.payload_json) if model else None

    def find_by_idempotency_key(self, idempotency_key: str) -> PowerWebHandoffSnapshot | None:
        model = self._session.scalars(
            select(PowerWebHandoffModel).where(PowerWebHandoffModel.idempotency_key == idempotency_key)
        ).first()
        return PowerWebHandoffSnapshot.model_validate(model.payload_json) if model else None

    def create(self, handoff: PowerWebHandoffSnapshot) -> PowerWebHandoffSnapshot:
        if self.get(handoff.handoff_id) is not None:
            raise ValueError("power_web_handoff_immutable")
        self._session.add(PowerWebHandoffModel(
            handoff_id=handoff.handoff_id,
            radar_id=handoff.radar_id,
            policy_version_id=handoff.radar_power_web_policy_version_id,
            source_candidate_run_id=handoff.source_candidate_run_id,
            source_candidate_id=handoff.source_candidate_id,
            source_signal_run_id=handoff.source_signal_run_id,
            account_id=handoff.account.account_id,
            status=handoff.status,
            idempotency_key=handoff.idempotency_key,
            request_fingerprint=handoff.request_fingerprint,
            payload_json=handoff.model_dump(mode="json"),
            created_by=handoff.created_by,
            created_at=handoff.created_at,
        ))
        self._session.flush()
        return self.get(handoff.handoff_id) or handoff

    def list_for_candidate(self, *, radar_id: str, source_candidate_run_id: str, candidate_id: str):
        rows = self._session.scalars(
            select(PowerWebHandoffModel).where(
                PowerWebHandoffModel.radar_id == radar_id,
                PowerWebHandoffModel.source_candidate_run_id == source_candidate_run_id,
                PowerWebHandoffModel.source_candidate_id == candidate_id,
            ).order_by(PowerWebHandoffModel.created_at.desc())
        ).all()
        return tuple(PowerWebHandoffSnapshot.model_validate(row.payload_json) for row in rows)


class SqlAlchemyPowerWebProductReader:
    def __init__(self, session: Session) -> None:
        self._repository = SqlAlchemySalesPlaybookRepository(session)

    def get_active_product(self, product_id: str) -> ProductHandoffSource | None:
        summary = self._repository.get_product(product_id)
        if summary is None:
            return None
        version = self._repository.get_version(product_id, summary.active_version_id) if summary.active_version_id else None
        return ProductHandoffSource(
            product_id=summary.product_id,
            lifecycle=summary.lifecycle.value,
            sales_playbook_version_id=version.version_id if version else None,
            product_definition_version_id=version.product_definition_version_id if version else None,
            buying_role_policy_version_id=version.buying_role_policy_version_id if version else None,
            product_code=summary.product_code,
            name=version.product.name if version else summary.name,
            short_description=version.product.short_description if version else "",
            roles=tuple(
                SemanticRoleSnapshot(
                    role_code=role.role_code,
                    display_name=role.display_name,
                    responsibility=role.business_responsibility,
                    required=role.required,
                    priority=role.priority.value,
                    scope=role.scope.value,
                ) for role in (version.buying_roles if version else ())
            ),
        )


class SqlAlchemyPowerWebCandidateReader:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_candidate(self, *, radar_id: str, source_candidate_run_id: str, candidate_id: str):
        run = self._session.get(RadarRunModel, source_candidate_run_id)
        output = self._session.get(RadarRunOutputModel, source_candidate_run_id)
        if run is None or output is None or run.radar_id != radar_id:
            return None
        surface = StoredCandidatePublicSurfaceProjector().project(
            artifact_payload=output.artifact_payload_json,
            candidates_payload=output.candidates_json,
        )
        row = next((item for item in surface.rows if str(item.get("candidate_id") or "") == candidate_id), None)
        if row is None:
            return None
        evidence_refs = _strings(row.get("evidence_refs"))
        upstream_refs = _strings(row.get("upstream_source_refs"))
        name = str(row.get("legal_name") or row.get("name") or candidate_id).strip()
        return CandidateHandoffSource(
            radar_id=run.radar_id,
            source_candidate_run_id=run.run_id,
            run_pipeline_id=run.pipeline_id,
            run_status=run.status,
            candidate_id=candidate_id,
            legal_name=name,
            entity_type=str(row.get("entity_type") or "legal_entity"),
            candidate_surface_status=str(row.get("candidate_surface_status") or "review_needed_candidate"),
            product_acceptance_status=str(row.get("product_acceptance_status") or "review_required"),
            inn=_optional(row.get("inn")),
            ogrn=_optional(row.get("ogrn")),
            evidence_refs=evidence_refs,
            upstream_source_refs=upstream_refs,
        )


class SqlAlchemyPowerWebSignalReader:
    def __init__(self, session: Session) -> None:
        self._session = session

    def list_candidate_contexts(self, *, radar_id: str, source_candidate_run_id: str, candidate_id: str):
        rows = self._session.execute(
            select(RadarRunModel, SignalMonitoringRunOutputModel)
            .join(SignalMonitoringRunOutputModel, SignalMonitoringRunOutputModel.run_id == RadarRunModel.run_id)
            .where(
                RadarRunModel.radar_id == radar_id,
                RadarRunModel.pipeline_id == "signal_monitoring",
                RadarRunModel.source_run_id == source_candidate_run_id,
                RadarRunModel.status == "completed",
            )
            .order_by(RadarRunModel.completed_at.desc())
        ).all()
        contexts: list[PowerWebSignalContextSnapshot] = []
        for run, output in rows:
            artifact = output.artifact_payload_json if isinstance(output.artifact_payload_json, dict) else {}
            snapshot = output.input_snapshot_json if isinstance(output.input_snapshot_json, dict) else {}
            observations = [item for item in artifact.get("observations", []) if isinstance(item, dict)]
            if not _candidate_in_scope(candidate_id, snapshot, artifact, observations):
                continue
            outcomes = tuple(
                SignalOutcomeSnapshot(
                    signal_code=str(item.get("signal_code") or item.get("criterion_id") or "unknown"),
                    outcome=str(item.get("search_status") or item.get("observation_status") or "unclear"),
                    temporal_status=_optional(item.get("temporal_status")),
                    evidence_refs=_strings(item.get("evidence_refs")),
                    reason=_optional(item.get("reason") or item.get("summary")),
                )
                for item in observations
                if str(item.get("candidate_id") or "") == candidate_id
            )
            contexts.append(PowerWebSignalContextSnapshot(
                signal_run_id=run.run_id,
                radar_id=radar_id,
                source_candidate_run_id=source_candidate_run_id,
                candidate_id=candidate_id,
                completed_at=run.completed_at or run.updated_at,
                outcomes=outcomes,
            ))
        return tuple(contexts)


def _candidate_in_scope(
    candidate_id: str,
    snapshot: dict[str, object],
    artifact: dict[str, object],
    observations: list[dict[str, object]],
) -> bool:
    collections: list[object] = [snapshot.get("candidates"), artifact.get("candidate_scope"), artifact.get("candidates")]
    for collection in collections:
        if isinstance(collection, list) and any(
            isinstance(item, dict) and str(item.get("candidate_id") or "") == candidate_id for item in collection
        ):
            return True
    return any(str(item.get("candidate_id") or "") == candidate_id for item in observations)


def _strings(value: object) -> tuple[str, ...]:
    values: Iterable[object] = value if isinstance(value, (list, tuple)) else ()
    return tuple(dict.fromkeys(str(item).strip() for item in values if str(item).strip()))


def _optional(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
