"""Runtime-config projection for Radar model profiles."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from power_web_os.application.radar_model_profiles import (
    RadarModelProfileError,
    RadarModelProfileRegistry,
)


def runtime_model_profiles_config(model_profile_dir: str) -> dict[str, Any]:
    root = Path(model_profile_dir)
    if not root.is_absolute():
        root = Path.cwd() / root
    try:
        registry = RadarModelProfileRegistry.from_directory(root)
        candidate = registry.require("candidate_discovery_default")
        signal = registry.require("signal_monitoring_default")
    except RadarModelProfileError as exc:
        return {
            "status": "failed",
            "directory": _display_path(root),
            "error": str(exc),
        }
    return {
        "status": "loaded",
        "directory": _display_path(root),
        "candidate_discovery": candidate.to_summary(),
        "signal_monitoring": signal.to_summary(),
    }


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return path.as_posix()
