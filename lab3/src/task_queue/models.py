from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Task:
    """Minimal task representation for queue processing."""

    id: str
    payload: Any
    status: str = "new"
    priority: int = 3
