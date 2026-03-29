<!-- Type: ISSUE/DRAFT -->
# Python Version Policy Note

Status: draft

## Context

`codex-core` currently declares `requires-python = ">=3.12"` in
`pyproject.toml` and advertises Python 3.12 / 3.13 classifiers.

This note exists as an internal planning record for future Python-version
expansion work. It is intentionally kept outside the public navigation.

## Current State

- Runtime requirement: Python 3.12+
- Declared classifiers: Python 3.12, Python 3.13
- CI and publish workflows should stay aligned with the supported versions

## When to update

Update this note when one of the following changes is planned:

1. Add a new officially supported Python version.
2. Raise the minimum supported Python version.
3. Expand CI, docs, or publish matrices to new versions.

## Checklist

- [ ] Update `project.requires-python` in `pyproject.toml` if support policy changes.
- [ ] Update `classifiers` in `pyproject.toml`.
- [ ] Update Python-version matrices in `.github/workflows/ci.yml`.
- [ ] Update Python-version matrices in `.github/workflows/docs.yml`.
- [ ] Update Python-version matrices in `.github/workflows/publish.yml`.
- [ ] Reflect the new policy in user-facing docs only after CI is updated.
