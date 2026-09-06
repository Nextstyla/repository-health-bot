# Project Conventions

## Code
- Use snake_case for Python files, functions, and variables.
- Use PascalCase for classes.
- Keep checks deterministic, small, and standard-library-only.
- Add unit tests for every check.

## Safety
- Never scan or write outside the selected project root.
- Never commit secrets, tokens, credentials, or private repository data.
- Never auto-merge, publish, deploy, delete, or alter GitHub settings without explicit approval.
- Always run format, lint, and tests before forward work.
- Do not bypass a failed quality or security gate.

## Resilience
- Apply a timeout to subprocess checks.
- Report one failed optional check without stopping unrelated checks.

## Git
- Use Conventional Commit messages.
- Keep generated reports as CI artifacts, not tracked files.
