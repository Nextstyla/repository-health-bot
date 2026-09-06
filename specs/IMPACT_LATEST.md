# Impact Assessment - Secure Dependency Maintenance Lab

## Target

- New `.github/dependabot.yml` configuration.
- New `.github/workflows/codeql.yml` security-analysis workflow.
- README documentation for dependency maintenance and code scanning.

## Dependents (2)

- `.github/workflows/ci.yml`: validates pull requests that Dependabot will create.
- `.github/workflows/weekly-health.yml`: already performs scheduled `pip-audit`; it remains unchanged and provides complementary dependency evidence.

## Affected Stories

No release-plan stories are defined. This is the initial secure-dependency-maintenance learning slice.

## Test Coverage

- `tests/test_checks.py`: local health-check behavior only; unaffected.
- `tests/test_report.py`: report rendering and output containment only; unaffected.
- Gap: GitHub-hosted Dependabot and CodeQL execution cannot be tested locally. YAML structure and least-privilege permissions can be validated locally.

## Risk: Low

The change adds isolated read-only GitHub configuration. It does not change application code, local report behavior, deployment behavior, package publishing, or repository settings.

## Recommended action

Proceed with a small configuration-only implementation: Dependabot weekly Python and GitHub Actions updates, a read-only CodeQL workflow for Python and Actions, and beginner-oriented documentation. Review pull requests and security findings manually; do not enable auto-merge.
