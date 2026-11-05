"""Runtime settings read from environment variables, so dev and production run the same code."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    max_upload_mb: int = 10
    max_rows: int = 200_000
    workflow_file: Path | None = None
    log_level: str = "INFO"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024


def _int_env(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a whole number, got {raw!r}.") from exc
    if value <= 0:
        raise ValueError(f"{name} must be greater than zero, got {value}.")
    return value


def load_settings() -> Settings:
    workflow = os.environ.get("FLOW_METRICS_WORKFLOW_FILE", "").strip()
    return Settings(
        max_upload_mb=_int_env("FLOW_METRICS_MAX_UPLOAD_MB", 10),
        max_rows=_int_env("FLOW_METRICS_MAX_ROWS", 200_000),
        workflow_file=Path(workflow) if workflow else None,
        log_level=os.environ.get("FLOW_METRICS_LOG_LEVEL", "INFO").upper(),
    )
