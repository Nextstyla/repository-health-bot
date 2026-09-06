"""Typed result models for repository health checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Literal

CheckStatus = Literal["pass", "warn", "fail", "skip"]


@dataclass(frozen=True)
class CheckResult:
    """One deterministic repository-health check result."""

    name: str
    status: CheckStatus
    summary: str
    details: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        return asdict(self)


@dataclass(frozen=True)
class HealthReport:
    """The complete report for one explicitly selected repository root."""

    root: str
    results: tuple[CheckResult, ...]

    def as_dict(self) -> dict[str, object]:
        """Return a JSON-serializable representation."""
        return {
            "root": self.root,
            "results": [result.as_dict() for result in self.results],
        }
