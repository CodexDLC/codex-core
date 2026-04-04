<!-- Type: CONCEPT -->
[🏠 Главная](../../../index.md) | [🧭 Руководство (RU)](../../README.md) | [🛠️ Dev API](../../../en/api/dev/index.md)

# Dev Tools (Архитектура)

Модуль `dev` предоставляет переиспользуемые инструменты разработки, общие для всех проектов **Codex**.
Все инструменты написаны на **чистом Python** (только stdlib) — никаких внешних зависимостей.

---

## 1. BaseCheckRunner — Quality Gate

Базовый класс для скриптов проверки качества. Каждый Codex-проект имеет `tools/dev/check.py`,
который наследуется от `BaseCheckRunner` и переопределяет только то, что отличается.

### Стандартное поведение (базовый класс)

| Проверка | Команда |
|----------|---------|
| Качество | `pre-commit run --all-files` |
| Типы | `sys.executable -m mypy src/` |
| Безопасность | `pip-audit --skip-editable` |
| Unit тесты | `pytest -m unit -v --tb=short` |
| Integration | `pytest -m integration -v --tb=short` |

Флаг `--skip-editable` гарантирует, что pip-audit сканирует только настоящие PyPI-пакеты,
а не локально установленные editable-зависимости codex-*.

### CLI интерфейс

```bash
python tools/dev/check.py --lint        # только pre-commit
python tools/dev/check.py --types       # только mypy
python tools/dev/check.py --security    # только pip-audit
python tools/dev/check.py --tests unit
python tools/dev/check.py --tests integration
python tools/dev/check.py --all         # lint + types + security + unit, спрашивает про integration
python tools/dev/check.py --ci          # всё без промптов (GitHub Actions)
```

### Проектные переключатели

Рекомендуемый способ задания проектной политики проверки качества — через секцию `[tool.codex-check]` в файле `pyproject.toml`:

```toml
[tool.codex-check]
project-name = "my-project"
audit-flags = "--skip-editable"
run-lint = true
run-types = true
run-security = true
run-unit-tests = true
run-integration-tests = false
test-stages = ["unit", "integration"]
prompt-test-stages = ["integration"]
```

Поддержка атрибутов класса в `CheckRunner` сохранена для обратной совместимости:

```python
class CheckRunner(BaseCheckRunner):
    RUN_UNIT_TESTS = True
    RUN_INTEGRATION_TESTS = False
```

### Использование в проекте

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

### Расширение для Docker или миграций

Переопределите `extra_checks()` для добавления проектных проверок:

```python
class CheckRunner(BaseCheckRunner):
    PROJECT_NAME = "codex-django"
    INTEGRATION_REQUIRES = "PostgreSQL + Redis"

    def extra_checks(self) -> bool:
        # manage.py check, migrate --check и т.д.
        return True
```

### Override для CI с API-ключами (паттерн codex-ai)

Когда интеграционные тесты требуют API-ключей, которых может не быть,
добавьте `--no-cov` чтобы не провалить coverage-порог на 0 собранных тестах:

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

Генерирует читаемое дерево директорий проекта и сохраняет его в `project_structure.txt`.
Удобно для документации, онбординга и архитектурных ревью.

### Возможности

- Интерактивное меню — выбор одной папки верхнего уровня или всего проекта
- Готовые списки игнорирования (`.venv`, `__pycache__`, `node_modules` и др.)
- Расширяемо: передайте свои `ignore_dirs` / `ignore_extensions`

### Использование в проекте

```python
# tools/dev/generate_project_tree.py
from pathlib import Path
from codex_core.dev.project_tree import ProjectTreeGenerator

if __name__ == "__main__":
    ProjectTreeGenerator(Path(__file__).parent.parent.parent).interactive()
```

### Программное использование

```python
gen = ProjectTreeGenerator(root=Path("/my/project"))

# Весь проект → project_structure.txt
gen.generate(target_dir=None, output=Path("project_structure.txt"))

# Только папка src/
gen.generate(target_dir="src", output=Path("src_structure.txt"))

# Кастомный список игнорирования
gen = ProjectTreeGenerator(
    root=Path("/my/project"),
    ignore_dirs=frozenset({".git", ".venv", "build"}),
)
```

---

## 3. StaticCompiler — Компилятор CSS и JS

Чистый Python компилятор статических ресурсов. Разрешает цепочки CSS `@import` и
конкатенирует JS-файлы в бандлы. Без Node.js, без внешних пакетов.

### Подмодули

| Модуль | Ответственность |
|--------|----------------|
| `css.py` | Разрешение `@import url(...)`, удаление комментариев, минификация |
| `js.py` | Конкатенация файлов, удаление комментариев, минификация |
| `compiler.py` | Оркестрация, парсинг конфига, два режима работы |

### Формат конфига (`compiler_config.json`)

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

Для JS также поддерживается dependency-aware режим:

```json
{
    "js": {
        "app.js": {
            "strategy": "dependency_graph",
            "entry": ["app/entry.js"],
            "roots": ["core", "widgets", "builders", "app"]
        }
    }
}
```

В этом режиме компилятор читает metadata из JS-файлов:

```js
/* @provides cabinet.widgets.client_lookup
   @depends cabinet.core.dom, cabinet.core.events */
```

И строит итоговый порядок автоматически. Старый ordered-mode через явный список файлов остаётся полностью поддержанным.

Старый формат только для CSS поддерживается для обратной совместимости:
```json
{ "base.css": "app.css" }
```

### Режим 1 — Один проект

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

### Режим 2 — Мульти-проект (лендинги)

Компиляция нескольких под-проектов из одного мастер-файла настроек:

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

### Флаги

```python
StaticCompiler(css=True, js=False)       # только CSS
StaticCompiler(js=True, css=False)       # только JS
StaticCompiler(minify=True)              # полная минификация
StaticCompiler(remove_comments=False)    # сохранить комментарии
```

### Точка входа в проекте

```python
# tools/static/compile.py  (~10 строк)
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
