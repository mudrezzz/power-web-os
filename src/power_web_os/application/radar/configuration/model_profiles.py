"""Config-backed model role profiles for Radar pipelines.

Model profiles are non-secret application configuration. They describe which
model role should be used by a pipeline, while credentials and deployment
overrides remain outside these files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, ValidationError, field_validator


DEFAULT_MODEL_PROFILE_DIR = Path(__file__).resolve().parents[5] / "config" / "radar" / "model_profiles"
SIGNAL_MONITORING_REQUIRED_ROLES = {
    "signal_task_builder",
    "signal_extractor",
    "signal_backup_extractor",
    "signal_evidence_judge",
    "signal_dedupe_judge",
}


class RadarModelProfileError(ValueError):
    """Raised when a model profile config cannot be loaded or validated."""


class RadarModelRoleSettings(BaseModel):
    role: str
    primary_model: str
    backup_model: str = ""
    temperature: float = 0.0
    max_attempts: int = 1

    @field_validator("role", "primary_model", "backup_model", mode="before")
    @classmethod
    def _string_or_empty(cls, value: Any) -> str:
        return "" if value is None else str(value).strip()

    @field_validator("primary_model")
    @classmethod
    def _primary_model_required(cls, value: str) -> str:
        if not value:
            raise ValueError("primary_model is required")
        return value

    @field_validator("max_attempts")
    @classmethod
    def _max_attempts_positive(cls, value: int) -> int:
        if value < 1:
            raise ValueError("max_attempts must be positive")
        return value

    def to_summary(self) -> dict[str, Any]:
        return {
            "role": self.role,
            "primary_model": self.primary_model,
            "backup_model": self.backup_model,
            "temperature": self.temperature,
            "max_attempts": self.max_attempts,
        }


class RadarModelProfile(BaseModel):
    profile_id: str
    pipeline_id: str
    description: str = ""
    roles: dict[str, RadarModelRoleSettings] = Field(default_factory=dict)

    @field_validator("profile_id", "pipeline_id", "description", mode="before")
    @classmethod
    def _profile_string_or_empty(cls, value: Any) -> str:
        return "" if value is None else str(value).strip()

    @field_validator("profile_id", "pipeline_id")
    @classmethod
    def _required_profile_field(cls, value: str) -> str:
        if not value:
            raise ValueError("field is required")
        return value

    @field_validator("roles", mode="before")
    @classmethod
    def _roles_from_mapping(cls, value: Any) -> dict[str, Any]:
        if not isinstance(value, dict):
            raise ValueError("roles must be an object")
        result: dict[str, Any] = {}
        for role, settings in value.items():
            if not isinstance(settings, dict):
                raise ValueError(f"role {role} must be an object")
            result[str(role)] = {"role": str(role), **settings}
        return result

    def require_roles(self, required_roles: set[str]) -> None:
        missing = sorted(required_roles - set(self.roles))
        if missing:
            raise RadarModelProfileError(
                f"Model profile {self.profile_id} is missing required roles: {', '.join(missing)}"
            )

    def to_summary(self) -> dict[str, Any]:
        return {
            "profile_id": self.profile_id,
            "pipeline_id": self.pipeline_id,
            "description": self.description,
            "roles": {
                role: settings.to_summary()
                for role, settings in sorted(self.roles.items())
            },
        }


class RadarModelProfileRegistry:
    def __init__(self, profiles: list[RadarModelProfile]) -> None:
        self._profiles = {profile.profile_id: profile for profile in profiles}

    @classmethod
    def from_directory(cls, directory: Path | str = DEFAULT_MODEL_PROFILE_DIR) -> "RadarModelProfileRegistry":
        root = Path(directory)
        if not root.exists():
            raise RadarModelProfileError(f"Model profile directory does not exist: {root}")
        profiles = [load_model_profile(path) for path in sorted(root.glob("*.json"))]
        if not profiles:
            raise RadarModelProfileError(f"Model profile directory is empty: {root}")
        return cls(profiles)

    def require(self, profile_id: str) -> RadarModelProfile:
        profile = self._profiles.get(profile_id)
        if profile is None:
            raise RadarModelProfileError(f"Unknown model profile: {profile_id}")
        return profile

    def for_pipeline(self, pipeline_id: str) -> list[RadarModelProfile]:
        return [profile for profile in self._profiles.values() if profile.pipeline_id == pipeline_id]

    def to_summary(self) -> dict[str, Any]:
        return {
            profile_id: profile.to_summary()
            for profile_id, profile in sorted(self._profiles.items())
        }


def default_model_profile_registry() -> RadarModelProfileRegistry:
    return RadarModelProfileRegistry.from_directory(DEFAULT_MODEL_PROFILE_DIR)


def load_model_profile(path: Path | str) -> RadarModelProfile:
    profile_path = Path(path)
    try:
        payload = json.loads(profile_path.read_text(encoding="utf-8"))
        profile = RadarModelProfile.model_validate(payload)
    except (OSError, json.JSONDecodeError, ValidationError, ValueError) as exc:
        raise RadarModelProfileError(f"Invalid model profile {profile_path}: {exc}") from exc
    if profile.pipeline_id == "signal-monitoring":
        profile.require_roles(SIGNAL_MONITORING_REQUIRED_ROLES)
    return profile
