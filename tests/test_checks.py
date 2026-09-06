"""Tests for local-only repository checks."""

from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from repository_health_bot.checks import (
    markdown_local_link_check,
    pip_audit_check,
    python_file_count_check,
    selected_root,
)


class ChecksTestCase(unittest.TestCase):
    def test_selected_root_rejects_a_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            file_path = Path(temporary_directory) / "not-a-directory.txt"
            file_path.write_text("content", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "not a directory"):
                selected_root(file_path)

    def test_python_file_count_skips_a_symlink_outside_root(self) -> None:
        with (
            tempfile.TemporaryDirectory() as root_directory,
            tempfile.TemporaryDirectory() as outside_directory,
        ):
            root = Path(root_directory).resolve()
            (root / "inside.py").write_text("print('inside')\n", encoding="utf-8")
            outside_file = Path(outside_directory) / "outside.py"
            outside_file.write_text("print('outside')\n", encoding="utf-8")
            try:
                (root / "linked.py").symlink_to(outside_file)
            except OSError as error:
                self.skipTest(f"Symlinks are unavailable: {error}")

            result = python_file_count_check(root)

            self.assertEqual("Found 1 Python file(s).", result.summary)

    def test_python_file_count_excludes_virtual_environment_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            (root / "application.py").write_text("print('application')\n", encoding="utf-8")
            virtual_environment = root / ".venv" / "Lib" / "site-packages"
            virtual_environment.mkdir(parents=True)
            (virtual_environment / "dependency.py").write_text(
                "print('dependency')\n", encoding="utf-8"
            )

            result = python_file_count_check(root)

            self.assertEqual("Found 1 Python file(s).", result.summary)

    def test_markdown_check_does_not_follow_external_urls(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            (root / "README.md").write_text(
                "[GitHub](https://github.com)\n[Section](#heading)\n",
                encoding="utf-8",
            )

            result = markdown_local_link_check(root)

            self.assertEqual("pass", result.status)
            self.assertIn("URLs were not followed", result.summary)

    def test_markdown_check_reports_missing_and_out_of_root_links(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            (root / "README.md").write_text(
                "[Missing](missing.md)\n[Outside](../outside.md)\n",
                encoding="utf-8",
            )

            result = markdown_local_link_check(root)

            self.assertEqual("warn", result.status)
            self.assertEqual(2, len(result.details))

    def test_pip_audit_gracefully_skips_when_tool_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            (root / "requirements.txt").write_text("example==1.0\n", encoding="utf-8")

            with patch("repository_health_bot.checks.shutil.which", return_value=None):
                result = pip_audit_check(root)

            self.assertEqual("skip", result.status)
            self.assertIn("not installed", result.summary)

    def test_pip_audit_timeout_is_a_warning_without_stopping_other_checks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            requirements_file = root / "requirements.txt"
            requirements_file.write_text("example==1.0\n", encoding="utf-8")

            def timed_out_runner(
                *_args: object, **_kwargs: object
            ) -> subprocess.CompletedProcess[str]:
                raise subprocess.TimeoutExpired("pip-audit", 1)

            with patch(
                "repository_health_bot.checks.shutil.which", return_value="/usr/bin/pip-audit"
            ):
                result = pip_audit_check(root, timeout_seconds=1, runner=timed_out_runner)

            self.assertEqual("warn", result.status)
            self.assertIn("timed out after 1s", result.details[0])


if __name__ == "__main__":
    unittest.main()
