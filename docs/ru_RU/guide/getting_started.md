[🏠 На главную](../../index.md) | [🧭 Руководство (RU)](../README.md) | [🚀 Начало работы](getting_started.md)

# Начало работы (RU)

Добро пожаловать! Это руководство поможет вам быстро и правильно интегрировать **codex-core** в ваш проект.

## Установка

Установите библиотеку с помощью pip:

```bash
pip install codex-core
```

### Установка из исходного кода
Если вам нужны самые свежие изменения из ветки `main`, вы можете установить её напрямую из репозитория:

```bash
pip install git+https://github.com/codexdlc/codex-core.git
```

### Опциональные зависимости
Если вы хотите использовать преднастроенный логгер `Loguru`, вам нужно будет установить `loguru` вручную:

```bash
pip install loguru
```

## Первые шаги

### 1. Создание BaseDTO
Наследуйтесь от `BaseDTO`, чтобы получить автоматическую маскировку PII в ваших логах:

```python
from codex_core.core import BaseDTO

class UserDTO(BaseDTO):
    full_name: str
    email: str
    phone: str
```

### 2. Настройка конфигурации
Используйте `BaseCommonSettings` для стандартизированной загрузки переменных окружения:

```python
from codex_core.settings import BaseCommonSettings

class ProjectSettings(BaseCommonSettings):
    my_api_key: str = "secret"
```

## Что дальше?
Ознакомьтесь с [🛡️ Обзором архитектуры](../architecture/README.md) для более подробной информации.
