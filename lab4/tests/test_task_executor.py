import asyncio
from io import StringIO
from contextlib import redirect_stdout
from unittest.mock import patch

import pytest

from task_executor import (
    AsyncLogManager,
    AsyncTaskExecutor,
    AsyncTaskQueue,
    EchoHandler,
    FailHandler,
    SlowHandler,
    Task,
    TaskHandler,
    TaskQueueManager,
    is_task_handler,
)


# ─── Model ───────────────────────────────────────────────────────────────

def test_task_creation() -> None:
    task = Task(id="t-1", payload={"kind": "echo"}, status="new", priority=2)
    assert task.id == "t-1"
    assert task.payload == {"kind": "echo"}
    assert task.status == "new"
    assert task.priority == 2


def test_task_defaults() -> None:
    task = Task(id="t-1", payload={})
    assert task.status == "new"
    assert task.priority == 3


def test_task_is_frozen() -> None:
    task = Task(id="t-1", payload={})
    with pytest.raises(AttributeError):
        task.id = "other"  # type: ignore[misc]


# ─── Contracts ──────────────────────────────────────────────────────────

class ValidHandler:
    async def handle(self, task: Task) -> None:
        pass


class InvalidHandler:
    pass


def test_is_task_handler_with_valid_handler() -> None:
    assert is_task_handler(ValidHandler()) is True


def test_is_task_handler_with_invalid_handler() -> None:
    assert is_task_handler(InvalidHandler()) is False


def test_is_task_handler_with_object() -> None:
    assert is_task_handler(object()) is False


def test_runtime_checkable_via_isinstance() -> None:
    assert isinstance(ValidHandler(), TaskHandler) is True
    assert isinstance(InvalidHandler(), TaskHandler) is False


# ─── Handlers ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_echo_handler_processes_task() -> None:
    handler = EchoHandler()
    task = Task(id="echo-1", payload={"kind": "echo"})
    await handler.handle(task)
    # Просто проверяем, что не падает


@pytest.mark.asyncio
async def test_slow_handler_processes_task() -> None:
    handler = SlowHandler(delay=0.05)
    task = Task(id="slow-1", payload={"kind": "slow"})
    await handler.handle(task)


@pytest.mark.asyncio
async def test_fail_handler_can_succeed() -> None:
    handler = FailHandler(fail_probability=0.0)
    task = Task(id="ok-1", payload={"kind": "fail"})
    await handler.handle(task)


@pytest.mark.asyncio
async def test_fail_handler_can_fail() -> None:
    handler = FailHandler(fail_probability=1.0)
    task = Task(id="fail-1", payload={"kind": "fail"})
    with pytest.raises(RuntimeError, match="Task fail-1 processing failed"):
        await handler.handle(task)


def test_fail_handler_rejects_invalid_probability() -> None:
    with pytest.raises(ValueError, match="fail_probability must be between 0.0 and 1.0"):
        FailHandler(fail_probability=-0.1)

    with pytest.raises(ValueError, match="fail_probability must be between 0.0 and 1.0"):
        FailHandler(fail_probability=1.5)


# ─── Async Queue ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_async_queue_put_and_get() -> None:
    queue = AsyncTaskQueue()
    task = Task(id="t-1", payload={})

    await queue.put(task)
    assert queue.qsize() == 1

    retrieved = await queue.get()
    assert retrieved.id == "t-1"
    queue.task_done()

    assert queue.qsize() == 0


@pytest.mark.asyncio
async def test_async_queue_join() -> None:
    queue = AsyncTaskQueue()
    await queue.put(Task(id="t-1", payload={}))
    await queue.put(Task(id="t-2", payload={}))

    task1 = await queue.get()
    task2 = await queue.get()
    queue.task_done()
    queue.task_done()

    await queue.join()


@pytest.mark.asyncio
async def test_async_queue_iteration() -> None:
    queue = AsyncTaskQueue()
    await queue.put(Task(id="t-1", payload={}))
    await queue.put(Task(id="t-2", payload={}))

    # Завершим задачи, чтобы итерация могла закончиться
    async def drain() -> None:
        collected = []
        async for task in queue:
            collected.append(task.id)
            queue.task_done()
            if len(collected) == 2:
                break
        return collected

    tasks = await drain()
    assert tasks == ["t-1", "t-2"]


# ─── Task Queue Manager (context manager) ───────────────────────────────

@pytest.mark.asyncio
async def test_task_queue_manager_context() -> None:
    async with TaskQueueManager(maxsize=5) as queue:
        assert isinstance(queue, AsyncTaskQueue)
        await queue.put(Task(id="t-1", payload={}))
        await queue.put(Task(id="t-2", payload={}))

        t1 = await queue.get()
        t2 = await queue.get()
        queue.task_done()
        queue.task_done()


