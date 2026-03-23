import json
from pathlib import Path
from typing import Any, Iterable, Protocol

from .models import Task


class APIClient(Protocol):
    """Минимальный контракт внешнего API-клиента."""

    def fetch_tasks(self) -> Iterable[dict[str, Any]]:
        ...


class FileTaskSource:
    """Источник задач из JSON-файла."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    def get_tasks(self) -> list[Task]:
        raw_items = json.loads(self._path.read_text(encoding="utf-8"))
        if not isinstance(raw_items, list):
            raise ValueError("FileTaskSource expects a JSON list of tasks")

        return [self._to_task(item) for item in raw_items]

    @staticmethod
    def _to_task(item: object) -> Task:
        if not isinstance(item, dict):
            raise ValueError("Task item must be a JSON object")
        if "id" not in item or "payload" not in item:
            raise ValueError("Task item must contain 'id' and 'payload'")

        return Task(id=str(item["id"]), payload=item["payload"])


class GeneratedTaskSource:
    """Источник задач, генерируемых программно."""

    def __init__(self, count: int, prefix: str = "generated") -> None:
        if count < 0:
            raise ValueError("count must be >= 0")

        self._count = count
        self._prefix = prefix

    def get_tasks(self) -> Iterable[Task]:
        for idx in range(1, self._count + 1):
            yield Task(id=f"{self._prefix}-{idx}", payload={"index": idx})


class StubTaskAPI:
    """Упрощённая API-заглушка внешнего сервиса."""

    def __init__(self, tasks: Iterable[dict[str, Any]]) -> None:
        self._tasks = list(tasks)

    def fetch_tasks(self) -> list[dict[str, Any]]:
        return list(self._tasks)


class APITaskSource:
    """Источник задач из API-заглушки."""

    def __init__(self, api_client: APIClient) -> None:
        self._api_client = api_client

    def get_tasks(self) -> list[Task]:
        result: list[Task] = []

        for item in self._api_client.fetch_tasks():
            if "id" not in item or "payload" not in item:
                raise ValueError("API task must contain 'id' and 'payload'")

            result.append(Task(id=str(item["id"]), payload=item["payload"]))

        return result
