"""Static asset compiler for CSS and JS bundling.

Usage (single project):
    from codex_core.dev.static_compiler import StaticCompiler

    StaticCompiler().compile_from_config(
        config=Path("static/css/compiler_config.json"),
        css_dir=Path("static/css"),
        js_dir=Path("static/js"),
    )

Usage (multi-project landings):
    StaticCompiler().compile_from_settings(Path("static_settings.json"))
"""

from .compiler import StaticCompiler

__all__ = ["StaticCompiler"]
