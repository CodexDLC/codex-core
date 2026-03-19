"""StaticCompiler: orchestrates CSS and JS compilation from config files.

Two modes:

1. Single project (compile_from_config):
   Reads one compiler_config.json and compiles CSS/JS for that project.

   compiler_config.json format:
   {
       "css": {"base.css": "app.css"},
       "js":  {"app.js": ["module1.js", "module2.js"]}
   }
   Old format (CSS-only, backwards-compatible):
   {
       "base.css": "app.css"
   }

2. Multi-project (compile_from_settings):
   Reads a master settings file listing multiple sub-projects (e.g. landings).

   static_settings.json format:
   {
       "projects": [
           {
               "name": "landing-ru",
               "config": "src/landing_ru/static/css/compiler_config.json",
               "css_dir": "src/landing_ru/static/css",
               "js_dir":  "src/landing_ru/static/js"
           }
       ]
   }
"""

import json
from pathlib import Path
from typing import Any

from .css import CSSCompiler
from .js import JSCompiler


class StaticCompiler:
    """Orchestrates CSS and JS compilation.

    Args:
        css: Enable CSS compilation (default True).
        js:  Enable JS compilation (default True).
        minify: Full minification — removes comments + collapses whitespace.
        remove_comments: Remove comments only, keep formatting.
    """

    def __init__(
        self,
        css: bool = True,
        js: bool = True,
        minify: bool = False,
        remove_comments: bool = True,
    ) -> None:
        self._css = CSSCompiler() if css else None
        self._js = JSCompiler() if js else None
        self._minify = minify
        self._remove_comments = remove_comments

    # ── Single project ────────────────────────────────────────────────────────

    def compile_from_config(
        self,
        config: Path,
        css_dir: Path | None = None,
        js_dir: Path | None = None,
    ) -> bool:
        """Compile one project from its compiler_config.json.

        css_dir and js_dir default to the directory containing the config file.
        """
        if not config.exists():
            print(f"ERROR: config not found: {config}")
            return False

        try:
            data = json.loads(config.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"ERROR: invalid JSON in {config}: {e}")
            return False

        base_dir = config.parent
        css_dir = css_dir or base_dir
        js_dir = js_dir or base_dir

        # Detect old {"base.css": "app.css"} format — treat as css-only
        css_config: dict[str, str] = data.get("css", {})
        js_config: dict[str, list[str]] = data.get("js", {})
        if not css_config and not js_config:
            css_config = data

        ok = True

        if css_config and self._css:
            print("--- CSS ---")
            for src, dst in css_config.items():
                src_path = css_dir / src
                dst_path = css_dir / dst
                if not src_path.exists():
                    print(f"  WARNING: skipping {src} — file not found")
                    continue
                if not self._css.compile(
                    src_path,
                    dst_path,
                    minify=self._minify,
                    remove_comments=self._remove_comments,
                ):
                    ok = False

        if js_config and self._js:
            print("--- JS ---")
            for dst, sources in js_config.items():
                dst_path = js_dir / dst
                if not self._js.compile(
                    sources,
                    dst_path,
                    js_dir,
                    minify=self._minify,
                    remove_comments=self._remove_comments,
                ):
                    ok = False

        return ok

    # ── Multi-project (landings) ───────────────────────────────────────────────

    def compile_from_settings(self, settings: Path) -> bool:
        """Compile multiple projects listed in a master settings JSON file."""
        if not settings.exists():
            print(f"ERROR: settings not found: {settings}")
            return False

        try:
            data = json.loads(settings.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"ERROR: invalid JSON in {settings}: {e}")
            return False

        projects: list[dict[str, Any]] = data.get("projects", [])
        if not projects:
            print("WARNING: no projects defined in settings")
            return True

        root = settings.parent
        ok = True

        for project in projects:
            name = project.get("name", "unnamed")
            config_rel = project.get("config")
            if not config_rel:
                print(f"  WARNING: project '{name}' has no 'config' key, skipping")
                continue

            config_path = (root / config_rel).resolve()
            css_dir = (root / project["css_dir"]).resolve() if "css_dir" in project else None
            js_dir = (root / project["js_dir"]).resolve() if "js_dir" in project else None

            print(f"\n=== Project: {name} ===")
            if not self.compile_from_config(config_path, css_dir, js_dir):
                ok = False

        return ok
