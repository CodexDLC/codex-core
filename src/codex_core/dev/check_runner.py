"""
BaseCheckRunner — universal quality gate base class for all codex-* projects.

Usage in a project's tools/dev/check.py:

    from pathlib import Path
    from codex_core.dev.check_runner import BaseCheckRunner

    class CheckRunner(BaseCheckRunner):
        PROJECT_NAME = "my-project"
        INTEGRATION_REQUIRES = "Redis"

    if __name__ == "__main__":
        CheckRunner(Path(__file__).parent.parent.parent).main()
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

# --- ANSI Colors ---


class Colors:
    HEADER = "\033[95m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"


class BaseCheckRunner:
    """Base quality gate runner. Subclass and override class attributes or methods."""

    PROJECT_NAME: str = "project"
    AUDIT_FLAGS: str = "--skip-editable"
    INTEGRATION_REQUIRES: str = "external services"
    RUN_LINT: bool = True
    RUN_TYPES: bool = True
    RUN_SECURITY: bool = True
    RUN_EXTRA_CHECKS: bool = True
    RUN_UNIT_TESTS: bool = True
    RUN_INTEGRATION_TESTS: bool = True

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.src_dir = project_root / "src"
        self.tests_dir = project_root / "tests"

    # --- Output helpers ---

    def print_step(self, msg: str) -> None:
        print(f"\n{Colors.YELLOW}🔍 {msg}...{Colors.ENDC}")

    def print_success(self, msg: str) -> None:
        print(f"{Colors.GREEN}✅ {msg}{Colors.ENDC}")

    def print_error(self, msg: str) -> None:
        print(f"{Colors.RED}❌ {msg}{Colors.ENDC}")

    def print_skip(self, msg: str) -> None:
        print(f"{Colors.BLUE}⏭ {msg}{Colors.ENDC}")

    # --- Command runner ---

    def run_command(self, command: str, capture_output: bool = False) -> tuple[bool, str]:
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                shell=True,
                check=False,
                text=True,
                capture_output=capture_output,
            )
            return result.returncode == 0, result.stdout or result.stderr or ""
        except Exception as e:
            return False, str(e)

    # --- Check methods ---

    def check_quality(self) -> bool:
        self.print_step("Running Quality Hooks (pre-commit: Ruff, Format, Bandit)")
        success, out = self.run_command("pre-commit run --all-files")
        if not success:
            self.print_error(f"Pre-commit failed:\n{out}")
            return False
        self.print_success("Quality hooks passed.")
        return True

    def check_types(self) -> bool:
        self.print_step("Checking Types (Mypy)")
        success, out = self.run_command(
            f'"{sys.executable}" -m mypy {self.src_dir}',
            capture_output=True,
        )
        if not success:
            self.print_error(f"Mypy check failed:\n{out}")
        else:
            self.print_success("Mypy check passed.")
        return success

    def check_security(self) -> bool:
        self.print_step("Security Audit (pip-audit)")
        success, out = self.run_command(
            f"pip-audit {self.AUDIT_FLAGS}",
            capture_output=True,
        )
        if not success:
            self.print_error(f"Security audit failed:\n{out}")
        else:
            self.print_success("Security audit passed.")
        return success

    def run_tests(self, marker: str = "unit") -> bool:
        self.print_step(f"Running {marker.capitalize()} Tests")
        success, _ = self.run_command(f'"{sys.executable}" -m pytest {self.tests_dir} -m {marker} -v --tb=short')
        if success:
            self.print_success(f"{marker.capitalize()} tests passed.")
        else:
            self.print_error(f"{marker.capitalize()} tests failed.")
        return success

    def extra_checks(self) -> bool:
        """Hook for project-specific checks (Docker, migrations, etc.). Override in subclass."""
        return True

    # --- Orchestration ---

    def run_all(self) -> None:
        """Developer mode: runs all checks, asks before integration tests."""
        if os.name == "nt":
            os.system("cls")
        else:
            os.system("clear")

        print(f"{Colors.HEADER}{Colors.BOLD}=== {self.PROJECT_NAME} quality gate ==={Colors.ENDC}")

        if self.RUN_LINT and not self.check_quality():
            sys.exit(1)
        if not self.RUN_LINT:
            self.print_skip("Skipping quality hooks (RUN_LINT=False).")

        if self.RUN_TYPES and not self.check_types():
            sys.exit(1)
        if not self.RUN_TYPES:
            self.print_skip("Skipping mypy (RUN_TYPES=False).")

        if self.RUN_SECURITY and not self.check_security():
            sys.exit(1)
        if not self.RUN_SECURITY:
            self.print_skip("Skipping security audit (RUN_SECURITY=False).")

        if self.RUN_EXTRA_CHECKS and not self.extra_checks():
            sys.exit(1)
        if not self.RUN_EXTRA_CHECKS:
            self.print_skip("Skipping extra checks (RUN_EXTRA_CHECKS=False).")

        if self.RUN_UNIT_TESTS and not self.run_tests("unit"):
            sys.exit(1)
        if not self.RUN_UNIT_TESTS:
            self.print_skip("Skipping unit tests (RUN_UNIT_TESTS=False).")

        if self.RUN_INTEGRATION_TESTS:
            prompt = (
                f"\n{Colors.YELLOW}🚀 Run Integration Tests? "
                f"(Requires: {self.INTEGRATION_REQUIRES}) [y/N]: {Colors.ENDC}"
            )
            if input(prompt).lower() == "y" and not self.run_tests("integration"):
                sys.exit(1)
        else:
            self.print_skip("Skipping integration tests (RUN_INTEGRATION_TESTS=False).")

        print(f"\n{Colors.GREEN}{Colors.BOLD}ALL CHECKS PASSED!{Colors.ENDC}")

    def run_ci(self) -> None:
        """CI mode: runs everything non-interactively, no prompts."""
        print(f"{Colors.HEADER}{Colors.BOLD}=== {self.PROJECT_NAME} CI gate ==={Colors.ENDC}")

        results: list[bool] = []

        if self.RUN_LINT:
            results.append(self.check_quality())
        else:
            self.print_skip("Skipping quality hooks (RUN_LINT=False).")

        if self.RUN_TYPES:
            results.append(self.check_types())
        else:
            self.print_skip("Skipping mypy (RUN_TYPES=False).")

        if self.RUN_SECURITY:
            results.append(self.check_security())
        else:
            self.print_skip("Skipping security audit (RUN_SECURITY=False).")

        if self.RUN_EXTRA_CHECKS:
            results.append(self.extra_checks())
        else:
            self.print_skip("Skipping extra checks (RUN_EXTRA_CHECKS=False).")

        if self.RUN_UNIT_TESTS:
            results.append(self.run_tests("unit"))
        else:
            self.print_skip("Skipping unit tests (RUN_UNIT_TESTS=False).")

        if self.RUN_INTEGRATION_TESTS:
            results.append(self.run_tests("integration"))
        else:
            self.print_skip("Skipping integration tests (RUN_INTEGRATION_TESTS=False).")

        if not all(results):
            sys.exit(1)

        print(f"\n{Colors.GREEN}{Colors.BOLD}ALL CHECKS PASSED!{Colors.ENDC}")

    def main(self) -> None:
        parser = argparse.ArgumentParser(description=f"{self.PROJECT_NAME} quality gate")
        parser.add_argument("--all", action="store_true", help="Run all checks (asks about integration)")
        parser.add_argument("--ci", action="store_true", help="Run all checks non-interactively (for CI)")
        parser.add_argument("--lint", action="store_true", help="Run pre-commit hooks")
        parser.add_argument("--types", action="store_true", help="Run mypy")
        parser.add_argument("--security", action="store_true", help="Run pip-audit")
        parser.add_argument("--tests", choices=["unit", "integration", "all"], help="Run specified tests")

        args = parser.parse_args()

        if args.ci:
            self.run_ci()
        elif args.all:
            self.run_all()
        elif args.lint:
            if not self.RUN_LINT:
                self.print_skip("Quality hooks are disabled (RUN_LINT=False).")
                sys.exit(0)
            sys.exit(0 if self.check_quality() else 1)
        elif args.types:
            if not self.RUN_TYPES:
                self.print_skip("Type checks are disabled (RUN_TYPES=False).")
                sys.exit(0)
            sys.exit(0 if self.check_types() else 1)
        elif args.security:
            if not self.RUN_SECURITY:
                self.print_skip("Security checks are disabled (RUN_SECURITY=False).")
                sys.exit(0)
            sys.exit(0 if self.check_security() else 1)
        elif args.tests:
            if args.tests == "all":
                u = True
                i = True
                if self.RUN_UNIT_TESTS:
                    u = self.run_tests("unit")
                else:
                    self.print_skip("Unit tests are disabled (RUN_UNIT_TESTS=False).")

                if self.RUN_INTEGRATION_TESTS:
                    i = self.run_tests("integration")
                else:
                    self.print_skip("Integration tests are disabled (RUN_INTEGRATION_TESTS=False).")

                sys.exit(0 if u and i else 1)
            else:
                if args.tests == "unit" and not self.RUN_UNIT_TESTS:
                    self.print_skip("Unit tests are disabled (RUN_UNIT_TESTS=False).")
                    sys.exit(0)
                if args.tests == "integration" and not self.RUN_INTEGRATION_TESTS:
                    self.print_skip("Integration tests are disabled (RUN_INTEGRATION_TESTS=False).")
                    sys.exit(0)
                sys.exit(0 if self.run_tests(args.tests) else 1)
        else:
            parser.print_help()
