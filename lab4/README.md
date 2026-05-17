# Лабораторная работа №4: Асинхронный исполнитель задач

## Цель

Реализовать асинхронный исполнитель задач, обрабатывающий задачи из очереди с использованием расширяемых обработчиков.

## Реализация

- Контракт обработчика: `src/task_executor/contracts.py`
  - `TaskHandler(Protocol)` + `@runtime_checkable`
  - runtime-проверка: `is_task_handler(...)`
- Модель задачи: `src/task_executor/models.py`
  - `Task` с полями `id`, `payload`, `status`, `priority`
- Асинхронная очередь: `src/task_executor/queue.py`
  - `AsyncTaskQueue` — обёртка над `asyncio.Queue`
  - `TaskQueueManager` — асинхронный контекстный менеджер управления очередью
- Контекстный менеджер логирования: `src/task_executor/logging.py`
  - `AsyncLogManager` — структурированное логирование с `__aenter__`/`__aexit__`
- Исполнитель: `src/task_executor/executor.py`
  - `AsyncTaskExecutor` — воркер, забирающий задачи из очереди и передающий их обработчикам
  - роутинг по типу задачи (через `task.payload["kind"]`)
  - централизованная обработка ошибок
  - graceful shutdown
- Обработчики: `src/task_executor/handlers.py`
  - `EchoHandler` — логирует задачу
  - `SlowHandler` — имитирует долгую обработку
  - `FailHandler` — иногда падает с исключением
- Демо-запуск: `src/task_executor/demo.py`
- Тесты: `tests/test_task_executor.py`

## Запуск через Docker

### 1) Сборка образа
```bash
cd lab4
docker build -t task-executor-lab4 .
```

### 2) Запуск демо
```bash
docker run --rm task-executor-lab4
```

По умолчанию выполняется `python3 -m task_executor`.

### 3) Запуск тестов в контейнере
```bash
docker run --rm task-executor-lab4 pytest
```

Порог покрытия уже зашит в конфиг (`--cov-fail-under=80`).
Если покрытие станет ниже 80%, команда завершится ошибкой.

## Локальный запуск

```bash
cd lab4
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
python -m task_executor
pytest
```

## Пример использования

```python
import asyncio
from task_executor import Task, AsyncTaskQueue, AsyncTaskExecutor, EchoHandler

async def main():
    queue = AsyncTaskQueue()
    executor = AsyncTaskExecutor(queue, [EchoHandler()])

    for i in range(5):
        await queue.put(Task(id=f"t-{i}", payload={"kind": "echo"}))

    await asyncio.gather(
        executor.run(),
        queue.join(),
    )

asyncio.run(main())
```

## Итог

Реализована асинхронная система обработки задач:
- асинхронная очередь с корректным управлением жизненным циклом;
- контракт обработчика через `Protocol` с runtime-проверкой;
- контекстные менеджеры для логирования и управления очередью;
- централизованное логирование и обработка ошибок;
- архитектура, допускающая добавление новых типов задач и обработчиков без изменения существующего кода.