from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .descriptors import (
    DescriptionDescriptor,
    PriorityDescriptor,
    RuntimeNoteDescriptor,
    StatusDescriptor,
    TaskIdDescriptor,
)
from .exceptions import InvalidCreatedAtError


class Task:
    """Доменная модель задачи с валидацией и защитой инвариантов."""

    id = TaskIdDescriptor()
    description = DescriptionDescriptor()
    priority = PriorityDescriptor()
    status = StatusDescriptor()

    # non-data descriptor for demonstration purposes
    runtime_note = RuntimeNoteDescriptor()

    def __init__(
        self,
        id: str,
        description: str,
        priority: int = 3,
        status: str = "new",
        created_at: datetime | None = None,
    ) -> None:
        self.id = id
        self.description = description
        self.priority = priority

        if created_at is None:
            self._created_at = datetime.now(timezone.utc)
        else:
            if not isinstance(created_at, datetime) or created_at.tzinfo is None:
                raise InvalidCreatedAtError("created_at must be a timezone-aware datetime")
            self._created_at = created_at

        self.status = status

    @property
    def created_at(self) -> datetime:
        """Read-only время создания задачи."""

        return self._created_at

    @property
    def is_ready_for_execution(self) -> bool:
        """Вычисляемое свойство готовности задачи к выполнению."""

        return self.status in {"new", "in_progress"}

    @property
    def can_be_edited(self) -> bool:
        """После перехода в done задача считается неизменяемой."""

        return self.status != "done"

    def to_dict(self) -> dict[str, Any]:
        """Публичное представление задачи для сериализации/логирования."""

        return {
            "id": self.id,
            "description": self.description,
            "priority": self.priority,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "is_ready_for_execution": self.is_ready_for_execution,
            "can_be_edited": self.can_be_edited,
        }
