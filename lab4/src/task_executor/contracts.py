from typing import Protocol, runtime_checkable

from .models import Task


@runtime_checkable
class TaskHandler(Protocol):
    """Поведенческий контракт для асинхронного обработчика задачи."""

    async def handle(self, task: Task) -> None:
        """Обработать задачу.

        Args:
            task: Задача для обработки.

        Raises:
            Exception: Любое исключение в процессе обработки задачи.
        """
        ...


def is_task_handler(value: object) -> bool:
    """Runtime-проверка, что объект поддерживает контракт TaskHandler.

    Args:
        value: Проверяемый объект.

    Returns:
        True, если объект удовлетворяет контракту TaskHandler.
    """
    return isinstance(value, TaskHandler)