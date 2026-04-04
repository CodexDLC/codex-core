"""JS compiler: concatenates source files into one bundle."""

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class JSModule:
    rel_path: str
    full_path: Path
    provides: str
    depends: tuple[str, ...]


class JSCompiler:
    """Pure Python JS bundler (concatenation + optional comment removal)."""

    _provides_re = re.compile(r"@provides\s+([A-Za-z0-9._-]+)")
    _depends_re = re.compile(r"@depends\s+([^\n\r*]+)")

    def remove_comments(self, js: str) -> str:
        js = re.sub(r"/\*.*?\*/", "", js, flags=re.DOTALL)
        js = re.sub(r"(?<!:)//[^\n]*", "", js)
        return js

    def minify(self, js: str) -> str:
        js = self.remove_comments(js)
        return re.sub(r"\s+", " ", js).strip()

    def compile(
        self,
        sources: list[str],
        output: Path,
        js_dir: Path,
        minify: bool = False,
        remove_comments: bool = False,
    ) -> bool:
        print(f"  JS:  [{', '.join(sources)}] -> {output.name}")
        parts: list[str] = []

        for rel_path in sources:
            full_path = (js_dir / rel_path).resolve()
            if not full_path.exists():
                print(f"  WARNING: source not found: {full_path}")
                parts.append(f"/* Source not found: {rel_path} */")
                continue
            try:
                content = full_path.read_text(encoding="utf-8")
                parts.append(f"/* === {rel_path} === */\n{content}")
            except Exception as e:
                print(f"  ERROR reading {full_path}: {e}")

        result = "\n\n".join(parts)
        if minify:
            result = self.minify(result)
        elif remove_comments:
            result = self.remove_comments(result)

        header = f"/*\n * Compiled JS — DO NOT EDIT\n * Sources: {', '.join(sources)}\n * Minified: {minify}\n */\n\n"
        try:
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(header + result, encoding="utf-8")
            print(f"     OK: {len(header + result):,} bytes")
            return True
        except Exception as e:
            print(f"  ERROR writing {output}: {e}")
            return False

    def compile_bundle(
        self,
        bundle: list[str] | dict[str, Any],
        output: Path,
        js_dir: Path,
        minify: bool = False,
        remove_comments: bool = False,
    ) -> bool:
        if isinstance(bundle, list):
            return self.compile(bundle, output, js_dir, minify=minify, remove_comments=remove_comments)

        strategy = bundle.get("strategy", "ordered")
        if strategy == "ordered":
            sources = bundle.get("sources") or bundle.get("entry") or []
            if not isinstance(sources, list):
                print("  ERROR: ordered JS bundle expects a list in 'sources' or 'entry'")
                return False
            return self.compile(sources, output, js_dir, minify=minify, remove_comments=remove_comments)

        if strategy == "dependency_graph":
            return self.compile_dependency_graph(bundle, output, js_dir, minify=minify, remove_comments=remove_comments)

        print(f"  ERROR: unknown JS bundle strategy: {strategy}")
        return False

    def compile_dependency_graph(
        self,
        bundle: dict[str, Any],
        output: Path,
        js_dir: Path,
        minify: bool = False,
        remove_comments: bool = False,
    ) -> bool:
        js_dir = js_dir.resolve()
        entry_paths = bundle.get("entry", [])
        roots = bundle.get("roots", [])

        if not isinstance(entry_paths, list) or not entry_paths:
            print("  ERROR: dependency_graph bundle requires a non-empty 'entry' list")
            return False
        if not isinstance(roots, list) or not roots:
            print("  ERROR: dependency_graph bundle requires a non-empty 'roots' list")
            return False

        modules: dict[str, JSModule] = {}
        modules_by_path: dict[str, JSModule] = {}
        errors = False

        def register_module(rel_path: str) -> None:
            nonlocal errors
            normalized = rel_path.replace("\\", "/")
            if normalized in modules_by_path:
                return
            full_path = (js_dir / normalized).resolve()
            if not full_path.exists():
                print(f"  ERROR: unknown entry/source: {normalized}")
                errors = True
                return

            try:
                content = full_path.read_text(encoding="utf-8")
            except Exception as exc:
                print(f"  ERROR reading {full_path}: {exc}")
                errors = True
                return

            provides = self._parse_provides(content)
            if not provides:
                print(f"  ERROR: missing dependency provider metadata in {normalized}")
                errors = True
                return
            if len(provides) > 1:
                print(f"  ERROR: multiple @provides declarations in {normalized}: {', '.join(provides)}")
                errors = True
                return

            provide_name = provides[0]
            if provide_name in modules:
                print(
                    f"  ERROR: duplicate provider {provide_name} in {normalized} and {modules[provide_name].rel_path}"
                )
                errors = True
                return

            module = JSModule(
                rel_path=normalized,
                full_path=full_path,
                provides=provide_name,
                depends=tuple(self._parse_depends(content)),
            )
            modules[provide_name] = module
            modules_by_path[normalized] = module

        for root in roots:
            root_path = (js_dir / root).resolve()
            if not root_path.exists():
                print(f"  ERROR: unknown root directory: {root}")
                errors = True
                continue
            for full_path in sorted(root_path.rglob("*.js")):
                rel_path = full_path.relative_to(js_dir).as_posix()
                register_module(rel_path)

        for entry_path in entry_paths:
            register_module(entry_path)

        if errors:
            return False

        ordered_modules: list[JSModule] = []
        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(provider: str, stack: list[str]) -> bool:
            if provider in visited:
                return True
            if provider in visiting:
                cycle = " -> ".join(stack + [provider])
                print(f"  ERROR: dependency cycle detected: {cycle}")
                return False
            module = modules.get(provider)
            if module is None:
                print(f"  ERROR: missing dependency: {provider}")
                return False

            visiting.add(provider)
            for dependency in module.depends:
                if not visit(dependency, stack + [provider]):
                    return False
            visiting.remove(provider)
            visited.add(provider)
            ordered_modules.append(module)
            return True

        for entry_path in entry_paths:
            provider = modules_by_path.get(entry_path.replace("\\", "/"))
            if provider is None:
                print(f"  ERROR: unknown entry: {entry_path}")
                return False
            if not visit(provider.provides, []):
                return False

        ordered_sources = [module.rel_path for module in ordered_modules]
        return self.compile(ordered_sources, output, js_dir, minify=minify, remove_comments=remove_comments)

    def _parse_provides(self, content: str) -> list[str]:
        return self._provides_re.findall(content)

    def _parse_depends(self, content: str) -> list[str]:
        dependencies: list[str] = []
        for raw_line in self._depends_re.findall(content):
            for part in raw_line.split(","):
                dependency = part.strip()
                if dependency:
                    dependencies.append(dependency)
        return dependencies
