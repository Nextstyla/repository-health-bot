"""Command-line entry point for the local Repository Health Bot."""

from __future__ import annotations

import argparse
import sys

from .checks import run_checks, selected_root
from .models import HealthReport
from .report import markdown_report, write_json_report


def build_parser() -> argparse.ArgumentParser:
    """Create the explicit local-only command-line interface."""
    parser = argparse.ArgumentParser(
        description="Run local repository health checks without following Markdown URLs."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=".",
        help="Repository directory to inspect; defaults to the current directory.",
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Run pip-audit against local requirements*.txt files, when pip-audit is installed.",
    )
    parser.add_argument(
        "--audit-timeout",
        type=positive_seconds,
        default=30,
        metavar="SECONDS",
        help="Maximum seconds per pip-audit invocation; default: 30.",
    )
    parser.add_argument(
        "--json-output",
        metavar="PATH",
        help="Write JSON to a file within the selected repository directory.",
    )
    return parser


def positive_seconds(value: str) -> int:
    """Require an explicit positive timeout."""
    seconds = int(value)
    if seconds < 1:
        raise argparse.ArgumentTypeError("timeout must be at least one second")
    return seconds


def main(argv: list[str] | None = None) -> int:
    """Run checks and return a command-line status code."""
    args = build_parser().parse_args(argv)
    try:
        root = selected_root(args.path)
        report = HealthReport(
            root=str(root),
            results=run_checks(root, audit=args.audit, audit_timeout=args.audit_timeout),
        )
        if args.json_output:
            write_json_report(report, root, args.json_output)
    except ValueError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2

    print(markdown_report(report), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
