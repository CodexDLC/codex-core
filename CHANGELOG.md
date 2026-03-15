# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
