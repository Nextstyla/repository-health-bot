# Repository Health Bot

A local-first Python learning project that checks basic repository health and creates a Markdown/JSON report. It teaches GitHub Actions, artifacts, scheduled workflows, dependency auditing, and quality gates without hosting an application or buying a subscription.

## What it checks

- A README at the selected root.
- A conventional license file at the selected root.
- The number of Python files below the selected root.
- Local Markdown links below the selected root.
- Optional `pip-audit` results for `requirements*.txt` below the selected root.

The bot never follows Markdown URLs, skips symlinks, and rejects report output outside the selected root. Its own checks use only the Python standard library. `--audit` explicitly starts the installed `pip-audit` command; that third-party tool may query vulnerability data for the selected local requirement files.

## Local setup

In PowerShell:

```powershell
cd C:\Users\mario\repository-health-bot
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --require-hashes --requirement requirements.tools.txt
```

`requirements.tools.in` records the direct tool choices. `requirements.tools.txt` is generated with `pip-compile --generate-hashes` and pins every transitive dependency and approved package hash. `--require-hashes` rejects substituted package files.

## Run a report

Run against the current directory:

```powershell
python -m repository_health_bot
```

Run against one chosen project and write JSON inside that same project:

```powershell
python -m repository_health_bot C:\path\to\project --json-output artifacts\health-report.json
```

Add the optional dependency audit:

```powershell
python -m repository_health_bot . --audit --audit-timeout 30 --json-output artifacts\health-report.json
```

Markdown is always printed to the terminal. JSON is written only when `--json-output` is used. Generated `artifacts/` files are ignored by Git.

## Quality commands

```powershell
python -m unittest discover --verbose
ruff check .
ruff format --check .
python -m pip_audit --requirement requirements.tools.txt --require-hashes
```

There is no build step because this is a standard-library Python application.

## GitHub Actions

`.github/workflows/ci.yml` runs on pushes and pull requests. It installs the hash-locked tools, checks formatting and linting, runs unit tests, audits dependencies, generates a local health report, and uploads the report as a 14-day artifact. It has only `contents: read` permission.

`.github/workflows/weekly-health.yml` runs every Monday at 09:00 UTC and can also be started manually. It produces an artifact even when the repository code is unchanged, which helps detect newly disclosed dependency vulnerabilities or documentation drift.

The workflows use full commit-SHA-pinned actions. They do not write repository content, publish packages, deploy software, use secrets, or require server hosting.

## Secure dependency maintenance

`.github/dependabot.yml` asks GitHub's Dependabot service to check two dependency ecosystems every Monday:

- `pip` checks the pinned Python quality tools in `requirements.tools.in` and `requirements.tools.txt`.
- `github-actions` checks the action versions used in `.github/workflows/`.

When an update exists, Dependabot opens a pull request instead of changing `main` directly. The existing **Repository Quality** workflow then tests that pull request. Review the version change, lock-file diff, CI result, and any release notes before merging. This project deliberately does not enable automatic merging: a passing automated check is evidence, not a substitute for human judgment.

`.github/workflows/codeql.yml` provides separate security analysis for Python and GitHub Actions workflow configuration. It runs on pushes, pull requests, every Wednesday at 04:30 UTC, and manual dispatch. CodeQL uploads findings to GitHub's **Security** tab. Its only write permission is `security-events: write`, which is required to submit findings; it cannot write repository content, publish packages, or deploy software.

## Why this project is local-first

CI quality gates are useful before any infrastructure exists. You can learn how a fresh GitHub runner validates a commit, how reports become artifacts, and how scheduled maintenance works without exposing an application or paying for a VPS.

## Safety boundaries

Never provide a path that includes private content you do not intend to inspect. The tool operates only below the directory you select. It does not follow symlinks or Markdown URLs. Do not auto-merge bot pull requests, publish releases, deploy servers, or delete artifacts without explicit review.
