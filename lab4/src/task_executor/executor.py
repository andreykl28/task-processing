import asyncio
from collections.abc import Iterable
from typing import Any

from .contracts import TaskHandler, is_task_handler
from .logging import AsyncLogManager
from .models import Task
from .queue import AsyncTaskQueue, is_stop_sentinel


class AsyncTaskExecutor:
    """Асинхронный исполнитель задач.

    Забирает задачи из очереди и распределяет их между зарегистрированными
    обработчиками. Поддерживает graceful shutdown через отмену задачи.
    """

    def __init__(
        self,
        queue: AsyncTaskQueue,
        handlers: Iterable[TaskHandler],
        default_handler: TaskHandler | None = None,
        log_name: str = "executor",
    ) -> None:
        self._queue = queue
        self._handlers = list(handlers)
        self._default_handler = default_handler
        self._log_name = log_name
        self._running = False

        for h in self._handlers:
            if not is_task_handler(h):
                raise TypeError(
                    f"Handler '{type(h).__name__}' does not satisfy TaskHandler protocol"
                )

        if self._default_handler is not None and not is_task_handler(self._default_handler):
            raise TypeError(
                f"Default handler '{type(self._default_handler).__name__}' "
                "does not satisfy TaskHandler protocol"
            )

    async def run(self) -> None:
        """Запустить основной цикл обработки задач.

        Бесконечно забирает задачи из очереди и передаёт их подходящему
        обработчику. Обрабатывает ошибки в обработчиках централизованно.
        Поддерживает graceful shutdown через asyncio.CancelledError.
        """
        self._running = True

        async with AsyncLogManager(self._log_name) as log:
            await log.info("Executor started")

            while self._running:
                try:
                    task = await self._queue.get()
                except asyncio.CancelledError:
                    await log.info("Executor received cancellation signal")
                    self._running = False
                    break

                # Проверка sentinel-сигнала остановки
                if is_stop_sentinel(task):
                    self._queue.task_done()
                    self._running = False
                    await log.info("Executor received stop signal")
                    break

                try:
                    handler = self._resolve_handler(task)
                    await handler.handle(task)
                except asyncio.CancelledError:
                    self._queue.task_done()
                    self._running = False
                    await log.info("Executor cancelled during task processing")
                    break
                except Exception as exc:
                    await log.error(
                        f"Task {task.id} failed: {type(exc).__name__}: {exc}"
                    )
                finally:
                    self._queue.task_done()

            await log.info("Executor stopped")

    def stop(self) -> None:
        """Остановить исполнитель (флаг для завершения после текущей задачи)."""
        self._running = False

    def _resolve_handler(self, task: Task) -> TaskHandler:
        """Выбрать подходящий обработчик для задачи.

        Поиск происходит по типу задачи (task.payload.get("kind")).
        Если специализированный обработчик не найден, используется default_handler.

        Args:
            task: Задача, для которой нужно найти обработчик.

        Returns:
            Подходящий обработчик.

        Raises:
            RuntimeError: Если ни один обработчик не подходит и нет default_handler.
        """
        task_kind = task.payload.get("kind", "") if isinstance(task.payload, dict) else ""

        for handler in self._handlers:
            handler_name = type(handler).__name__.lower()
            if task_kind and task_kind in handler_name:
                return handler

        if self._default_handler is not None:
            return self._default_handler

        raise RuntimeError(
            f"No suitable handler found for task {task.id} (kind='{task_kind}')"
        )