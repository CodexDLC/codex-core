"""
codex_tools.core.interfaces
============================
Protocol contracts for adapters.
The library core relies only on these interfaces, not on concrete ORM models.
Implement these protocols when building a new adapter (Django, FastAPI, etc.).
"""

from __future__ import annotations

from datetime import date, datetime, time
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from codex_tools.booking.dto import MasterAvailability


class ScheduleProvider(Protocol):
    """Provides working schedules for professionals."""

    def get_working_hours(self, master_id: str, target_date: date) -> tuple[time, time] | None:
        """Return (start, end) of working day or None if day off."""
        ...

    def get_break_interval(self, master_id: str, target_date: date) -> tuple[datetime, datetime] | None:
        """Return (start, end) of break or None."""
        ...


class BusySlotsProvider(Protocol):
    """Provides busy time slots for professionals."""

    def get_busy_intervals(
        self, master_ids: list[str], target_date: date
    ) -> dict[str, list[tuple[datetime, datetime]]]:
        """Return {master_id: [(start, end), ...]} of busy times."""
        ...


class AvailabilityProvider(Protocol):
    """
    Full availability provider — the main adapter contract.
    Implement this protocol for each framework adapter (Django, SQLAlchemy, etc.).
    """

    def build_masters_availability(
        self,
        master_ids: list[str],
        target_date: date,
        cache_ttl: int = 300,
        exclude_appointment_ids: list[int] | None = None,
    ) -> dict[str, MasterAvailability]:
        """Build availability for a single date. Return {master_id: MasterAvailability}."""
        ...

    def build_availability_batch(
        self,
        master_ids: list[str],
        start_date: date,
        end_date: date,
    ) -> dict[date, dict[str, MasterAvailability]]:
        """
        Build availability for a date range in a single batch.
        Must avoid N+1 queries — group appointments in memory.
        Return {date: {master_id: MasterAvailability}}.
        """
        ...


class ContentProvider(Protocol):
    """Provides translated template text by key."""

    def get_text(self, key: str) -> str | None:
        """Return translated text or None if not found."""
        ...


class ContentCacheAdapter(Protocol):
    """Adapter for caching email/notification content (used by BaseEmailContentSelector)."""

    def get_cached_value(self, key: str) -> str | None:
        """Return cached string value or None if not found."""
        ...

    def set_cached_value(self, key: str, value: str, timeout: int) -> None:
        """Store value in cache with given timeout (seconds)."""
        ...


# NotificationAdapter was moved to codex_tools.notifications.adapters.base
