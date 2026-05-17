from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Task:
    """Единица работы в асинхронной системе обработки задач.

    Attributes:
        id: Уникальный идентификатор задачи.
        payload: Произвольные данные задачи.
        status: Текущий статус задачи.
        priority: Приоритет задачи (1 — наивысший, 5 — наинизший).
    """

    id: str
    payload: Any
    status: str = "new"
    priority: int = 3