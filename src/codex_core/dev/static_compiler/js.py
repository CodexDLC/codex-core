"""JS compiler: concatenates source files into one bundle."""

import re
from pathlib import Path


class JSCompiler:
    """Pure Python JS bundler (concatenation + optional comment removal)."""

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
