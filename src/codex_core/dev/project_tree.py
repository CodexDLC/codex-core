"""Project structure tree generator.

Scans a project directory and writes a human-readable tree to a text file.
Interactive mode lets the user pick a top-level folder or the full project.

Usage (in a project's tools/dev/generate_project_tree.py):

    from pathlib import Path
    from codex_core.dev.project_tree import ProjectTreeGenerator

    if __name__ == "__main__":
        ProjectTreeGenerator(Path(__file__).parent.parent.parent).interactive()
"""

import os
from pathlib import Path


class ProjectTreeGenerator:
    DEFAULT_IGNORE_DIRS: frozenset[str] = frozenset(
        {
            ".git",
            ".github",
            "venv",
            ".venv",
            "__pycache__",
            ".idea",
            ".vscode",
            "data",
            "logs",
            ".pytest_cache",
            ".mypy_cache",
            ".ruff_cache",
            ".gemini",
            "node_modules",
            "site-packages",
            "site",
        }
    )
    DEFAULT_IGNORE_EXTENSIONS: frozenset[str] = frozenset(
        {
            ".pyc",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".svg",
            ".db",
            ".sqlite3",
            ".ico",
            ".woff",
            ".woff2",
        }
    )

    def __init__(
        self,
        root: Path,
        ignore_dirs: frozenset[str] | None = None,
        ignore_extensions: frozenset[str] | None = None,
    ) -> None:
        self.root = root.resolve()
        self.ignore_dirs = ignore_dirs or self.DEFAULT_IGNORE_DIRS
        self.ignore_extensions = ignore_extensions or self.DEFAULT_IGNORE_EXTENSIONS

    def _top_level_dirs(self) -> list[str]:
        return sorted(d for d in os.listdir(self.root) if os.path.isdir(self.root / d) and d not in self.ignore_dirs)

    def generate(self, target_dir: str | None, output: Path) -> None:
        """Write tree to output file.

        Args:
            target_dir: Sub-directory name to scan, or None for the full project.
            output: Path to the output .txt file.
        """
        start = self.root / target_dir if target_dir else self.root
        title = f"Project Structure: {target_dir or 'Full Project'}"

        with open(output, "w", encoding="utf-8") as f:
            f.write(f"{title}\n{'=' * len(title)}\n\n")

            for current_root, dirs, files in os.walk(start, topdown=True):
                dirs[:] = sorted(d for d in dirs if d not in self.ignore_dirs)

                rel = os.path.relpath(current_root, start)
                if rel == ".":
                    level = 0
                    name = os.path.basename(start)
                else:
                    level = rel.count(os.sep) + 1
                    name = os.path.basename(current_root)

                indent = "    " * level
                f.write(f"{indent}📂 {name}/\n")

                sub = "    " * (level + 1)
                for file in sorted(files):
                    if not any(file.endswith(ext) for ext in self.ignore_extensions):
                        f.write(f"{sub}📄 {file}\n")

    def interactive(self, output: Path | None = None) -> None:
        """Show interactive folder selection menu and generate tree."""
        output = output or (self.root / "project_structure.txt")
        top_dirs = self._top_level_dirs()

        print(f"\n🔍 Project root: {self.root}")
        print("Select scope:\n")
        print("   0. 🌳 Full project")
        for idx, folder in enumerate(top_dirs, 1):
            print(f"   {idx}. 📁 {folder}/")

        while True:
            try:
                choice = input(f"\nEnter number (0-{len(top_dirs)}): ").strip()
                if not choice.isdigit():
                    raise ValueError
                idx = int(choice)
                if 0 <= idx <= len(top_dirs):
                    break
                print("Invalid number, try again.")
            except ValueError:
                print("Enter a number.")

        target = top_dirs[idx - 1] if idx > 0 else None
        label = target or "Full project"
        print(f"\n⚙️  Generating: {label}...")
        self.generate(target, output)
        print(f"✅ Saved to: {output}")
