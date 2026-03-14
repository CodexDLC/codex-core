"""
codex_tools.schemas.response
==============================
Standard response DTOs for inter-layer communication.

Usage::

    from codex_tools.schemas import CoreResponseDTO, ResponseHeader

    header = ResponseHeader(success=True, message="OK")
    response = CoreResponseDTO[MyPayload](header=header, payload=my_data)
"""

from pydantic import BaseModel


class ResponseHeader(BaseModel):
    """
    Метаданные ответа.
    Управляют состоянием бота и сообщают об ошибках.
    """

    success: bool = True
    message: str | None = None

    # Откуда мы пришли (для логирования / навигации)
    current_state: str | None = None

    # Куда переключить FSM (если None — остаёмся где были)
    next_state: str | None = None

    # Trace ID для логов
    trace_id: str | None = None


class CoreResponseDTO[T](BaseModel):
    """
    Стандартный ответ: Заголовок + Данные.
    Используется для обмена данными между слоями (Client → Orchestrator).

    Generic type parameter T — тип payload.

    Note: Uses PEP 695 syntax (Python 3.12+).
    """

    header: ResponseHeader
    payload: T | None = None
