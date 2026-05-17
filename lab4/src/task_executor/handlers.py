import asyncio
import random

from .logging import AsyncLogManager
from .models import Task


class EchoHandler:
    """Простой обработчик: логирует задачу и завершается."""

    async def handle(self, task: Task) -> None:
        """Вывести информацию о задаче.

        Args:
            task: Обрабатываемая задача.
        """
        async with AsyncLogManager("EchoHandler") as log:
            await log.info(f"Processing task {task.id} with payload {task.payload}")
            await asyncio.sleep(0.05)


class SlowHandler:
    """Обработчик, имитирующий долгую обработку задачи."""

    def __init__(self, delay: float = 0.3) -> None:
        self._delay = delay

    async def handle(self, task: Task) -> None:
        """Обработать задачу с искусственной задержкой.

        Args:
            task: Обрабатываемая задача.
        """
        async with AsyncLogManager("SlowHandler") as log:
            await log.info(f"Slow processing task {task.id} (delay={self._delay}s)")
            await asyncio.sleep(self._delay)
            await log.info(f"Finished task {task.id}")


class FailHandler:
    """Обработчик, который иногда падает с исключением (для проверки error handling)."""

    def __init__(self, fail_probability: float = 0.3) -> None:
        if not 0.0 <= fail_probability <= 1.0:
            raise ValueError("fail_probability must be between 0.0 and 1.0")
        self._fail_probability = fail_probability

    async def handle(self, task: Task) -> None:
        """Обработать задачу с вероятностью ошибки.

        Args:
            task: Обрабатываемая задача.

        Raises:
            RuntimeError: С вероятностью fail_probability.
        """
        async with AsyncLogManager("FailHandler") as log:
            await log.info(f"Processing task {task.id} (fail_prob={self._fail_probability})")

            if random.random() < self._fail_probability:
                await log.error(f"Task {task.id} failed!")
                raise RuntimeError(f"Task {task.id} processing failed")

            await asyncio.sleep(0.05)
            await log.info(f"Task {task.id} completed successfully")