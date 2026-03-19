# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-02-13

### Added
- **Python 3.13 Support**: Added official support for Python 3.13 in `pyproject.toml` classifiers.
- **Comprehensive Unit Tests**:
  - New tests for `core/exceptions.py` covering base exception functionality.
  - New tests for `common/log_context.py` covering `TaskLogContext` logging methods.
  - New tests for `common/loguru_setup.py` covering `InterceptHandler`, `setup_universal_logging`, and `setup_logging` with and without `loguru` installed.

### Changed
- **Documentation Structure**:
  - Renamed top-level language directories from `en_EN/` to `en/` and `ru_RU/` to `ru/`.
  - Moved `api/` documentation into `en/api/` for better language-specific grouping.
  - Renamed `guide/` directories to `tasks/` in both `en/` and `ru/` to align with `DocArchitect:StructurePolicy` for user-oriented guides.
  - Updated `mkdocs.yml` navigation and all internal Markdown links to reflect the new documentation structure.
  - Updated root `README.md` to strictly follow `DocArchitect:StructurePolicy` (Layer 5 - Root Landing), including a detailed `Modules` table (with `dev` module) and a comprehensive `Part of the Codex ecosystem` section.
- **Test Coverage Configuration**:
  - Configured `pytest-cov` in `pyproject.toml` to include `addopts`, `[tool.coverage.run]`, and `[tool.coverage.report]` sections.
  - Excluded `src/codex_core/dev/*` from coverage reports as these are internal development tools.
  - Added `exclude_lines` for `TYPE_CHECKING` and `ImportError` to achieve accurate coverage metrics.
- **Test Isolation**: Implemented `autouse` fixture `reset_pii_registry` in `tests/conftest.py` to ensure `PIIRegistry` global state is reset between tests, guaranteeing test isolation.
- **Test Markers**: Created `tests/unit/conftest.py` and `tests/integration/conftest.py` to automatically apply `pytest.mark.unit` and `pytest.mark.integration` markers to tests within their respective directories.

### Fixed
- **Mypy Errors**: Resolved missing type parameters for generic types in `src/codex_core/dev/static_compiler/compiler.py` and `src/codex_core/dev/static_compiler/css.py`.
- **Ruff Errors**: Resolved `SIM118` (Use `key in dict` instead of `key in dict.keys()`) in `src/codex_core/core/pii.py`.
- **Ruff Errors**: Resolved `SIM117` (Use a single `with` statement with multiple contexts) in `tests/unit/common/test_loguru_setup.py`.
- **Test Coverage Gaps**:
  - Covered `PIIRegistry` initialization logic and recursive list masking in `tests/unit/core/test_pii.py`.
  - Covered falsy input handling in `transliterate` and `sanitize_for_sms` functions in `tests/unit/common/test_text.py`.

## [0.1.1] - 2025-02-12

### Added
- **Declarative PII Registry**: Introduced `PIIRegistry` class in `pii.py` for explicit sensitive field name tracking, complementing the heuristic keyword-based matching.
- **Enhanced Documentation**:
  - Comprehensive Google-style docstrings added to all core modules: `log_context`, `loguru_setup`, `phone`, `text`, `base_dto`, `exceptions`, and `settings/base`.
  - Added localized (EN/RU) documentation links and PyPI/License badges to `README.md`.
- **Dependency Management**: Added `loguru` as an explicit optional dependency in `pyproject.toml`.

### Changed
- **PII Masking Logic**: Refined `is_pii_field` and `mask_value` to prioritize explicit registry matches over heuristic keyword search.
- **Project Configuration**: Updated `.gitignore` to include `.claude/` for modern AI tool support.

## [0.1.0] - 2024-05-24

### Added
- **Project Structure**: Initial setup of the core library as a standalone project.
- **Advanced PII Protection**:
  - Implementation of `BaseDTO` with automated, recursive PII masking in `repr` and `str`.
  - Keyword-based sensitive data detection (phone, email, name, address, notes).
- **International Utilities**:
  - `normalize_phone`: Robust normalization supporting `+`, `00`, and local German `0` formats.
  - `normalize_name`: Smart capitalization preserving hyphens and spaces.
  - `TaskLogContext`: Structured logging adapter for background tasks and operations.
- **Base Settings**: `BaseCommonSettings` with standardized Redis URL generation and environment-aware flags.
- **Documentation**:
  - New Domain-Driven documentation standard (Architecture + API Reference).
  - Bilingual support (EN/RU) with structural mirroring.
- **Testing**:
  - Comprehensive unit test suite (27 scenarios) covering Core, Common, and Settings.
  - Integration test for environment variable loading.

### Changed
- **Package Rename**: Renamed package from `codex_tools` to `codex_core` for better clarity.
- **Dependency Optimization**:
  - `loguru` removed from mandatory dependencies.
  - `loguru_setup` updated with safe imports and clear installation instructions.
- **CI/CD**:
  - Switched GitHub Actions to use Node.js 24 (via `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24`).
  - Updated Mypy paths to reflect the new package structure.

### Security
- Integrated `bandit`, `pip-audit`, and `detect-secrets` into the development lifecycle.
- Standardized `quote_plus` usage for all infrastructure connection strings.
