"""Small, local-only checks for an explicitly selected repository directory."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from collections.abc import Callable, Iterable
from pathlib import Path

from .models import CheckResult

_MARKDOWN_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+[^)]*)?\)")
# Generated metadata and virtual environments are not project source or documentation.
_EXCLUDED_DIRECTORIES = frozenset(
    {".git", ".venv", ".venv-wsl", "__pycache__", ".mypy_cache", ".ruff_cache", "artifacts"}
)


def selected_root(path: str | Path) -> Path:
    """Resolve and validate the only directory the bot may inspect."""
    root = Path(path).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Selected path is not a directory: {path}")
    return root


def is_within(root: Path, candidate: Path) -> bool:
    """Return whether a resolved candidate stays within the selected root."""
    try:
        candidate.relative_to(root)
    except ValueError:
        return False
    return True


def iter_local_files(root: Path, suffix: str | None = None) -> Iterable[Path]:
    """Yield non-symlinked files below root without following linked directories."""
    for directory, directories, files in os.walk(root, followlinks=False):
        directories[:] = [
            name
            for name in directories
            if name not in _EXCLUDED_DIRECTORIES and not (Path(directory) / name).is_symlink()
        ]
        for name in files:
            candidate = Path(directory) / name
            if candidate.is_symlink() or (suffix and candidate.suffix.lower() != suffix):
                continue
            resolved = candidate.resolve()
            if is_within(root, resolved):
                yield resolved


def readme_check(root: Path) -> CheckResult:
    """Check for a conventional README file at the selected root."""
    readmes = [
        path for path in root.iterdir() if path.is_file() and path.name.lower().startswith("readme")
    ]
    if readmes:
        return CheckResult("README present", "pass", f"Found {readmes[0].name}.")
    return CheckResult("README present", "warn", "No README file exists at the selected root.")


def license_check(root: Path) -> CheckResult:
    """Check for a conventional license file at the selected root."""
    license_names = {"license", "license.md", "license.txt", "copying", "copying.txt"}
    licenses = [
        path for path in root.iterdir() if path.is_file() and path.name.lower() in license_names
    ]
    if licenses:
        return CheckResult("License present", "pass", f"Found {licenses[0].name}.")
    return CheckResult(
        "License present", "warn", "No conventional license file exists at the selected root."
    )


def python_file_count_check(root: Path) -> CheckResult:
    """Count Python source files without entering linked directories."""
    count = sum(1 for _ in iter_local_files(root, ".py"))
    return CheckResult("Python file count", "pass", f"Found {count} Python file(s).")


def markdown_local_link_check(root: Path) -> CheckResult:
    """Check only local Markdown links; URLs and paths outside root are never followed."""
    invalid_links: list[str] = []
    markdown_files = sorted(iter_local_files(root, ".md"))
    for markdown_file in markdown_files:
        text = markdown_file.read_text(encoding="utf-8", errors="replace")
        for target in _MARKDOWN_LINK.findall(text):
            if _is_external_or_anchor(target):
                continue
            local_target = target.split("#", maxsplit=1)[0]
            if not local_target:
                continue
            resolved = (markdown_file.parent / local_target).resolve()
            if not is_within(root, resolved) or not resolved.exists():
                source = markdown_file.relative_to(root).as_posix()
                invalid_links.append(f"{source} -> {target}")
    if invalid_links:
        return CheckResult(
            "Markdown local links",
            "warn",
            f"Found {len(invalid_links)} missing or out-of-root local link(s).",
            tuple(invalid_links),
        )
    return CheckResult(
        "Markdown local links",
        "pass",
        f"Validated local links in {len(markdown_files)} Markdown file(s); URLs were not followed.",
    )


def _is_external_or_anchor(target: str) -> bool:
    """Identify links the local-only checker must never fetch or inspect."""
    lowered = target.lower()
    return target.startswith("#") or lowered.startswith(("http://", "https://", "mailto:", "data:"))


def requirements_files(root: Path) -> tuple[Path, ...]:
    """Return non-symlinked requirements*.txt files strictly inside root."""
    return tuple(
        path
        for path in sorted(iter_local_files(root))
        if path.name.startswith("requirements") and path.name.endswith(".txt")
    )


def pip_audit_check(
    root: Path,
    *,
    executable: str = "pip-audit",
    timeout_seconds: int = 30,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> CheckResult:
    """Optionally audit local requirement files, gracefully handling unavailable tooling."""
    files = requirements_files(root)
    if not files:
        return CheckResult("Dependency audit", "skip", "No requirements*.txt files were found.")
    if shutil.which(executable) is None:
        return CheckResult(
            "Dependency audit", "skip", "pip-audit is not installed; audit was not run."
        )

    failures: list[str] = []
    for requirements_file in files:
        try:
            completed = runner(
                [executable, "--requirement", str(requirements_file)],
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired:
            relative_file = requirements_file.relative_to(root).as_posix()
            failures.append(f"{relative_file}: timed out after {timeout_seconds}s")
            continue
        except OSError as error:
            relative_file = requirements_file.relative_to(root).as_posix()
            failures.append(f"{relative_file}: could not run pip-audit ({error})")
            continue
        if completed.returncode:
            output = (completed.stdout + completed.stderr).strip().splitlines()
            detail = output[-1] if output else f"pip-audit exited {completed.returncode}"
            failures.append(f"{requirements_file.relative_to(root).as_posix()}: {detail}")

    if failures:
        return CheckResult(
            "Dependency audit", "warn", "pip-audit reported an issue.", tuple(failures)
        )
    return CheckResult(
        "Dependency audit", "pass", f"pip-audit passed for {len(files)} requirement file(s)."
    )


def run_checks(
    root: Path, *, audit: bool = False, audit_timeout: int = 30
) -> tuple[CheckResult, ...]:
    """Run all deterministic checks, optionally adding the pip-audit subprocess check."""
    results: list[CheckResult] = [
        readme_check(root),
        license_check(root),
        python_file_count_check(root),
        markdown_local_link_check(root),
    ]
    if audit:
        results.append(pip_audit_check(root, timeout_seconds=audit_timeout))
    return tuple(results)
