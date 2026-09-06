"""Tests for report rendering, output containment, and the CLI."""

from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
from pathlib import Path

from repository_health_bot.__main__ import main
from repository_health_bot.models import CheckResult, HealthReport
from repository_health_bot.report import contained_output_path, json_report, markdown_report


class ReportTestCase(unittest.TestCase):
    def test_markdown_and_json_reports_include_check_results(self) -> None:
        report = HealthReport(
            root="/example",
            results=(CheckResult("README present", "pass", "Found README.md."),),
        )

        self.assertIn("# Repository Health Report", markdown_report(report))
        self.assertIn("**Status:** pass", markdown_report(report))
        rendered_json = json.loads(json_report(report))
        self.assertEqual("README present", rendered_json["results"][0]["name"])

    def test_contained_output_path_rejects_parent_directory_escape(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()

            with self.assertRaisesRegex(ValueError, "stay within"):
                contained_output_path(root, "../report.json")

    def test_cli_writes_json_only_inside_selected_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            (root / "README.md").write_text("# Example\n", encoding="utf-8")
            output = StringIO()

            with redirect_stdout(output):
                status = main([str(root), "--json-output", "artifacts/report.json"])

            self.assertEqual(0, status)
            self.assertTrue((root / "artifacts/report.json").is_file())
            self.assertIn("Repository Health Report", output.getvalue())

    def test_cli_rejects_json_output_outside_selected_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory).resolve()
            error = StringIO()

            with redirect_stderr(error):
                status = main([str(root), "--json-output", "../report.json"])

            self.assertEqual(2, status)
            self.assertIn("must stay within", error.getvalue())


if __name__ == "__main__":
    unittest.main()
