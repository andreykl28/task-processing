from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Task:
    """Минимальная структура задачи."""

    id: str
    payload: Any
