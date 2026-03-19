"""CSS compiler: resolves @import, removes comments, minifies."""

import re
from pathlib import Path


class CSSCompiler:
    """Pure Python CSS compiler. No external dependencies."""

    def read(self, file_path: Path) -> str:
        try:
            return file_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"  ERROR reading {file_path}: {e}")
            return ""

    def resolve_imports(self, css: str, base_path: Path) -> str:
        """Recursively resolves @import url('...') directives."""
        pattern = r"@import\s+url\(['\"](.+?)['\"]\)(?:\s+(.+?))?;"

        def replace(match: re.Match[str]) -> str:
            import_path = match.group(1)
            media_query = match.group(2)
            full_path = (base_path / import_path).resolve()
            if not full_path.exists():
                print(f"  WARNING: import not found: {full_path}")
                return f"/* Import not found: {import_path} */"
            content = self.read(full_path)
            content = self.resolve_imports(content, full_path.parent)
            if media_query:
                return f"/* From {import_path} */\n@media {media_query} {{\n{content}\n}}"
            return f"/* From {import_path} */\n{content}"

        return re.sub(pattern, replace, css)

    def remove_comments(self, css: str) -> str:
        return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)

    def minify(self, css: str) -> str:
        css = self.remove_comments(css)
        css = re.sub(r"\s+", " ", css)
        css = re.sub(r"\s*([{}:;,])\s*", r"\1", css)
        return css.strip()

    def compile(
        self,
        source: Path,
        output: Path,
        minify: bool = False,
        remove_comments: bool = False,
    ) -> bool:
        print(f"  CSS: {source.name} -> {output.name}")
        raw = self.read(source)
        if not raw:
            return False

        result = self.resolve_imports(raw, source.parent)
        if minify:
            result = self.minify(result)
        elif remove_comments:
            result = self.remove_comments(result)

        header = f"/*\n * Compiled CSS — DO NOT EDIT\n * Source: {source.name}\n * Minified: {minify}\n */\n\n"
        try:
            output.write_text(header + result, encoding="utf-8")
            print(f"     OK: {len(header + result):,} bytes")
            return True
        except Exception as e:
            print(f"  ERROR writing {output}: {e}")
            return False
