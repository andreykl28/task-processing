import asyncio
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Self


class AsyncLogManager:
    """Асинхронный контекстный менеджер для структурированного логирования.

    Использование:
        async with AsyncLogManager("executor") as log:
            await log.info("Start processing")
            ...
    """

    def __init__(self, name: str, level: int = logging.INFO) -> None:
        self._name = name
        self._level = level
        self._logger = logging.getLogger(name)
        self._handler: logging.Handler | None = None

    async def __aenter__(self) -> Self:
        """Открыть контекст логирования: настроить обработчик и записать START."""
        loop = asyncio.get_running_loop()

        def _setup() -> None:
            self._logger.setLevel(self._level)
            self._handler = logging.StreamHandler()
            formatter = logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S%z",
            )
            self._handler.setFormatter(formatter)
            self._logger.addHandler(self._handler)

        await loop.run_in_executor(None, _setup)
        await self._emit("START", logging.INFO)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Закрыть контекст логирования: записать END/ERROR и убрать обработчик."""
        if exc_type is not None:
            await self._emit(f"ERROR: {exc_type.__name__}: {exc_val}", logging.ERROR)
        else:
            await self._emit("END", logging.INFO)

        if self._handler is not None:
            loop = asyncio.get_running_loop()

            def _cleanup() -> None:
                self._logger.removeHandler(self._handler)
                self._handler.close()

            await loop.run_in_executor(None, _cleanup)

    async def info(self, message: str) -> None:
        """Записать информационное сообщение.

        Args:
            message: Текст сообщения.
        """
        await self._emit(message, logging.INFO)

    async def error(self, message: str) -> None:
        """Записать сообщение об ошибке.

        Args:
            message: Текст сообщения.
        """
        await self._emit(message, logging.ERROR)

    async def _emit(self, message: str, level: int) -> None:
        """Записать лог с указанным уровнем (вспомогательный метод)."""
        loop = asyncio.get_running_loop()

        def _log() -> None:
            self._logger.log(level, message)

        await loop.run_in_executor(None, _log)


@asynccontextmanager
async def async_log_context(name: str, level: int = logging.INFO) -> AsyncIterator[AsyncLogManager]:
    """Функция-обёртка для использования AsyncLogManager как асинхронного контекстного менеджера.

    Args:
        name: Имя логгера.
        level: Уровень логирования.

    Yields:
        Экземпляр AsyncLogManager.
    """
    async with AsyncLogManager(name, level) as log:
        yield log