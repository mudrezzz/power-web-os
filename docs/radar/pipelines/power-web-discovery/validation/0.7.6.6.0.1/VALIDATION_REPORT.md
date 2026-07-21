# Product and sales Playbook foundation validation

Slice: `0.7.6.6.0.1`
Validation status: **PASS**

## Runtime evidence

- Product: `product-smartdiagnostics`.
- Active version: `sales-playbook-52395309-e69b-46ef-8887-ecb37310fcfd`.
- Draft revision after UI round-trip and restart: `19`.
- Semantic roles: `8`.
- Access routes: `4`.
- Published versions: `1`.
- UI: `ru, en` at `1280x720, 1366x768`.
- Provider calls: `0`; new pipeline runs: `0`.
- Blind leakage: `0`.

| Requirement | Status | Evidence |
|---|---|---|
| `PWF-PROD-01` | PASS | tests/test_sales_playbook_contracts.py::test_product_publish_activate_restore_and_archive |
| `PWF-ROLE-01` | PASS | tests/test_sales_playbook_contracts.py::test_published_roles_require_semantic_fields |
| `PWF-ROLE-02` | PASS | tests/test_sales_playbook_contracts.py::test_title_hypothesis_cannot_mutate_role_policy |
| `PWF-ACCESS-01` | PASS | tests/test_sales_playbook_contracts.py::test_access_rules_reject_dangling_role_references |
| `PWF-VERS-01` | PASS | tests/test_sales_playbook_api.py::test_published_version_is_immutable_and_stale_draft_conflicts |
| `PWF-API-01` | PASS | tests/test_sales_playbook_api.py::test_sales_playbook_round_trip |
| `PWF-UI-01` | PASS | tests/test_frontend_architecture_contract.py::test_playbook_workspace_uses_backend_product_contract |
| `PWF-UI-02` | PASS | tests/test_frontend_architecture_contract.py::test_account_playbook_analysis_lives_in_access_plans |
| `PWF-DEMO-01` | PASS | tests/test_sales_playbook_api.py::test_smartdiagnostics_seed_is_idempotent |
| `PWF-BENCH-01` | PASS | tests/test_power_web_benchmark_contract.py::test_sales_playbook_amendment_has_no_blind_leakage |
| `PWF-COMPAT-01` | PASS | tests/test_power_web_board.py, tests/test_access_planning_workflow.py |
| `PWF-NET-01` | PASS | tests/test_sales_playbook_contracts.py::test_sales_playbook_has_no_provider_dependency |
| `PWF-PROC-01` | PASS | tests/test_radar_pipeline_documentation_contract.py::test_power_web_playbook_foundation_evidence_loop |

## Retrospective

The previous account-specific Playbook screen mixed global policy with its application. The slice separates those responsibilities and makes version lineage explicit before people discovery starts.

Full regression exposed calendar-aging Signal Monitoring fixtures: hardcoded fresh dates crossed the seven-day window. The fixtures now derive their fresh event date at runtime; temporal boundary semantics remain covered by dedicated fixed-date tests.

No search or provider runtime was invoked. The next slice must consume the active immutable product and semantic-role policy rather than inventing a universal role list.
