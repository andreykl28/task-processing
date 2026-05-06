# Лабораторная работа №3: Очередь задач, итераторы и генераторы

## Цель
Реализовать коллекцию `TaskQueue`, которая поддерживает итерацию, повторный обход, ленивую фильтрацию и потоковую обработку задач.

## Реализация

- Модель задачи: `src/task_queue/models.py`
  - `Task` с полями `id`, `payload`, `status`, `priority`
- Очередь задач: `src/task_queue/queue.py`
  - `TaskQueue` как пользовательская коллекция
  - `TaskQueueIterator` для протокола итерации
  - поддержка `for`, `list`, `sum`
  - повторный обход очереди
  - ленивые фильтры `filter_by_status(...)` и `filter_by_priority(...)`
  - потоковая обработка через `stream_batches(...)`
- Демо-запуск: `src/task_queue/demo.py`
- Тесты: `tests/test_task_queue.py`

## Запуск через Docker

### 1) Сборка образа
```bash
cd lab3
docker build -t task-queue-lab3 .
```

### 2) Запуск демо
```bash
docker run --rm task-queue-lab3
```

### 3) Запуск тестов
```bash
docker run --rm task-queue-lab3 pytest
```

Порог покрытия включён в конфиг: `--cov-fail-under=80`.

## Локальный запуск

```bash
cd lab3
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
python -m task_queue
pytest
```

## Пример использования

```python
from task_queue import Task, TaskQueue

tasks = [
    Task(id="t-1", payload={"kind": "email"}, status="new", priority=2),
    Task(id="t-2", payload={"kind": "report"}, status="done", priority=4),
]

queue = TaskQueue(tasks)

for task in queue.filter_by_status("new"):
    print(task.id)

for batch in queue.stream_batches(batch_size=2):
    print(batch)
```

## Итог

Реализована очередь задач с корректным протоколом итерации:
- очередь можно обходить повторно;
- фильтры работают лениво через генераторы;
- большие источники задач не требуют предварительного сохранения всего набора в память;
- ручное исчерпание итератора корректно завершается `StopIteration`.
