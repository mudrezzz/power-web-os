"""Deterministic preparation of immutable Power Web search briefs."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from uuid import uuid4

from power_web_os.application.radar.power_web_discovery.contracts import (
    AccountIdentitySnapshot,
    CandidateHandoffSource,
    PowerWebHandoffPreflight,
    PowerWebHandoffSnapshot,
    PowerWebSignalContextSnapshot,
    ProductHandoffSource,
    ProductRoleDemandSet,
    ProductSnapshot,
    RadarPowerWebPolicyVersion,
    ReviewNeededAcknowledgement,
    RoleDemand,
)
from power_web_os.application.radar.power_web_discovery.ports import (
    PowerWebCandidateReader,
    PowerWebHandoffRepository,
    PowerWebProductReader,
    PowerWebSignalReader,
    RadarPowerWebPolicyRepository,
)


class PowerWebHandoffError(ValueError):
    def __init__(self, *reasons: str) -> None:
        self.reasons = tuple(reasons)
        super().__init__("; ".join(self.reasons))


class PowerWebHandoffConflictError(RuntimeError):
    pass


class RadarPowerWebPolicyService:
    def __init__(
        self,
        *,
        policy_repository: RadarPowerWebPolicyRepository,
        product_reader: PowerWebProductReader,
    ) -> None:
        self._policies = policy_repository
        self._products = product_reader

    def update(
        self,
        *,
        radar_id: str,
        product_ids: tuple[str, ...],
        expected_policy_version_id: str | None,
        requester: str,
        now: datetime | None = None,
    ) -> RadarPowerWebPolicyVersion:
        current = self._policies.get_active(radar_id)
        actual_id = current.policy_version_id if current else None
        if expected_policy_version_id != actual_id:
            raise PowerWebHandoffConflictError("power_web_policy_version_conflict")
        for product_id in product_ids:
            product = self._products.get_active_product(product_id)
            if product is None:
                raise PowerWebHandoffError(f"product_not_found:{product_id}")
            if product.lifecycle != "active" or not product.sales_playbook_version_id:
                raise PowerWebHandoffError(f"product_not_active:{product_id}")
        policy = next_policy_version(
            radar_id=radar_id,
            product_ids=product_ids,
            created_by=requester,
            previous=current,
            now=now,
        )
        return self._policies.save(policy)


class AccountIdentitySnapshotFactory:
    def create(self, candidate: CandidateHandoffSource) -> AccountIdentitySnapshot:
        inn = _digits(candidate.inn)
        ogrn = _digits(candidate.ogrn)
        if inn:
            account_id, status, basis = f"account-inn-{inn}", "stable", "inn"
        elif ogrn:
            account_id, status, basis = f"account-ogrn-{ogrn}", "stable", "ogrn"
        else:
            digest = sha256(
                f"{candidate.source_candidate_run_id}|{candidate.candidate_id}".encode("utf-8")
            ).hexdigest()[:20]
            account_id, status, basis = f"account-provisional-{digest}", "provisional", "source_candidate"
        refs = _unique((*candidate.evidence_refs, *candidate.upstream_source_refs))
        return AccountIdentitySnapshot(
            account_id=account_id,
            identity_status=status,
            identity_basis=basis,
            legal_name=candidate.legal_name,
            entity_type=candidate.entity_type,
            inn=inn or None,
            ogrn=ogrn or None,
            evidence_refs=refs,
            source_candidate_run_id=candidate.source_candidate_run_id,
            source_candidate_id=candidate.candidate_id,
        )


class RoleDemandCompiler:
    def compile(self, product: ProductHandoffSource) -> ProductRoleDemandSet:
        if not product.sales_playbook_version_id or not product.product_definition_version_id:
            raise PowerWebHandoffError(f"product_version_missing:{product.product_id}")
        if not product.buying_role_policy_version_id:
            raise PowerWebHandoffError(f"role_policy_version_missing:{product.product_id}")
        if not product.roles:
            raise PowerWebHandoffError(f"role_policy_empty:{product.product_id}")
        if not any(role.required for role in product.roles):
            raise PowerWebHandoffError(f"required_role_missing:{product.product_id}")
        snapshot = ProductSnapshot(
            product_id=product.product_id,
            product_code=product.product_code,
            name=product.name,
            short_description=product.short_description,
            sales_playbook_version_id=product.sales_playbook_version_id,
            product_definition_version_id=product.product_definition_version_id,
            buying_role_policy_version_id=product.buying_role_policy_version_id,
        )
        demands = tuple(
            RoleDemand(
                demand_id=f"role-demand-{_stable_key(product.product_id, product.sales_playbook_version_id, role.role_code)}",
                product_id=product.product_id,
                sales_playbook_version_id=product.sales_playbook_version_id,
                buying_role_policy_version_id=product.buying_role_policy_version_id,
                semantic_role_code=role.role_code,
                display_name=role.display_name,
                responsibility=role.responsibility,
                required=role.required,
                priority=role.priority,
                scope=role.scope,
            )
            for role in product.roles
        )
        return ProductRoleDemandSet(product=snapshot, role_demands=demands)


class PowerWebSignalContextSelector:
    def select(
        self, contexts: tuple[PowerWebSignalContextSnapshot, ...]
    ) -> PowerWebSignalContextSnapshot | None:
        return max(contexts, key=lambda item: item.completed_at, default=None)


class PowerWebHandoffPreflightService:
    def __init__(
        self,
        *,
        policy_repository: RadarPowerWebPolicyRepository,
        candidate_reader: PowerWebCandidateReader,
        product_reader: PowerWebProductReader,
        signal_reader: PowerWebSignalReader,
    ) -> None:
        self._policies = policy_repository
        self._candidates = candidate_reader
        self._products = product_reader
        self._signals = signal_reader
        self._identities = AccountIdentitySnapshotFactory()
        self._compiler = RoleDemandCompiler()
        self._signal_selector = PowerWebSignalContextSelector()

    def inspect(
        self,
        *,
        radar_id: str,
        source_candidate_run_id: str,
        candidate_id: str,
        product_ids: tuple[str, ...] | None = None,
        review_acknowledged: bool = False,
        include_latest_signal_context: bool = True,
    ) -> PowerWebHandoffPreflight:
        blockers: list[str] = []
        warnings: list[str] = []
        policy = self._policies.get_active(radar_id)
        bound_ids = tuple(item.product_id for item in policy.product_bindings) if policy else ()
        selected_ids = bound_ids if product_ids is None else _unique(product_ids)
        if policy is None or not bound_ids:
            blockers.append("power_web_products_not_configured")
        if not selected_ids:
            blockers.append("product_selection_empty")
        if any(product_id not in bound_ids for product_id in selected_ids):
            blockers.append("product_not_bound_to_radar")

        candidate = self._candidates.get_candidate(
            radar_id=radar_id,
            source_candidate_run_id=source_candidate_run_id,
            candidate_id=candidate_id,
        )
        if candidate is None:
            blockers.append("candidate_not_found_or_ineligible")
        elif candidate.run_pipeline_id != "candidate_discovery" or candidate.run_status != "completed":
            blockers.append("candidate_run_not_completed")
        elif not candidate.evidence_refs and not candidate.upstream_source_refs:
            blockers.append("candidate_provenance_missing")
        elif candidate.candidate_surface_status == "review_needed_candidate" and not review_acknowledged:
            blockers.append("review_needed_acknowledgement_required")

        role_count = 0
        for product_id in selected_ids:
            product = self._products.get_active_product(product_id)
            if product is None:
                blockers.append(f"product_not_found:{product_id}")
                continue
            if product.lifecycle != "active":
                blockers.append(f"product_not_active:{product_id}")
                continue
            try:
                role_count += len(self._compiler.compile(product).role_demands)
            except PowerWebHandoffError as exc:
                blockers.extend(exc.reasons)

        identity_status = None
        if candidate is not None and (candidate.evidence_refs or candidate.upstream_source_refs):
            identity = self._identities.create(candidate)
            identity_status = identity.identity_status
            if identity.identity_status == "provisional":
                warnings.append("account_identity_provisional")

        signal = None
        if candidate is not None and include_latest_signal_context:
            signal = self._signal_selector.select(self._signals.list_candidate_contexts(
                radar_id=radar_id,
                source_candidate_run_id=source_candidate_run_id,
                candidate_id=candidate_id,
            ))
            if signal is None:
                warnings.append("linked_signal_context_missing")
            elif any("review" in outcome.outcome for outcome in signal.outcomes):
                warnings.append("signal_context_contains_review_items")

        return PowerWebHandoffPreflight(
            ready=not blockers,
            radar_id=radar_id,
            source_candidate_run_id=source_candidate_run_id,
            candidate_id=candidate_id,
            policy_version_id=policy.policy_version_id if policy else None,
            selected_product_ids=selected_ids,
            candidate_status=candidate.candidate_surface_status if candidate else None,
            account_identity_status=identity_status,
            linked_signal_run_id=signal.signal_run_id if signal else None,
            role_demand_count=role_count,
            blockers=tuple(dict.fromkeys(blockers)),
            warnings=tuple(dict.fromkeys(warnings)),
        )


class PowerWebHandoffService:
    def __init__(
        self,
        *,
        policy_repository: RadarPowerWebPolicyRepository,
        handoff_repository: PowerWebHandoffRepository,
        candidate_reader: PowerWebCandidateReader,
        product_reader: PowerWebProductReader,
        signal_reader: PowerWebSignalReader,
    ) -> None:
        self._policies = policy_repository
        self._handoffs = handoff_repository
        self._candidates = candidate_reader
        self._products = product_reader
        self._signals = signal_reader
        self._preflight = PowerWebHandoffPreflightService(
            policy_repository=policy_repository,
            candidate_reader=candidate_reader,
            product_reader=product_reader,
            signal_reader=signal_reader,
        )
        self._identities = AccountIdentitySnapshotFactory()
        self._compiler = RoleDemandCompiler()
        self._signal_selector = PowerWebSignalContextSelector()

    def create(
        self,
        *,
        radar_id: str,
        source_candidate_run_id: str,
        candidate_id: str,
        product_ids: tuple[str, ...] | None,
        include_latest_signal_context: bool,
        reviewer: str | None,
        acknowledgement_comment: str | None,
        idempotency_key: str,
        requester: str,
        now: datetime | None = None,
    ) -> PowerWebHandoffSnapshot:
        acknowledged = bool(reviewer)
        preflight = self._preflight.inspect(
            radar_id=radar_id,
            source_candidate_run_id=source_candidate_run_id,
            candidate_id=candidate_id,
            product_ids=product_ids,
            review_acknowledged=acknowledged,
            include_latest_signal_context=include_latest_signal_context,
        )
        if not preflight.ready:
            raise PowerWebHandoffError(*preflight.blockers)
        policy = self._policies.get_active(radar_id)
        candidate = self._candidates.get_candidate(
            radar_id=radar_id,
            source_candidate_run_id=source_candidate_run_id,
            candidate_id=candidate_id,
        )
        if policy is None or candidate is None:
            raise PowerWebHandoffError("handoff_inputs_changed")
        selected_ids = preflight.selected_product_ids
        product_sets = tuple(self._compiler.compile(self._required_product(product_id)) for product_id in selected_ids)
        timestamp = now or datetime.now(UTC)
        signal = None
        if include_latest_signal_context:
            signal = self._signal_selector.select(self._signals.list_candidate_contexts(
                radar_id=radar_id,
                source_candidate_run_id=source_candidate_run_id,
                candidate_id=candidate_id,
            ))
        fingerprint = _stable_key(
            radar_id,
            policy.policy_version_id,
            source_candidate_run_id,
            candidate_id,
            *selected_ids,
            signal.signal_run_id if signal else "no-signal",
        )
        existing = self._handoffs.find_by_idempotency_key(idempotency_key)
        if existing is not None:
            if existing.request_fingerprint != fingerprint:
                raise PowerWebHandoffConflictError("idempotency_key_payload_mismatch")
            return existing
        acknowledgement = None
        if candidate.candidate_surface_status == "review_needed_candidate":
            acknowledgement = ReviewNeededAcknowledgement(
                reviewer=reviewer or "",
                comment=acknowledgement_comment,
                acknowledged_at=timestamp,
            )
        handoff = PowerWebHandoffSnapshot(
            handoff_id=f"power-web-handoff-{uuid4()}",
            radar_id=radar_id,
            radar_power_web_policy_version_id=policy.policy_version_id,
            source_candidate_run_id=source_candidate_run_id,
            source_candidate_id=candidate_id,
            source_signal_run_id=signal.signal_run_id if signal else None,
            account=self._identities.create(candidate),
            product_role_demand_sets=product_sets,
            signal_context=signal,
            review_needed_acknowledgement=acknowledgement,
            as_of=timestamp,
            created_at=timestamp,
            created_by=requester,
            idempotency_key=idempotency_key,
            request_fingerprint=fingerprint,
        )
        return self._handoffs.create(handoff)

    def _required_product(self, product_id: str) -> ProductHandoffSource:
        product = self._products.get_active_product(product_id)
        if product is None:
            raise PowerWebHandoffError(f"product_not_found:{product_id}")
        return product


def next_policy_version(
    *,
    radar_id: str,
    product_ids: tuple[str, ...],
    created_by: str,
    previous: RadarPowerWebPolicyVersion | None,
    now: datetime | None = None,
) -> RadarPowerWebPolicyVersion:
    unique_ids = _unique(product_ids)
    if len(unique_ids) != len(product_ids):
        raise PowerWebHandoffError("duplicate_product_binding")
    from power_web_os.application.radar.power_web_discovery.contracts import RadarProductBinding

    return RadarPowerWebPolicyVersion(
        policy_version_id=f"radar-power-web-policy-{uuid4()}",
        radar_id=radar_id,
        version_number=(previous.version_number + 1) if previous else 1,
        product_bindings=tuple(
            RadarProductBinding(product_id=product_id, position=index)
            for index, product_id in enumerate(product_ids)
        ),
        created_at=now or datetime.now(UTC),
        created_by=created_by,
    )


def _digits(value: str | None) -> str:
    return "".join(character for character in str(value or "") if character.isdigit())


def _unique(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _stable_key(*parts: str) -> str:
    return sha256("|".join(parts).encode("utf-8")).hexdigest()[:24]
