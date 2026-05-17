import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Self

from .logging import AsyncLogManager
from .models import Task


# Специальный sentinel-объект для сигнала остановки
_STOP_SENTINEL: Task | None = None


def _make_stop_sentinel() -> Task:
    """Создать sentinel-задачу для остановки исполнителя."""
    return Task(id="__STOP__", payload={})


def is_stop_sentinel(task: Task) -> bool:
    """Проверить, является ли задача sentinel-сигналом остановки."""
    return task.id == "__STOP__"


class AsyncTaskQueue:
    """Асинхронная очередь задач на базе asyncio.Queue.

    Предоставляет методы put/get/task_done/join и поддерживает
    использование в качестве асинхронного итератора.
    """

    def __init__(self, maxsize: int = 0) -> None:
        self._queue: asyncio.Queue[Task] = asyncio.Queue(maxsize=maxsize)

    async def put(self, task: Task) -> None:
        """Добавить задачу в очередь.

        Args:
            task: Задача для добавления.
        """
        await self._queue.put(task)

    async def get(self) -> Task:
        """Извлечь задачу из очереди. Блокирует, пока задача не появится.

        Returns:
            Извлечённая задача.
        """
        return await self._queue.get()

    def qsize(self) -> int:
        """Текущий размер очереди.

        Returns:
            Количество задач в очереди.
        """
        return self._queue.qsize()

    def task_done(self) -> None:
        """Сообщить, что задача обработана."""
        self._queue.task_done()

    async def join(self) -> None:
        """Дождаться обработки всех задач в очереди."""
        await self._queue.join()

    async def stop(self) -> None:
        """Отправить sentinel-сигнал для остановки исполнителя."""
        await self.put(_make_stop_sentinel())

    def __aiter__(self) -> "AsyncTaskQueue":
        return self

    async def __anext__(self) -> Task:
        """Асинхронная итерация по задачам в очереди."""
        try:
            return await self._queue.get()
        except asyncio.CancelledError:
            raise StopAsyncIteration


class TaskQueueManager:
    """Асинхронный контекстный менеджер для управления жизненным циклом очереди.

    Использование:
        async with TaskQueueManager(maxsize=10) as queue:
            await queue.put(Task(...))
            ...
    """

    def __init__(self, maxsize: int = 0, log_name: str = "queue") -> None:
        self._maxsize = maxsize
        self._log_name = log_name
        self._log: AsyncLogManager | None = None

    async def __aenter__(self) -> AsyncTaskQueue:
        """Создать очередь и залогировать её создание."""
        self._log = AsyncLogManager(self._log_name)
        await self._log.__aenter__()
        self._queue = AsyncTaskQueue(maxsize=self._maxsize)
        await self._log.info(f"Queue created (maxsize={self._maxsize})")
        return self._queue

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Дождаться завершения обработки и закрыть логгер."""
        if self._queue.qsize() > 0:
            await self._queue.join()

        if self._log is not None:
            await self._log.__aexit__(exc_type, exc_val, exc_tb)