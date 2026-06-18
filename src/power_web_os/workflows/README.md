# Workflows Layer

The workflows layer owns runtime wrappers around application services. It is the
place where optional `langgraph-document-ai-platform` / `langgraph-dai`
integration belongs.

## Ownership

- `live_icp_radar_workflow.py` wraps the live Radar application service in the
  existing `BaseWorkflow` pattern when the framework is installed. Its node
  names map to application pipeline phases such as planning, collection,
  extraction, evaluation, validation, and artifact shaping.
- `live_radar_executor.py` adapts the live workflow to the application
  `LiveRadarArtifactExecutor` port for persisted run services.
- Local fallback workflow behavior remains available for base installs and
  deterministic tests.

## Dependency Rules

Allowed imports:

- application services and contracts;
- provider ports passed into the workflow;
- `framework.workflows.base` for optional LangGraph runtime integration.

Forbidden imports:

- SQLAlchemy queries or persistence transactions;
- provider HTTP calls hidden directly inside workflow nodes;
- domain scoring or review semantics hidden inside workflow wrappers;
- FastAPI route handling.

Workflows orchestrate and annotate execution. They do not own provider
normalization, scoring rules, durable run state, journal semantics, or API
transport.
When a technical trace repository is wired by a worker, workflow adapters pass
the application tracer into execution context. Redaction and trace semantics
still belong to `application`, not to workflow nodes.

## How To Extend

1. Put business/use-case behavior in an application service phase first.
2. Wrap the service here for LangGraph runtime metadata and node structure.
3. Keep fallback runtime behavior for tests without optional agent dependencies.
4. Add tests that prove the wrapper delegates to the service and preserves
   artifact contracts.
