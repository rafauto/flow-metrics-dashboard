"""Workflow mapping: which status belongs to which flow category."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from importlib import resources
from pathlib import Path

import yaml

from flow_metrics.errors import DataValidationError


class Category(str, Enum):
    BACKLOG = "backlog"
    ACTIVE = "active"
    WAITING = "waiting"
    DONE = "done"


IN_PROGRESS = frozenset({Category.ACTIVE, Category.WAITING})


def normalize_status(status: str) -> str:
    return " ".join(str(status).split()).casefold()


@dataclass(frozen=True)
class Workflow:
    """Status -> category lookup. Statuses are matched ignoring case and extra spaces."""

    mapping: Mapping[str, Category] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Mapping[str, Iterable[str]]) -> Workflow:
        mapping: dict[str, Category] = {}
        for raw_category, statuses in data.items():
            try:
                category = Category(str(raw_category).strip().lower())
            except ValueError as exc:
                valid = ", ".join(c.value for c in Category)
                raise DataValidationError(
                    f"Unknown category {raw_category!r} in workflow mapping. Use one of: {valid}."
                ) from exc
            for status in statuses or []:
                mapping[normalize_status(status)] = category
        return cls(mapping)

    def category_of(self, status: str) -> Category | None:
        return self.mapping.get(normalize_status(status))

    def unknown_statuses(self, statuses: Iterable[str]) -> list[str]:
        return sorted({s for s in statuses if self.category_of(s) is None})

    def with_overrides(self, overrides: Mapping[str, Category]) -> Workflow:
        merged = dict(self.mapping)
        merged.update({normalize_status(s): Category(c) for s, c in overrides.items()})
        return Workflow(merged)

    def require_known(self, statuses: Iterable[str]) -> None:
        unknown = self.unknown_statuses(statuses)
        if unknown:
            raise DataValidationError(
                "These statuses are not mapped to a category: "
                + ", ".join(repr(s) for s in unknown)
                + ". Map them in the sidebar or in your workflow file."
            )


def load_workflow(path: Path | None = None) -> Workflow:
    """Load a workflow YAML file, or the bundled default when no path is given."""
    if path is None:
        text = resources.files("flow_metrics").joinpath("default_workflow.yaml").read_text("utf-8")
    else:
        if not path.exists():
            raise DataValidationError(f"Workflow file not found: {path}")
        text = path.read_text("utf-8")
    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        raise DataValidationError("The workflow file must map categories to lists of statuses.")
    return Workflow.from_dict(data)
