<!-- Type: CONCEPT -->
[🏠 Home](../../../index.md) | [🧭 Guide (EN)](../../README.md) | [🛠️ Dev API](../../api/dev/index.md)

# Dev Tools (Architecture)

The `dev` module provides reusable development utilities shared across all **Codex** projects.
All tools are **pure Python** (stdlib only) — no external dependencies required.

---

## 1. BaseCheckRunner — Quality Gate

A base class for project-level quality gate scripts. Every Codex project has a `tools/dev/check.py`
that inherits from `BaseCheckRunner` and overrides only what differs.

### Standardized behavior (base class)

| Check | Command |
|-------|---------|
| Quality | `pre-commit run --all-files` |
| Types | `sys.executable -m mypy src/` |
| Security | `pip-audit --skip-editable` |
| Unit tests | `pytest -m unit -v --tb=short` |
| Integration | `pytest -m integration -v --tb=short` |

`--skip-editable` ensures pip-audit only scans real PyPI packages,
not locally installed editable codex-* dependencies.

### CLI interface

```bash
python tools/dev/check.py --lint        # pre-commit only
python tools/dev/check.py --types       # mypy only
python tools/dev/check.py --security    # pip-audit only
python tools/dev/check.py --tests unit
python tools/dev/check.py --tests integration
python tools/dev/check.py --all         # lint + types + security + unit, asks about integration
python tools/dev/check.py --ci          # everything non-interactively (GitHub Actions)
```

### Project switches

Projects can keep the shared orchestration and declare their local policy with
simple boolean attributes on `CheckRunner`:

```python
class CheckRunner(BaseCheckRunner):
    RUN_LINT = True
    RUN_TYPES = True
    RUN_SECURITY = True
    RUN_EXTRA_CHECKS = True
    RUN_UNIT_TESTS = True
    RUN_INTEGRATION_TESTS = False
```

This is the preferred extension point when a library does not need every stage.
Use method overrides only when behavior itself must change.

### Usage in a project

```python
# tools/dev/check.py
from pathlib import Path
from codex_core.dev.check_runner import BaseCheckRunner

class CheckRunner(BaseCheckRunner):
    PROJECT_NAME = "my-project"
    INTEGRATION_REQUIRES = "Redis"

if __name__ == "__main__":
    CheckRunner(Path(__file__).parent.parent.parent).main()
```

### Extending for Docker or migrations

Override `extra_checks()` to add project-specific gates:

```python
class CheckRunner(BaseCheckRunner):
    PROJECT_NAME = "codex-django"
    INTEGRATION_REQUIRES = "PostgreSQL + Redis"

    def extra_checks(self) -> bool:
        # manage.py check, migrate --check, etc.
        return True
```

### CI-specific override (codex-ai pattern)

When integration tests require API keys that may be absent, override `run_tests()`
to add `--no-cov` so the coverage threshold gate does not fail on 0 collected tests:

```python
def run_tests(self, marker: str = "unit") -> bool:
    if marker == "integration":
        success, _ = self.run_command(
            f'"{sys.executable}" -m pytest {self.tests_dir}'
            f" -m integration -v --tb=short --no-cov"
        )
        return success
    return super().run_tests(marker)
```

---

## 2. ProjectTreeGenerator

Generates a human-readable directory tree of any project and saves it to `project_structure.txt`.
Useful for documentation, onboarding, and architecture reviews.

### Features

- Interactive menu — pick a single top-level folder or scan the full project
- Pre-configured ignore lists (`.venv`, `__pycache__`, `node_modules`, etc.)
- Extendable: pass custom `ignore_dirs` / `ignore_extensions` sets

### Usage in a project

```python
# tools/dev/generate_project_tree.py
from pathlib import Path
from codex_core.dev.project_tree import ProjectTreeGenerator

if __name__ == "__main__":
    ProjectTreeGenerator(Path(__file__).parent.parent.parent).interactive()
```

### Programmatic usage

```python
gen = ProjectTreeGenerator(root=Path("/my/project"))

# Full project → project_structure.txt
gen.generate(target_dir=None, output=Path("project_structure.txt"))

# Only the src/ folder
gen.generate(target_dir="src", output=Path("src_structure.txt"))

# Custom ignore list
gen = ProjectTreeGenerator(
    root=Path("/my/project"),
    ignore_dirs=frozenset({".git", ".venv", "build"}),
)
```

---

## 3. StaticCompiler — CSS & JS Bundler

A pure Python static asset compiler. Resolves CSS `@import` chains and concatenates
JS source files into bundles. No Node.js, no external packages required.

### Sub-modules

| Module | Responsibility |
|--------|---------------|
| `css.py` | Resolve `@import url(...)`, remove comments, minify |
| `js.py` | Concatenate sources, remove comments, minify |
| `compiler.py` | Orchestration, config parsing, two modes |

### Config format (`compiler_config.json`)

```json
{
    "css": {
        "base.css": "app.css"
    },
    "js": {
        "app.js": ["vendor/alpine.js", "src/main.js", "src/ui.js"]
    }
}
```

Old CSS-only format is supported for backwards compatibility:
```json
{ "base.css": "app.css" }
```

### Mode 1 — Single project

```python
from pathlib import Path
from codex_core.dev.static_compiler import StaticCompiler

root = Path(__file__).parent.parent.parent
static = root / "src" / "backend_django" / "static"

StaticCompiler().compile_from_config(
    config=static / "css" / "compiler_config.json",
    css_dir=static / "css",
    js_dir=static / "js",
)
```

### Mode 2 — Multi-project (landings)

Compile multiple sub-projects from a single master settings file:

```json
{
    "projects": [
        {
            "name": "landing-ru",
            "config": "src/landing_ru/static/css/compiler_config.json",
            "css_dir": "src/landing_ru/static/css",
            "js_dir":  "src/landing_ru/static/js"
        },
        {
            "name": "landing-en",
            "config": "src/landing_en/static/css/compiler_config.json"
        }
    ]
}
```

```python
StaticCompiler().compile_from_settings(Path("static_settings.json"))
```

### Flags

```python
StaticCompiler(css=True, js=False)               # CSS only
StaticCompiler(js=True, css=False)               # JS only
StaticCompiler(minify=True)                      # full minification
StaticCompiler(remove_comments=False)            # keep comments
```

### Project-level entry point

```python
# tools/static/compile.py  (project-specific, ~10 lines)
from pathlib import Path
from codex_core.dev.static_compiler import StaticCompiler

if __name__ == "__main__":
    root = Path(__file__).parent.parent.parent
    static = root / "src" / "backend_django" / "static"
    StaticCompiler().compile_from_config(
        config=static / "css" / "compiler_config.json",
        css_dir=static / "css",
        js_dir=static / "js",
    )
```
