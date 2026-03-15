# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-05-24

### Added
- **Project Structure**: Initial setup of the core library as a standalone project.
- **Core Modules**:
  - `codex_tools.common`: Cache, logging, text and phone utilities.
  - `codex_tools.core`: Base DTOs, interfaces, exceptions and PII utilities.
  - `codex_tools.schemas`: Standard response schemas.
  - `codex_tools.settings`: Base configuration management using `pydantic-settings`.
- **Infrastructure**:
  - `pyproject.toml` with Hatchling build-system and Ruff/Mypy support.
  - Pre-commit hooks for security and code quality.
  - GitHub Actions workflows for CI, Docs and Publishing.
  - MkDocs documentation skeleton.

### Changed
- **Python Support**: Downgraded minimum Python requirement to `3.10+` for broader compatibility.
- **Repository Split**: Formally split from the monolithic `codex_tools` repository into 4 focused projects (core, bot, cli, sdk).

### Security
- Integrated `bandit`, `pip-audit`, and `detect-secrets` into the development lifecycle.
