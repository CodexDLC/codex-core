"""Quality gate for codex-core."""

from pathlib import Path

from codex_core.dev.check_runner import BaseCheckRunner


class CheckRunner(BaseCheckRunner):
    PROJECT_NAME = "codex-core"
    INTEGRATION_REQUIRES = "Redis"


if __name__ == "__main__":
    CheckRunner(Path(__file__).parent.parent.parent).main()
