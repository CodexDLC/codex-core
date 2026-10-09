<!-- Type: GUIDE -->
[🏠 Home](../../index.md) | [🧭 Guide (EN)](../README.md) | [🚀 Getting Started](getting_started.md)

# Optional agent skill

Starting with `codex-core` 0.5.0, the Python package includes an offline usage skill for coding agents. Install the package in the Python environment you will use for the commands below, then run these commands from your consumer project root:

```bash
python -m pip install "codex-core>=0.5.0"
python -m codex_core.agent_skills install --project .
python -m codex_core.agent_skills status --project .
```

The installer creates `.agents/skills/codex-core/` with a version/hash manifest and adds a marked instruction to `AGENTS.md`. The copy and manifest are managed by the package. Keep application-specific rules in your own project skill or outside the marked block.

Updating the Python package and refreshing the installed skill are separate steps:

```bash
python -m pip install --upgrade codex-core
python -m codex_core.agent_skills update --project .
python -m codex_core.agent_skills status --project .
```

To remove only installer-owned content, run `python -m codex_core.agent_skills delete --project .`. `install` is safe to repeat when current, and `delete` succeeds when the skill is already absent. `status` exits with code 0 only when the skill is installed and current; it exits with code 1 when absent, outdated, or damaged. The other commands exit with code 1 on an error.

Update and delete refuse to discard changed managed files. Installation also refuses to take over an existing unowned destination or overwrite a colliding file. If a command reports local changes, save them in a project-owned skill, restore the managed files or marked block from a trusted backup of the installed version, and retry. Do not edit the manifest to make changes appear managed, or manually remove the destination to force an update. Unrelated `AGENTS.md` text and unowned files are preserved.
