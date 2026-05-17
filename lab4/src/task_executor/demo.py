import asyncio

from .executor import AsyncTaskExecutor
from .handlers import EchoHandler, FailHandler, SlowHandler
from .logging import AsyncLogManager
from .models import Task
from .queue import AsyncTaskQueue


async def main() -> None:
    """Демонстрационный запуск асинхронного исполнителя задач.

    Создаёт очередь, наполняет её тестовыми задачами разных типов,
    запускает исполнитель с набором обработчиков и ожидает завершения.
    """
    async with AsyncLogManager("demo") as log:
        await log.info("Starting demo")

        queue = AsyncTaskQueue(maxsize=10)

        executor = AsyncTaskExecutor(
            queue=queue,
            handlers=[
                EchoHandler(),
                SlowHandler(delay=0.2),
                FailHandler(fail_probability=0.3),
            ],
            default_handler=EchoHandler(),
        )

        # Наполнить очередь тестовыми задачами
        await log.info("Adding tasks to queue")
        tasks = [
            Task(id="echo-1", payload={"kind": "echo", "message": "hello"}),
            Task(id="echo-2", payload={"kind": "echo", "message": "world"}),
            Task(id="slow-1", payload={"kind": "slow", "data": "heavy computation"}),
            Task(id="fail-1", payload={"kind": "fail", "data": "risky operation"}),
            Task(id="fail-2", payload={"kind": "fail", "data": "another risky"}),
            Task(id="echo-3", payload={"kind": "echo", "message": "done"}),
        ]
        for task in tasks:
            await queue.put(task)

        # Запустить исполнитель и дождаться завершения
        await log.info(f"Queued {len(tasks)} tasks, starting executor")

        # Отправить сигнал остановки после добавления всех задач
        await queue.stop()

        await executor.run()

        await log.info("Demo finished")


if __name__ == "__main__":
    asyncio.run(main())