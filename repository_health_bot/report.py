"""Render repository health results as Markdown and JSON."""

from __future__ import annotations

import json
from pathlib import Path

from .checks import is_within
from .models import HealthReport


def markdown_report(report: HealthReport) -> str:
    """Render a deterministic, human-readable Markdown report."""
    lines = ["# Repository Health Report", "", f"Selected root: `{report.root}`", ""]
    for result in report.results:
        lines.extend(
            [
                f"## {result.name}",
                "",
                f"**Status:** {result.status}",
                "",
                result.summary,
            ]
        )
        if result.details:
            lines.extend(["", *[f"- {detail}" for detail in result.details]])
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def json_report(report: HealthReport) -> str:
    """Render a stable JSON report suitable for an artifact or local review."""
    return json.dumps(report.as_dict(), indent=2, sort_keys=True) + "\n"


def contained_output_path(root: Path, requested_path: str | Path) -> Path:
    """Resolve an output path and reject paths outside the selected root."""
    requested = Path(requested_path).expanduser()
    output = requested.resolve() if requested.is_absolute() else (root / requested).resolve()
    if not is_within(root, output):
        raise ValueError("JSON output must stay within the selected project directory.")
    return output


def write_json_report(report: HealthReport, root: Path, requested_path: str | Path) -> Path:
    """Write JSON only inside root; create only contained parent directories."""
    output = contained_output_path(root, requested_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json_report(report), encoding="utf-8")
    return output
