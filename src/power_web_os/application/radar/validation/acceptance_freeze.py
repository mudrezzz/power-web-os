"""Immutable acceptance-manifest freeze used by reproducible live validation."""

from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path


def manifest_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_acceptance_freeze(*, manifest_path: Path, output_path: Path, git_commit: str = "") -> dict[str, object]:
    record: dict[str, object] = {
        "schema_version": "radar_acceptance_freeze.v1",
        "manifest_path": manifest_path.as_posix(),
        "manifest_sha256": manifest_sha256(manifest_path),
        "git_commit": git_commit,
        "frozen_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "initial_live_run_ids": [],
        "incremental_live_run_id": "",
        "pre_restart_report_sha256": {},
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return record


def verify_acceptance_freeze(*, manifest_path: Path, freeze_path: Path) -> dict[str, object]:
    record = json.loads(freeze_path.read_text(encoding="utf-8"))
    expected = str(record.get("manifest_sha256") or "")
    actual = manifest_sha256(manifest_path)
    if not expected or expected != actual:
        raise RuntimeError(
            f"Acceptance manifest changed after freeze: expected {expected or 'missing'}, got {actual}."
        )
    return record
