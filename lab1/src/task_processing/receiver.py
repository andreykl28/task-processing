from typing import Iterable

from .contracts import is_task_source
from .models import Task


class TaskReceiver:
    """Модуль приёма задач из любых совместимых источников."""

    def receive(self, sources: Iterable[object]) -> list[Task]:
        result: list[Task] = []

        for source in sources:
            if not is_task_source(source):
                source_name = type(source).__name__
                raise TypeError(
                    f"Source '{source_name}' does not satisfy TaskSource protocol"
                )

            result.extend(source.get_tasks())

        return result
