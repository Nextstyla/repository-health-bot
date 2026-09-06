# Repository Health Bot

Read `CONVENTIONS.md` before changing this project.

## Project
A local-only Python repository health reporter.

## Commands
| Action | Command |
| --- | --- |
| Run | `python -m repository_health_bot` |
| Test | `python -m unittest discover --verbose` |
| Lint | `ruff check .` |
| Format | `ruff format --check .` |
| Preflight | `ruff format --check . && ruff check . && python -m unittest discover --verbose` |

## Rules
- Read `specs/` before major changes.
- Add tests for every new health check.
- Never scan outside the selected root.
- Never publish, deploy, merge, or change GitHub settings without approval.
