"""
Declarative quality gate runner shared by codex-* projects.

Projects are expected to describe their checker policy in ``pyproject.toml``
under ``[tool.codex-check]``. The runner still supports legacy subclass
attributes as defaults so repositories can migrate incrementally.
"""

from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
import sys
import tomllib
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


@dataclass(frozen=True)
class ExtraCommand:
    name: str
    command: list[str]
    skip_if_missing: str | None = None


@dataclass(frozen=True)
class CheckRunnerConfig:
    project_name: str
    audit_flags: str
    integration_requires: str
    e2e_requires: str | None
    run_lint: bool
    run_types: bool
    run_security: bool
    run_extra_checks: bool
    test_stages: list[str]
    prompt_test_stages: list[str]
    allow_empty_test_stages: set[str] = field(default_factory=set)
    no_cov_test_stages: set[str] = field(default_factory=set)
    live_output_test_stages: set[str] = field(default_factory=set)
    test_paths: list[str] = field(default_factory=lambda: ["tests"])
    test_markers: dict[str, str] = field(default_factory=dict)
    types_paths: list[str] = field(default_factory=lambda: ["src"])
    quality_command: list[str] | None = None
    types_command: list[str] | None = None
    security_command: list[str] | None = None
    extra_commands: list[ExtraCommand] = field(default_factory=list)


