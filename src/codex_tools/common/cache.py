"""
codex_tools.common.cache
=========================
Универсальные утилиты для работы с кэшем.
"""

import logging
from collections.abc import Callable
from typing import Any

log = logging.getLogger(__name__)


def get_cached_data_universal(
    cache_instance: Any, key: str, fetch_func: Callable[[], Any], timeout: int = 86400, service_name: str = "Cache"
) -> Any:
    """
    Универсальная функция Cache-Aside.

    Args:
        cache_instance: Объект кэша (должен иметь методы get и set).
        key: Уникальный ключ.
        fetch_func: Функция получения данных при промахе кэша.
        timeout: Время жизни в секундах.
        service_name: Имя сервиса для логов.
    """
    data = cache_instance.get(key)

    if data is not None:
        log.debug(f"{service_name} | action=get status=hit key='{key}'")
        return data

    log.debug(f"{service_name} | action=get status=miss key='{key}'")

    # Получаем свежие данные
    data = fetch_func()

    if data is not None:
        # Если это Django QuerySet, превращаем в список для сериализации
        if hasattr(data, "all") and callable(data.all):
            data = list(data)

        cache_instance.set(key, data, timeout)
        log.debug(f"{service_name} | action=set status=success key='{key}' timeout={timeout}")

    return data