# ─── Executor ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_executor_processes_all_tasks() -> None:
    queue = AsyncTaskQueue()
    handler = EchoHandler()
    executor = AsyncTaskExecutor(queue, [handler], default_handler=handler)

    tasks = [
        Task(id="t-1", payload={"kind": "echo", "msg": "a"}),
        Task(id="t-2", payload={"kind": "echo", "msg": "b"}),
    ]
    for t in tasks:
        await queue.put(t)

    # Отправить сигнал остановки после задач
    await queue.stop()

    # Запускаем executor и ждём завершения
    await executor.run()


@pytest.mark.asyncio
async def test_executor_detects_invalid_handler() -> None:
    queue = AsyncTaskQueue()

    with pytest.raises(TypeError, match="does not satisfy TaskHandler protocol"):
        AsyncTaskExecutor(queue, [InvalidHandler()])


@pytest.mark.asyncio
async def test_executor_detects_invalid_default_handler() -> None:
    queue = AsyncTaskQueue()

    with pytest.raises(TypeError, match="does not satisfy TaskHandler protocol"):
        AsyncTaskExecutor(queue, [ValidHandler()], default_handler=InvalidHandler())  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_executor_handles_task_failures() -> None:
    queue = AsyncTaskQueue()
    handler = FailHandler(fail_probability=1.0)
    executor = AsyncTaskExecutor(queue, [handler])

    await queue.put(Task(id="fail-1", payload={"kind": "fail"}))
    await queue.stop()

    await executor.run()


@pytest.mark.asyncio
async def test_executor_graceful_stop() -> None:
    queue = AsyncTaskQueue()
    handler = EchoHandler()
    executor = AsyncTaskExecutor(queue, [handler])

    # Создаём задачу, которая будет обработана
    await queue.put(Task(id="t-1", payload={"kind": "echo"}))
    await queue.stop()

    await executor.run()


@pytest.mark.asyncio
async def test_executor_resolve_handler_routing() -> None:
    queue = AsyncTaskQueue()

    class CustomHandler:
        async def handle(self, task: Task) -> None:
            pass

    handler = CustomHandler()
    echo_handler = EchoHandler()
    executor = AsyncTaskExecutor(
        queue,
        [handler, echo_handler],
        default_handler=echo_handler,
    )

    # Проверяем _resolve_handler для разных типов
    task_echo = Task(id="e-1", payload={"kind": "echo"})
    resolved = executor._resolve_handler(task_echo)
    assert isinstance(resolved, EchoHandler)

    task_custom = Task(id="c-1", payload={"kind": "custom"})
    resolved = executor._resolve_handler(task_custom)
    # Имя класса CustomHandler содержит "custom", поэтому роутинг находит его
    assert isinstance(resolved, CustomHandler)


@pytest.mark.asyncio
async def test_executor_raises_on_no_handler_for_kind() -> None:
    queue = AsyncTaskQueue()
    executor = AsyncTaskExecutor(queue, [EchoHandler()])

    task = Task(id="no-match", payload={"kind": "unknown"})
    with pytest.raises(RuntimeError, match="No suitable handler found"):
        executor._resolve_handler(task)


# ─── Async Log Manager ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_async_log_manager_context() -> None:
    async with AsyncLogManager("test_logger") as log:
        await log.info("test message")
        await log.error("test error")


@pytest.mark.asyncio
async def test_async_log_manager_logs_start_end() -> None:
    log = AsyncLogManager("test_logger")
    await log.__aenter__()
    await log.__aexit__(None, None, None)


@pytest.mark.asyncio
async def test_async_log_manager_logs_error_on_exception() -> None:
    log = AsyncLogManager("test_logger")
    await log.__aenter__()
    await log.__aexit__(ValueError, ValueError("test error"), None)


# ─── Demo ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_demo_main_runs() -> None:
    from task_executor.demo import main

    await main()


# ─── New handler can be added without changing existing code ────────────

@pytest.mark.asyncio
async def test_new_handler_can_be_added_without_changing_executor() -> None:
    """Проверяет архитектурную расширяемость: новый обработчик подключается
    без изменения существующего кода исполнителя."""

    class NewHandler:
        processed: list[str] = []

        async def handle(self, task: Task) -> None:
            NewHandler.processed.append(task.id)

    queue = AsyncTaskQueue()
    handler = NewHandler()
    executor = AsyncTaskExecutor(queue, [handler], default_handler=handler)

    await queue.put(Task(id="new-task", payload={"kind": "new"}))
    await queue.stop()

    await executor.run()

    assert NewHandler.processed == ["new-task"]
