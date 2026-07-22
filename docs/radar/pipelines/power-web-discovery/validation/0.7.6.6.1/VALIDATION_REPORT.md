# Power Web handoff validation

Slice: `0.7.6.6.1`
Validation status: **PASS**

## Runtime evidence

- Radar: `benchmark-sibur-holding-contour`.
- Candidate run: `radar-run-fixture-power-web-handoff`.
- Signal context: `signal-run-fixture-power-web-handoff`.
- Policy: `radar-power-web-policy-1e75592f-1a98-4a8a-916d-4e70aaed8ebc`; products: `2`.
- All-products roles: `14`; subset roles: `8`.
- Handoffs: `power-web-handoff-aed4f0dc-7067-4bb8-a6ce-ade3b776e2f6, power-web-handoff-fd0187c2-9de3-4ea8-b47c-cd93e8ecc5c9`.
- Provider calls: `0`; new pipeline runs: `0`; blind leakage: `0`.
- Restart verified: `True`.

## Requirements

| Requirement | Status | Evidence |
|---|---|---|
| `PW-HO-POL-01` | PASS | tests/test_power_web_handoff_contracts.py::test_radar_product_policy_is_ordered_and_versioned |
| `PW-HO-PROD-01` | PASS | tests/test_power_web_handoff_contracts.py::test_role_demands_freeze_product_versions |
| `PW-HO-ELIG-01` | PASS | tests/test_power_web_handoff_contracts.py::test_review_needed_candidate_requires_acknowledgement |
| `PW-HO-PROV-01` | PASS | tests/test_power_web_handoff_contracts.py::test_source_less_candidate_is_rejected |
| `PW-HO-ID-01` | PASS | tests/test_power_web_handoff_contracts.py::test_account_identity_prefers_inn_and_scopes_provisional_ids |
| `PW-HO-ROLE-01` | PASS | tests/test_power_web_handoff_contracts.py::test_role_demand_contract_excludes_search_inventions |
| `PW-HO-ROLE-02` | PASS | tests/test_power_web_handoff_contracts.py::test_equal_role_codes_from_two_products_are_not_merged |
| `PW-HO-SIG-01` | PASS | tests/test_power_web_handoff_contracts.py::test_signal_selector_uses_latest_matching_candidate_scope |
| `PW-HO-IDEM-01` | PASS | tests/test_persisted_power_web_handoff.py::test_handoff_is_immutable_and_idempotent |
| `PW-HO-API-01` | PASS | tests/test_power_web_handoff_api.py::test_power_web_policy_and_handoff_round_trip |
| `PW-HO-UI-01` | PASS | tests/test_frontend_architecture_contract.py::test_radar_power_web_handoff_ui_contract |
| `PW-HO-ARCH-01` | PASS | tests/test_backend_architecture_contract.py::test_power_web_handoff_package_boundaries |
| `PW-HO-BENCH-01` | PASS | tests/test_power_web_benchmark_contract.py::test_handoff_contract_has_no_blind_control_fields |
| `PW-HO-NET-01` | PASS | tests/test_power_web_handoff_api.py::test_handoff_has_zero_provider_and_pipeline_calls |
| `PW-HO-PROC-01` | PASS | tests/test_radar_pipeline_documentation_contract.py::test_power_web_handoff_evidence_loop |

## Retrospective

Radar-product ownership is isolated in a versioned policy, so candidate and signal configuration cannot overwrite product bindings. Handoff snapshots freeze account identity, product versions, role demand and optional signal lineage without pretending that people were already discovered.

The deterministic demo fixture is explicitly marked as fixture import and records zero provider calls. Future Power Web runtime slices consume the handoff; they must not mutate it or silently merge similar roles across products.