class BaseCheckRunner:
    """Base quality gate runner."""

    PROJECT_NAME: str = "project"
    AUDIT_FLAGS: str = "--skip-editable"
    INTEGRATION_REQUIRES: str = "external services"
    E2E_REQUIRES: str | None = None
    RUN_LINT: bool = True
    RUN_TYPES: bool = True
    RUN_SECURITY: bool = True
    RUN_EXTRA_CHECKS: bool = True
    RUN_UNIT_TESTS: bool = True
    RUN_INTEGRATION_TESTS: bool = True

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root.resolve()
        self.src_dir = self.project_root / "src"
        self.tests_dir = self.project_root / "tests"
        self.pyproject_path = self.project_root / "pyproject.toml"
        self.config = self._load_config()

    def _load_config(self) -> CheckRunnerConfig:
        raw_config = self._read_pyproject_config()
        legacy_stages = self._legacy_test_stages()
        legacy_prompt_stages = ["integration"] if "integration" in legacy_stages else []
        test_stages = self._dedupe(
            self._get_list(raw_config, "test-stages") or self._get_list(raw_config, "test_stages") or legacy_stages
        )
        prompt_test_stages = self._dedupe(
            self._get_list(raw_config, "prompt-test-stages")
            or self._get_list(raw_config, "prompt_test_stages")
            or legacy_prompt_stages
        )
        prompt_test_stages = [stage for stage in prompt_test_stages if stage in test_stages]

        quality_command = self._normalize_command(
            raw_config.get("quality-command") or raw_config.get("quality_command")
        )
        types_command = self._normalize_command(raw_config.get("types-command") or raw_config.get("types_command"))
        security_command = self._normalize_command(
            raw_config.get("security-command") or raw_config.get("security_command")
        )

        extra_commands: list[ExtraCommand] = []
        for item in raw_config.get("extra-commands", []):
            if not isinstance(item, dict):
                continue
            name = str(item.get("name", "")).strip()
            command = self._normalize_command(item.get("command"))
            if not name or not command:
                continue
            skip_if_missing = item.get("skip-if-missing") or item.get("skip_if_missing")
            extra_commands.append(
                ExtraCommand(
                    name=name, command=command, skip_if_missing=str(skip_if_missing) if skip_if_missing else None
                )
            )

        return CheckRunnerConfig(
            project_name=str(raw_config.get("project-name") or raw_config.get("project_name") or self.PROJECT_NAME),
            audit_flags=str(raw_config.get("audit-flags") or raw_config.get("audit_flags") or self.AUDIT_FLAGS),
            integration_requires=str(
                raw_config.get("integration-requires")
                or raw_config.get("integration_requires")
                or self.INTEGRATION_REQUIRES
            ),
            e2e_requires=self._optional_str(
                raw_config.get("e2e-requires") or raw_config.get("e2e_requires") or self.E2E_REQUIRES
            ),
            run_lint=self._get_bool(raw_config, "run-lint", self.RUN_LINT),
            run_types=self._get_bool(raw_config, "run-types", self.RUN_TYPES),
            run_security=self._get_bool(raw_config, "run-security", self.RUN_SECURITY),
            run_extra_checks=self._get_bool(raw_config, "run-extra-checks", self.RUN_EXTRA_CHECKS),
            test_stages=test_stages,
            prompt_test_stages=prompt_test_stages,
            allow_empty_test_stages=set(
                self._get_list(raw_config, "allow-empty-test-stages")
                or self._get_list(raw_config, "allow_empty_test_stages")
            ),
            no_cov_test_stages=set(
                self._get_list(raw_config, "no-cov-test-stages") or self._get_list(raw_config, "no_cov_test_stages")
            ),
            live_output_test_stages=set(
                self._get_list(raw_config, "live-output-test-stages")
                or self._get_list(raw_config, "live_output_test_stages")
            ),
            test_paths=self._get_list(raw_config, "test-paths")
            or self._get_list(raw_config, "test_paths")
            or ["tests"],
            test_markers=self._get_dict(raw_config, "test-markers") or self._get_dict(raw_config, "test_markers"),
            types_paths=self._get_list(raw_config, "types-paths")
            or self._get_list(raw_config, "types_paths")
            or ["src"],
            quality_command=quality_command,
            types_command=types_command,
            security_command=security_command,
            extra_commands=extra_commands,
        )

    def _read_pyproject_config(self) -> dict[str, Any]:
        if not self.pyproject_path.exists():
            return {}
        with self.pyproject_path.open("rb") as fh:
            data = tomllib.load(fh)
        tool = data.get("tool", {})
        section = tool.get("codex-check", {})
        return section if isinstance(section, dict) else {}

    def _legacy_test_stages(self) -> list[str]:
        stages: list[str] = []
        if self.RUN_UNIT_TESTS:
            stages.append("unit")
        if self.RUN_INTEGRATION_TESTS:
            stages.append("integration")
        return stages

    @staticmethod
    def _dedupe(values: Sequence[str]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []
        for value in values:
            if value not in seen:
                seen.add(value)
                result.append(value)
        return result

    @staticmethod
    def _optional_str(value: Any) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None

    @staticmethod
    def _get_bool(raw_config: dict[str, Any], key: str, default: bool) -> bool:
        alt_key = key.replace("-", "_")
        value = raw_config.get(key, raw_config.get(alt_key, default))
        return bool(value)

    @staticmethod
    def _get_list(raw_config: dict[str, Any], key: str) -> list[str]:
        value = raw_config.get(key)
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [str(item) for item in value]
        return []

    @staticmethod
    def _get_dict(raw_config: dict[str, Any], key: str) -> dict[str, str]:
        value = raw_config.get(key)
        if not isinstance(value, dict):
            return {}
        return {str(dict_key): str(dict_value) for dict_key, dict_value in value.items()}

    @staticmethod
    def _normalize_command(value: Any) -> list[str] | None:
        if value is None:
            return None
        if isinstance(value, list):
            return [str(item) for item in value]
        if isinstance(value, str):
            return shlex.split(value)
        return None

    def print_step(self, msg: str) -> None:
        print(f"\n{Colors.YELLOW}🔍 {msg}...{Colors.ENDC}", flush=True)

    def print_success(self, msg: str) -> None:
        print(f"{Colors.GREEN}✅ {msg}{Colors.ENDC}", flush=True)

    def print_error(self, msg: str) -> None:
        print(f"{Colors.RED}❌ {msg}{Colors.ENDC}", flush=True)

    def print_skip(self, msg: str) -> None:
        print(f"{Colors.BLUE}⏭ {msg}{Colors.ENDC}", flush=True)

    def run_command(
        self,
        command: Sequence[str] | str,
        *,
        capture_output: bool = False,
        env: dict[str, str] | None = None,
    ) -> tuple[bool, str]:
        try:
            if isinstance(command, str):
                result = subprocess.run(
                    command,
                    cwd=self.project_root,
                    shell=True,
                    check=False,
                    text=True,
                    capture_output=capture_output,
                    env=env,
                )
            else:
                result = subprocess.run(
                    list(command),
                    cwd=self.project_root,
                    shell=False,  # nosec B603
                    check=False,
                    text=True,
                    capture_output=capture_output,
                    env=env,
                )
            return result.returncode == 0, result.stdout or result.stderr or ""
        except Exception as exc:  # pragma: no cover - defensive
            return False, str(exc)

    def _expand_command(self, command: Sequence[str]) -> list[str]:
        mapping = {
            "{python}": sys.executable,
            "{project_root}": str(self.project_root),
            "{src}": str(self.src_dir),
            "{tests}": str(self.tests_dir),
        }
        expanded: list[str] = []
        for part in command:
            expanded.append(mapping.get(part, part))
        return expanded

    def _default_quality_command(self) -> list[str]:
        return [sys.executable, "-m", "pre_commit", "run", "--all-files"]

    def _default_types_command(self) -> list[str]:
        command = [sys.executable, "-m", "mypy"]
        command.extend(self.config.types_paths)
        return command

    def _default_security_command(self) -> list[str]:
        command = [sys.executable, "-m", "pip_audit"]
        if self.config.audit_flags:
            command.extend(shlex.split(self.config.audit_flags))
        return command

    def check_quality(self) -> bool:
        self.print_step("Running Quality Hooks")
        command = self._expand_command(self.config.quality_command or self._default_quality_command())
        success, out = self.run_command(command, capture_output=False)
        if not success:
            self.print_error("Quality hooks failed.")
            return False
        self.print_success("Quality hooks passed.")
        return True

    def check_types(self) -> bool:
        self.print_step("Checking Types (Mypy)")
        command = self._expand_command(self.config.types_command or self._default_types_command())
        success, out = self.run_command(command, capture_output=False)
        if not success:
            self.print_error("Mypy check failed.")
        else:
            self.print_success("Mypy check passed.")
        return success

    def check_security(self) -> bool:
        self.print_step("Security Audit (pip-audit)")
        command = self._expand_command(self.config.security_command or self._default_security_command())
        success, out = self.run_command(command, capture_output=False)
        if not success:
            self.print_error("Security audit failed.")
        else:
            self.print_success("Security audit passed.")
        return success

    def _resolved_test_paths(self) -> list[str]:
        resolved: list[str] = []
        for raw_path in self.config.test_paths:
            path = Path(raw_path)
            if not path.is_absolute():
                path = self.project_root / path
            if path.exists():
                resolved.append(str(path))
        return resolved

    def _test_command(self, stage: str) -> list[str]:
        command = [sys.executable, "-m", "pytest", *self._resolved_test_paths()]
        marker = self.config.test_markers.get(stage, stage)
        if marker:
            command.extend(["-m", marker])
        command.extend(["-v", "--tb=short"])
        if stage in self.config.no_cov_test_stages:
            command.append("--no-cov")
        if stage in self.config.live_output_test_stages:
            command.append("-s")
        return command

    @staticmethod
    def _is_empty_test_selection(output: str) -> bool:
        normalized = output.lower()
        return "0 selected" in normalized or "no tests ran" in normalized or "collected 0 items" in normalized

    def run_tests(self, stage: str = "unit") -> bool:
        if stage not in self.config.test_stages:
            self.print_skip(f"Skipping {stage} tests (stage not configured).")
            return True

        test_paths = self._resolved_test_paths()
        if not test_paths:
            self.print_skip(f"Skipping {stage} tests (no configured test paths found).")
            return True

        self.print_step(f"Running {stage.capitalize()} Tests")
        capture_output = stage not in self.config.live_output_test_stages
        success, out = self.run_command(self._test_command(stage), capture_output=capture_output)
        if not success and stage in self.config.allow_empty_test_stages and self._is_empty_test_selection(out):
            self.print_success(f"No {stage} tests collected; skipping.")
            return True
        if success:
            self.print_success(f"{stage.capitalize()} tests passed.")
        else:
            self.print_error(f"{stage.capitalize()} tests failed.")
        return success

    def _run_declared_extra_commands(self) -> bool:
        for item in self.config.extra_commands:
            self.print_step(item.name)
            if item.skip_if_missing and shutil.which(item.skip_if_missing) is None:
                self.print_skip(f"Skipping {item.name} ({item.skip_if_missing} not installed).")
                continue
            success, out = self.run_command(self._expand_command(item.command), capture_output=False)
            if not success:
                self.print_error(f"{item.name} failed.")
                return False
            self.print_success(f"{item.name} passed.")
        return True

    def extra_checks(self) -> bool:
        return self._run_declared_extra_commands()

    def _clear_screen(self) -> None:
        if os.name == "nt":
            os.system("cls")
        else:
            os.system("clear")

    def _stage_requirement(self, stage: str) -> str | None:
        if stage == "integration":
            return self.config.integration_requires
        if stage == "e2e":
            return self.config.e2e_requires
        return None

    def _prompt_for_stage(self, stage: str) -> bool:
        requirement = self._stage_requirement(stage)
        label = stage.upper() if stage == "e2e" else stage.capitalize()
        suffix = f" (Requires: {requirement})" if requirement else ""
        prompt = f"\n{Colors.YELLOW}🚀 Run {label} Tests?{suffix} [y/N]: {Colors.ENDC}"
        try:
            answer = input(prompt).strip().lower()
        except EOFError:
            answer = "n"
            print("n")
        return answer == "y"

    def _run_auto_test_stages(self) -> bool:
        for stage in self.config.test_stages:
            if stage in self.config.prompt_test_stages:
                continue
            if not self.run_tests(stage):
                return False
        return True

    def _run_prompted_test_stages(self) -> bool:
        for stage in self.config.test_stages:
            if stage not in self.config.prompt_test_stages:
                continue
            if self._prompt_for_stage(stage) and not self.run_tests(stage):
                return False
        return True

    def run_all(self) -> None:
        self._clear_screen()
        print(f"{Colors.HEADER}{Colors.BOLD}=== {self.config.project_name} quality gate ==={Colors.ENDC}")

        if self.config.run_lint and not self.check_quality():
            sys.exit(1)
        if not self.config.run_lint:
            self.print_skip("Skipping quality hooks.")

        if self.config.run_types and not self.check_types():
            sys.exit(1)
        if not self.config.run_types:
            self.print_skip("Skipping type checks.")

        if self.config.run_security and not self.check_security():
            sys.exit(1)
        if not self.config.run_security:
            self.print_skip("Skipping security audit.")

        if self.config.run_extra_checks and not self.extra_checks():
            sys.exit(1)
        if not self.config.run_extra_checks:
            self.print_skip("Skipping extra checks.")

        if not self._run_auto_test_stages():
            sys.exit(1)
        if not self._run_prompted_test_stages():
            sys.exit(1)

        print(f"\n{Colors.GREEN}{Colors.BOLD}ALL CHECKS PASSED!{Colors.ENDC}")

    def run_ci(self) -> None:
        print(f"{Colors.HEADER}{Colors.BOLD}=== {self.config.project_name} CI gate ==={Colors.ENDC}")
        results: list[bool] = []

        if self.config.run_lint:
            results.append(self.check_quality())
        else:
            self.print_skip("Skipping quality hooks.")

        if self.config.run_types:
            results.append(self.check_types())
        else:
            self.print_skip("Skipping type checks.")

        if self.config.run_security:
            results.append(self.check_security())
        else:
            self.print_skip("Skipping security audit.")

        if self.config.run_extra_checks:
            results.append(self.extra_checks())
        else:
            self.print_skip("Skipping extra checks.")

        for stage in self.config.test_stages:
            results.append(self.run_tests(stage))

        if not all(results):
            sys.exit(1)

        print(f"\n{Colors.GREEN}{Colors.BOLD}ALL CHECKS PASSED!{Colors.ENDC}")

    def main(self) -> None:
        parser = argparse.ArgumentParser(description=f"{self.config.project_name} quality gate")
        parser.add_argument("--all", action="store_true", help="Run all checks (prompts for optional stages)")
        parser.add_argument("--ci", action="store_true", help="Run all checks non-interactively")
        parser.add_argument("--lint", action="store_true", help="Run quality hooks")
        parser.add_argument("--types", action="store_true", help="Run mypy")
        parser.add_argument("--security", action="store_true", help="Run pip-audit")
        parser.add_argument("--tests", help="Run a configured test stage or 'all'")

        args = parser.parse_args()

        if args.ci:
            self.run_ci()
            return
        if args.all:
            self.run_all()
            return
        if args.lint:
            if not self.config.run_lint:
                self.print_skip("Quality hooks are disabled.")
                raise SystemExit(0)
            raise SystemExit(0 if self.check_quality() else 1)
        if args.types:
            if not self.config.run_types:
                self.print_skip("Type checks are disabled.")
                raise SystemExit(0)
            raise SystemExit(0 if self.check_types() else 1)
        if args.security:
            if not self.config.run_security:
                self.print_skip("Security checks are disabled.")
                raise SystemExit(0)
            raise SystemExit(0 if self.check_security() else 1)
        if args.tests:
            if args.tests == "all":
                success = all(self.run_tests(stage) for stage in self.config.test_stages)
                raise SystemExit(0 if success else 1)
            if args.tests not in self.config.test_stages:
                parser.error(
                    f"unknown test stage '{args.tests}'. configured stages: {', '.join(self.config.test_stages)}"
                )
            raise SystemExit(0 if self.run_tests(args.tests) else 1)

        parser.print_help()
