"""Task-context parsing for Radar external-call budget settings."""

from __future__ import annotations

from power_web_os.application.radar.shared.budgets.external_models import RadarExternalCallBudgetSettings


def external_budget_settings_from_context(context: dict[str, object]) -> RadarExternalCallBudgetSettings:
    profile = str(context.get("run_profile") or "live").strip().lower()
    if profile not in {"live", "smoke"}:
        profile = "live"
    smoke = profile == "smoke"
    return RadarExternalCallBudgetSettings(
        run_profile=profile,
        max_openrouter_calls_per_run=_context_int_or_default(context, "max_openrouter_calls_per_run", 8 if smoke else None),
        max_openrouter_planner_calls_per_run=_context_int_or_default(
            context, "max_openrouter_planner_calls_per_run", 2 if smoke else None
        ),
        max_openrouter_web_task_calls_per_run=_context_int_or_default(
            context, "max_openrouter_web_task_calls_per_run", 6 if smoke else None
        ),
        max_recall_expansion_openrouter_calls_per_run=_context_int_or_default(
            context, "max_recall_expansion_openrouter_calls_per_run", 2 if smoke else None
        ),
        max_openrouter_server_tool_web_searches_per_run=_context_int_or_default(
            context, "max_openrouter_server_tool_web_searches_per_run", 24 if smoke else None
        ),
        max_dadata_lookups_per_run=_context_int_or_default(context, "max_dadata_lookups_per_run", 3 if smoke else None),
        max_source_verification_requests_per_run=_context_int_or_default(
            context, "max_source_verification_requests_per_run", 20 if smoke else None
        ),
        max_provider_retries_per_task=(
            _context_int(context, "max_provider_retries_per_task")
            if _context_int(context, "max_provider_retries_per_task") is not None
            else (1 if smoke else 0)
        ),
        openrouter_web_max_results_per_call=_context_int_or_default(
            context, "openrouter_web_max_results_per_call", 3 if smoke else None
        ),
        openrouter_web_max_total_results_per_call=_context_int_or_default(
            context, "openrouter_web_max_total_results_per_call", 6 if smoke else None
        ),
        smoke_max_candidates=_context_int_or_default(context, "smoke_max_candidates", 2 if smoke else None),
        smoke_max_signals=_context_int_or_default(context, "smoke_max_signals", 1 if smoke else None),
        budget_reserve_limits=_budget_reserve_limits(context, smoke=smoke),
    )


def _context_int(context: dict[str, object], key: str) -> int | None:
    value = context.get(key)
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _context_int_or_default(context: dict[str, object], key: str, default: int | None) -> int | None:
    parsed = _context_int(context, key)
    return default if parsed is None else parsed


def _budget_reserve_limits(context: dict[str, object], *, smoke: bool) -> dict[str, int]:
    defaults = _default_budget_reserve_limits(smoke=smoke)
    configured = context.get("budget_reserve_limits")
    if isinstance(configured, dict):
        parsed = {
            str(key): parsed
            for key, value in configured.items()
            if (parsed := _parse_non_negative_int(value)) is not None
        }
        return {**defaults, **parsed}
    return defaults


def _default_budget_reserve_limits(*, smoke: bool) -> dict[str, int]:
    if not smoke:
        return {}
    return {
        "primary_discovery": 3,
        "registry_identity": 2,
        "recall_expansion": 3,
        "official_coverage_probe": 2,
        "open_web_coverage_probe": 3,
        "production_site_coverage_probe": 2,
        "extraction_recovery": 2,
        "signal_search": 1,
    }


def _parse_non_negative_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None
