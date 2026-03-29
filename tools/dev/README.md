<!-- Type: REFERENCE -->
# Development & Validation Tools

This directory contains scripts to ensure code quality and environment consistency.

## `check.py`
The primary quality gate for the project. It wraps the shared `BaseCheckRunner`
from `codex_core.dev` and runs the checks enabled by the local project config.

### Usage
- Full check: `uv run python tools/dev/check.py --all`
- CI mode: `uv run python tools/dev/check.py --ci`
- Lint only: `uv run python tools/dev/check.py --lint`
- Types only: `uv run python tools/dev/check.py --types`
- Security only: `uv run python tools/dev/check.py --security`
- Unit tests only: `uv run python tools/dev/check.py --tests unit`
- Integration tests only: `uv run python tools/dev/check.py --tests integration`
- All tests: `uv run python tools/dev/check.py --tests all`

### Features
- Linting via `pre-commit run --all-files`
- Type checking via `sys.executable -m mypy src`
- Security audit via `pip-audit`
- Unit and integration test entry points via `pytest -m ...`
- Optional project-specific `extra_checks()` hook

### Project-level flags
`tools/dev/check.py` can enable or disable standard steps through boolean class attributes:

- `RUN_LINT`
- `RUN_TYPES`
- `RUN_SECURITY`
- `RUN_EXTRA_CHECKS`
- `RUN_UNIT_TESTS`
- `RUN_INTEGRATION_TESTS`

This lets each codex-* project treat the shared runner as a base and declare
its own quality gate policy without forking the orchestration logic.

## `generate_project_tree.py`
Generates a visual representation of the project structure for documentation purposes.
