from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from power_web_os.planner import DeterministicAccessPlanner
from power_web_os.serialization import (
    account_from_payload,
    build_access_plan_artifact,
    playbook_from_payload,
)

try:  # pragma: no cover - covered only when langgraph-dai is installed.
    from framework.workflows.base import BaseWorkflow, WorkflowExecutionContext, WorkflowNodeSpec

    FRAMEWORK_AVAILABLE = True
except Exception:  # pragma: no cover - normal path for base install.
    BaseWorkflow = object  # type: ignore[assignment,misc]
    WorkflowExecutionContext = Any  # type: ignore[misc,assignment]
    WorkflowNodeSpec = None  # type: ignore[assignment]
    FRAMEWORK_AVAILABLE = False


class AccessPlanningState(BaseModel):
    task_context: dict[str, Any] = Field(default_factory=dict)
    account_payload: dict[str, Any]
    playbook_payload: dict[str, Any]
    access_plan: dict[str, Any] | None = None
    workflow_metadata: dict[str, Any] = Field(default_factory=dict)
    unresolved_gaps: list[str] = Field(default_factory=list)
    error_message: str | None = None


class _FallbackAccessPlanningWorkflow:
    def __init__(self, planner: DeterministicAccessPlanner | None = None, **_: Any) -> None:
        self._planner = planner or DeterministicAccessPlanner()
        self._runtime_mode = "local_fallback"

    def compile(self) -> dict[str, Any]:
        return {
            "workflow": self.__class__.__name__,
            "runtime_mode": self._runtime_mode,
            "invoke_graph_ready": True,
            "resume_graph_ready": True,
            "invoke_node_count": 1,
            "resume_node_count": 1,
        }

    def invoke(self, payload: AccessPlanningState | dict[str, Any]) -> AccessPlanningState:
        state = AccessPlanningState.model_validate(payload)
        return self._run_plan(state=state, node_name="plan_access")

    def resume(self, payload: AccessPlanningState | dict[str, Any]) -> AccessPlanningState:
        return self.invoke(payload)

    def _runtime_metadata(self, *, state: AccessPlanningState, node_name: str) -> dict[str, Any]:
        return {
            "workflow_name": "AccessPlanningWorkflow",
            "runtime": "local_fallback",
            "framework_available": False,
            "runtime_mode": self._runtime_mode,
            "node_name": node_name,
            "task_id": state.task_context.get("task_id"),
            "correlation_id": state.task_context.get("correlation_id"),
            "planner": "DeterministicAccessPlanner",
        }

    def _run_plan(self, *, state: AccessPlanningState, node_name: str) -> AccessPlanningState:
        account = account_from_payload(state.account_payload)
        playbook = playbook_from_payload(state.playbook_payload)
        plan = self._planner.build_plan(account, playbook)
        metadata = self._runtime_metadata(state=state, node_name=node_name)
        artifact = build_access_plan_artifact(
            account=account,
            playbook=playbook,
            plan=plan,
            workflow_metadata=metadata,
        )
        return state.model_copy(
            update={
                "access_plan": artifact,
                "workflow_metadata": metadata,
                "unresolved_gaps": list(plan.unresolved_gaps),
                "error_message": None,
            }
        )


if FRAMEWORK_AVAILABLE:

    class AccessPlanningWorkflow(BaseWorkflow):  # type: ignore[misc,valid-type]
        def __init__(
            self,
            planner: DeterministicAccessPlanner | None = None,
            *,
            use_langgraph_runtime: bool = True,
            checkpointer: object | None = None,
            node_event_sink: object | None = None,
        ) -> None:
            super().__init__(
                use_langgraph_runtime=use_langgraph_runtime,
                checkpointer=checkpointer,
                node_event_sink=node_event_sink,
            )
            self._planner = planner or DeterministicAccessPlanner()
            self.compile()

        def state_schema(self) -> type[AccessPlanningState]:
            return AccessPlanningState

        def workflow_nodes(self, *, is_resume: bool) -> list[Any]:
            _ = is_resume
            return [
                WorkflowNodeSpec(  # type: ignore[misc,operator]
                    name="plan_access",
                    handler=self._plan_access_node,
                )
            ]

        def execute(self, state: AccessPlanningState) -> AccessPlanningState:
            return self._run_plan(state=state, node_name="plan_access")

        def execute_resume(self, state: AccessPlanningState) -> AccessPlanningState:
            return self.execute(state)

        def _plan_access_node(
            self,
            state: AccessPlanningState,
            context: WorkflowExecutionContext,
        ) -> AccessPlanningState:
            return self._run_plan(state=state, node_name=context.node_name)

        def _runtime_metadata(self, *, state: AccessPlanningState, node_name: str) -> dict[str, Any]:
            return {
                "workflow_name": "AccessPlanningWorkflow",
                "runtime": "langgraph_dai",
                "framework_available": True,
                "runtime_mode": getattr(self, "_runtime_mode", "unknown"),
                "node_name": node_name,
                "task_id": state.task_context.get("task_id"),
                "correlation_id": state.task_context.get("correlation_id"),
                "planner": "DeterministicAccessPlanner",
            }

        def _run_plan(self, *, state: AccessPlanningState, node_name: str) -> AccessPlanningState:
            account = account_from_payload(state.account_payload)
            playbook = playbook_from_payload(state.playbook_payload)
            plan = self._planner.build_plan(account, playbook)
            metadata = self._runtime_metadata(state=state, node_name=node_name)
            artifact = build_access_plan_artifact(
                account=account,
                playbook=playbook,
                plan=plan,
                workflow_metadata=metadata,
            )
            return state.model_copy(
                update={
                    "access_plan": artifact,
                    "workflow_metadata": metadata,
                    "unresolved_gaps": list(plan.unresolved_gaps),
                    "error_message": None,
                }
            )

else:
    AccessPlanningWorkflow = _FallbackAccessPlanningWorkflow
