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

        if not self.check_quality():
            sys.exit(1)
        if not self.check_types():
            sys.exit(1)
        if not self.check_security():
            sys.exit(1)
        if not self.extra_checks():
            sys.exit(1)
        if not self.run_tests("unit"):
            sys.exit(1)

        prompt = (
            f"\n{Colors.YELLOW}🚀 Run Integration Tests? (Requires: {self.INTEGRATION_REQUIRES}) [y/N]: {Colors.ENDC}"
        )
        if input(prompt).lower() == "y" and not self.run_tests("integration"):
            sys.exit(1)

        print(f"\n{Colors.GREEN}{Colors.BOLD}ALL CHECKS PASSED!{Colors.ENDC}")

    def run_ci(self) -> None:
        """CI mode: runs everything non-interactively, no prompts."""
        print(f"{Colors.HEADER}{Colors.BOLD}=== {self.PROJECT_NAME} CI gate ==={Colors.ENDC}")

        results = [
            self.check_quality(),
            self.check_types(),
            self.check_security(),
            self.extra_checks(),
            self.run_tests("unit"),
            self.run_tests("integration"),
        ]

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
            sys.exit(0 if self.check_quality() else 1)
        elif args.types:
            sys.exit(0 if self.check_types() else 1)
        elif args.security:
            sys.exit(0 if self.check_security() else 1)
        elif args.tests:
            if args.tests == "all":
                u = self.run_tests("unit")
                i = self.run_tests("integration")
                sys.exit(0 if u and i else 1)
            else:
                sys.exit(0 if self.run_tests(args.tests) else 1)
        else:
            parser.print_help()
