"""Compatibility shim for moved candidate-discovery staged execution. Source of truth: execution package."""
from power_web_os.application.radar.candidate_discovery.execution.orchestrator import *  # noqa: F401,F403
from power_web_os.application.radar.candidate_discovery.execution.expansion_diagnostics import _target_probe_guarantees  # noqa: F401
from power_web_os.application.radar.candidate_discovery.execution.finalization_universe import _append_review_needed_universe_entities  # noqa: F401
