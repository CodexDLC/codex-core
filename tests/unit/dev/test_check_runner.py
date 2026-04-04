from pathlib import Path

from codex_core.dev.check_runner import BaseCheckRunner


class DummyRunner(BaseCheckRunner):
    pass


def test_check_runner_loads_pyproject_configuration(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.codex-check]
project-name = "demo-project"
audit-flags = "--skip-editable --ignore-vuln CVE-TEST"
integration-requires = "Redis"
e2e-requires = "Filesystem"
test-stages = ["unit", "integration", "e2e"]
prompt-test-stages = ["integration", "e2e"]
allow-empty-test-stages = ["integration"]
no-cov-test-stages = ["integration", "e2e"]
live-output-test-stages = ["e2e"]
test-paths = ["tests/unit", "tests/e2e"]
types-paths = ["src", "examples"]

[tool.codex-check.test-markers]
unit = ""
integration = "integration"
e2e = "e2e"

[[tool.codex-check.extra-commands]]
name = "Docker Lint"
command = ["hadolint", "Dockerfile"]
skip-if-missing = "hadolint"
        """.strip(),
        encoding="utf-8",
    )

    runner = DummyRunner(tmp_path)

    assert runner.config.project_name == "demo-project"
    assert runner.config.audit_flags == "--skip-editable --ignore-vuln CVE-TEST"
    assert runner.config.e2e_requires == "Filesystem"
    assert runner.config.test_stages == ["unit", "integration", "e2e"]
    assert runner.config.prompt_test_stages == ["integration", "e2e"]
    assert runner.config.allow_empty_test_stages == {"integration"}
    assert runner.config.no_cov_test_stages == {"integration", "e2e"}
    assert runner.config.live_output_test_stages == {"e2e"}
    assert runner.config.test_paths == ["tests/unit", "tests/e2e"]
    assert runner.config.types_paths == ["src", "examples"]
    assert runner.config.test_markers == {"unit": "", "integration": "integration", "e2e": "e2e"}
    assert runner.config.extra_commands[0].command == ["hadolint", "Dockerfile"]


def test_check_runner_builds_test_command_from_stage_configuration(tmp_path: Path) -> None:
    (tmp_path / "tests" / "cabinet").mkdir(parents=True)
    (tmp_path / "pyproject.toml").write_text(
        """
[tool.codex-check]
project-name = "demo-project"
test-stages = ["unit", "e2e"]
test-paths = ["tests/cabinet"]
no-cov-test-stages = ["e2e"]
live-output-test-stages = ["e2e"]

[tool.codex-check.test-markers]
unit = ""
e2e = "e2e"
        """.strip(),
        encoding="utf-8",
    )

    runner = DummyRunner(tmp_path)

    assert runner._test_command("unit") == [
        runner._expand_command(["{python}"])[0],
        "-m",
        "pytest",
        str(tmp_path / "tests" / "cabinet"),
        "-v",
        "--tb=short",
    ]
    assert runner._test_command("e2e") == [
        runner._expand_command(["{python}"])[0],
        "-m",
        "pytest",
        str(tmp_path / "tests" / "cabinet"),
        "-m",
        "e2e",
        "-v",
        "--tb=short",
        "--no-cov",
        "-s",
    ]
