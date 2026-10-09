---
name: codex-core-maintenance
description: Use when changing codex-core public modules, packaging, release notes, or its consumer skill and offline installer in this source repository.
---

# codex-core maintenance

This repository is the canonical source of the `codex-core` Python package. Package metadata and build rules are in `pyproject.toml`; public code is under `src/codex_core`. The packaged consumer skill source is `src/codex_core/agent_skills/resources/`. Consumer installations under `.agents/skills/codex-core/` are generated, manifest-owned copies. Edit source here, not a consumer copy or its `.manifest.json`.

For API changes, keep the skill references aligned with shipped public imports and behavior. `BaseDTO` freezes Pydantic fields and masks its string representation; it does not sanitize `model_dump()`. A `PIIRegistry` subclass globally replaces heuristic matching with exact names, so partial declarations affect all DTOs in the process. `BaseCommonSettings` intentionally omits an env-file path and defaults to `debug=True`. `codex_core.common` exposes normalization and logging helpers; Loguru configuration requires the optional extra and is application-owned.

The offline installer entrypoint is `python -m codex_core.agent_skills {install,update,delete,status} --project PATH`. It writes only its manifest-owned skill files and marked `AGENTS.md` block. Preserve unrelated project text and files byte-for-byte. Refuse malformed manifests, symlinks/reparse points, collisions, and changed managed files before mutations; retain rollback protection for ordinary I/O errors. Changes to installer behavior need lifecycle tests and an isolated install from a built artifact.

Before implementation, read the repository `AGENTS.md` and graph report/index as instructed there. From the repository root, relevant checks are `python -m pytest -q`, `python -m ruff check src tests`, `python -m mypy src/codex_core`, and `uv build --no-sources`; use the project's environment where those commands are installed. For package changes, inspect wheel contents and perform an isolated consumer install/update/status/delete from the built wheel. After code changes, run `graphify update .` from the workspace root as `AGENTS.md` directs. Update `CHANGELOG.md` without inventing a release date. Do not commit, tag, or publish as part of ordinary maintenance; those actions belong to the release workflow.
