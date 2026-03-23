from typing import Iterable, Protocol, TypeGuard, runtime_checkable

from .models import Task


@runtime_checkable
class TaskSource(Protocol):
    """Поведенческий контракт для любого источника задач."""

    def get_tasks(self) -> Iterable[Task]:
        ...


def is_task_source(value: object) -> TypeGuard[TaskSource]:
    """Runtime-проверка, что объект поддерживает контракт TaskSource."""

    return isinstance(value, TaskSource)


def is_task_source_class(value: type[object]) -> bool:
    """Проверка класса на структурную совместимость с TaskSource."""

    return issubclass(value, TaskSource)
