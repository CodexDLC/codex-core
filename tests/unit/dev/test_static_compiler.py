from pathlib import Path

from codex_core.dev.static_compiler import StaticCompiler


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_static_compiler_keeps_ordered_js_mode(tmp_path: Path) -> None:
    js_dir = tmp_path / "static" / "js"
    config = js_dir / "compiler_config.json"
    _write(js_dir / "core" / "a.js", "window.a = 1;")
    _write(js_dir / "core" / "b.js", "window.b = window.a + 1;")
    _write(
        config,
        """
        {
          "js": {
            "bundle.js": ["core/a.js", "core/b.js"]
          }
        }
        """,
    )

    ok = StaticCompiler().compile_from_config(config, js_dir=js_dir)

    assert ok is True
    result = (js_dir / "bundle.js").read_text(encoding="utf-8")
    assert "core/a.js" in result
    assert "core/b.js" in result
    assert result.index("window.a = 1;") < result.index("window.b = window.a + 1;")


def test_static_compiler_builds_js_dependency_graph(tmp_path: Path) -> None:
    js_dir = tmp_path / "static" / "js"
    config = js_dir / "compiler_config.json"
    _write(
        js_dir / "core" / "dom.js",
        "/* @provides cabinet.core.dom */\nwindow.domReady = true;",
    )
    _write(
        js_dir / "widgets" / "lookup.js",
        "/* @provides cabinet.widgets.lookup\\n   @depends cabinet.core.dom */\nwindow.lookupReady = true;",
    )
    _write(
        js_dir / "app" / "entry.js",
        "/* @provides cabinet.app.entry\\n   @depends cabinet.widgets.lookup */\nwindow.entryReady = true;",
    )
    _write(
        config,
        """
        {
          "js": {
            "bundle.js": {
              "strategy": "dependency_graph",
              "entry": ["app/entry.js"],
              "roots": ["core", "widgets", "app"]
            }
          }
        }
        """,
    )

    ok = StaticCompiler().compile_from_config(config, js_dir=js_dir)

    assert ok is True
    result = (js_dir / "bundle.js").read_text(encoding="utf-8")
    assert result.index("window.domReady = true;") < result.index("window.lookupReady = true;")
    assert result.index("window.lookupReady = true;") < result.index("window.entryReady = true;")


def test_static_compiler_reports_missing_dependency_graph_provider(tmp_path: Path, capsys) -> None:
    js_dir = tmp_path / "static" / "js"
    config = js_dir / "compiler_config.json"
    _write(
        js_dir / "app" / "entry.js",
        "/* @provides cabinet.app.entry\\n   @depends cabinet.widgets.missing */\nwindow.entryReady = true;",
    )
    _write(
        config,
        """
        {
          "js": {
            "bundle.js": {
              "strategy": "dependency_graph",
              "entry": ["app/entry.js"],
              "roots": ["app"]
            }
          }
        }
        """,
    )

    ok = StaticCompiler().compile_from_config(config, js_dir=js_dir)

    captured = capsys.readouterr()
    assert ok is False
    assert "missing dependency: cabinet.widgets.missing" in captured.out


def test_static_compiler_reports_dependency_cycle(tmp_path: Path, capsys) -> None:
    js_dir = tmp_path / "static" / "js"
    config = js_dir / "compiler_config.json"
    _write(
        js_dir / "core" / "a.js",
        "/* @provides cabinet.core.a\\n   @depends cabinet.core.b */\nwindow.aReady = true;",
    )
    _write(
        js_dir / "core" / "b.js",
        "/* @provides cabinet.core.b\\n   @depends cabinet.core.a */\nwindow.bReady = true;",
    )
    _write(
        js_dir / "app" / "entry.js",
        "/* @provides cabinet.app.entry\\n   @depends cabinet.core.a */\nwindow.entryReady = true;",
    )
    _write(
        config,
        """
        {
          "js": {
            "bundle.js": {
              "strategy": "dependency_graph",
              "entry": ["app/entry.js"],
              "roots": ["core", "app"]
            }
          }
        }
        """,
    )

    ok = StaticCompiler().compile_from_config(config, js_dir=js_dir)

    captured = capsys.readouterr()
    assert ok is False
    assert "dependency cycle detected" in captured.out


def test_static_compiler_reports_duplicate_provider(tmp_path: Path, capsys) -> None:
    js_dir = tmp_path / "static" / "js"
    config = js_dir / "compiler_config.json"
    _write(
        js_dir / "core" / "a.js",
        "/* @provides cabinet.core.dom */\nwindow.aReady = true;",
    )
    _write(
        js_dir / "widgets" / "b.js",
        "/* @provides cabinet.core.dom */\nwindow.bReady = true;",
    )
    _write(
        js_dir / "app" / "entry.js",
        "/* @provides cabinet.app.entry\\n   @depends cabinet.core.dom */\nwindow.entryReady = true;",
    )
    _write(
        config,
        """
        {
          "js": {
            "bundle.js": {
              "strategy": "dependency_graph",
              "entry": ["app/entry.js"],
              "roots": ["core", "widgets", "app"]
            }
          }
        }
        """,
    )

    ok = StaticCompiler().compile_from_config(config, js_dir=js_dir)

    captured = capsys.readouterr()
    assert ok is False
    assert "duplicate provider cabinet.core.dom" in captured.out
