"""Config-backed non-secret Radar runtime settings.

The repository config is the source of truth for non-secret Radar defaults.
Process environment, local `.env`, and explicit API overrides remain stronger
deployment/emergency override layers, in that order. Local `.env` intentionally
overrides inherited process variables for Codex/manual live Radar runs.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping


DEFAULT_RADAR_CONFIG_DIR = Path(__file__).resolve().parents[3] / "config" / "radar"


def effective_runtime_env(
    *,
    env: Mapping[str, str] | None = None,
    dotenv_path: Path | None = None,
    overrides: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    return {
        key: str(value)
        for key, (value, _source) in effective_runtime_values(
            env=env,
            dotenv_path=dotenv_path,
            overrides=overrides,
        ).items()
    }


def effective_runtime_values(
    *,
    env: Mapping[str, str] | None = None,
    dotenv_path: Path | None = None,
    overrides: Mapping[str, Any] | None = None,
) -> dict[str, tuple[Any, str]]:
    dotenv_values = _load_env_file(dotenv_path) if dotenv_path is not None else {}
    source_env = dict(os.environ if env is None else env)
    override_values = {key: value for key, value in (overrides or {}).items() if value is not None}
    config_dir = _radar_config_dir(dotenv_values=dotenv_values, source_env=source_env, overrides=override_values)
    requested_profile = (
        override_values.get("POWER_WEB_OS_RADAR_RUN_PROFILE")
        or dotenv_values.get("POWER_WEB_OS_RADAR_RUN_PROFILE")
        or source_env.get("POWER_WEB_OS_RADAR_RUN_PROFILE")
    )
    result = _load_config_values(config_dir=config_dir, requested_run_profile=str(requested_profile or "").strip())
    result.setdefault("POWER_WEB_OS_RADAR_CONFIG_DIR", (_display_path(config_dir), "config_default"))

    _overlay_values(result, source_env, "process_env")
    _overlay_values(result, dotenv_values, ".env")
    _overlay_values(result, override_values, "explicit_override")
    return result


def runtime_env_value(name: str, default: str | None = None) -> str | None:
    return effective_runtime_env().get(name, default)


def _load_config_values(*, config_dir: Path, requested_run_profile: str = "") -> dict[str, tuple[Any, str]]:
    result: dict[str, tuple[Any, str]] = {}
    defaults = _load_json_env(config_dir / "runtime_defaults.json")
    for key, value in defaults.items():
        result[key] = (value, "config:runtime_defaults")
    profile = (requested_run_profile or str(defaults.get("POWER_WEB_OS_RADAR_RUN_PROFILE") or "") or "live").strip().lower()
    if profile not in {"live", "smoke"}:
        profile = "live"
    profile_values = _load_json_env(config_dir / "run_profiles" / f"{profile}.json")
    for key, value in profile_values.items():
        result[key] = (value, f"config:run_profile:{profile}")
    result["POWER_WEB_OS_RADAR_RUN_PROFILE"] = (profile, f"config:run_profile:{profile}")
    return result


def _load_json_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    env_payload = payload.get("env") if isinstance(payload, dict) else {}
    if not isinstance(env_payload, dict):
        return {}
    return {
        str(key): str(value)
        for key, value in env_payload.items()
        if str(key).strip() and value is not None
    }


def _overlay_values(target: dict[str, tuple[Any, str]], values: Mapping[str, Any], source: str) -> None:
    for key, value in values.items():
        if value is not None:
            target[key] = (value, source)


def _radar_config_dir(
    *,
    dotenv_values: Mapping[str, str],
    source_env: Mapping[str, str],
    overrides: Mapping[str, Any],
) -> Path:
    raw = (
        overrides.get("POWER_WEB_OS_RADAR_CONFIG_DIR")
        or dotenv_values.get("POWER_WEB_OS_RADAR_CONFIG_DIR")
        or source_env.get("POWER_WEB_OS_RADAR_CONFIG_DIR")
    )
    root = Path(str(raw).strip()) if raw else DEFAULT_RADAR_CONFIG_DIR
    if not root.is_absolute():
        root = Path.cwd() / root
    return root


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return path.as_posix()


def _load_env_file(path: Path | None) -> dict[str, str]:
    if path is None or not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        normalized_key = key.strip()
        if normalized_key.startswith("export "):
            normalized_key = normalized_key[7:].strip()
        values[normalized_key] = value.strip().strip('"').strip("'")
    return values
