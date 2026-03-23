# Лабораторная работа №1: Источники задач и контракты

## Цель
Собрать модуль приёма задач, который работает с разными источниками через единый поведенческий контракт `TaskSource` на базе `typing.Protocol`.

## Реализация

- Контракт источника: `src/task_processing/contracts.py`
  - `TaskSource(Protocol)` + `@runtime_checkable`
  - runtime-проверки: `is_task_source(...)` и `is_task_source_class(...)`
- Представление задачи: `src/task_processing/models.py`
  - `Task` с полями `id` и `payload`
- Источники задач (без общего базового класса): `src/task_processing/sources.py`
  - `FileTaskSource` (чтение из JSON)
  - `GeneratedTaskSource` (программная генерация)
  - `APITaskSource` + `StubTaskAPI` (API-заглушка)
- Модуль приёма: `src/task_processing/receiver.py`
  - `TaskReceiver.receive(...)` принимает любые источники, удовлетворяющие контракту
- Демо-запуск: `src/task_processing/demo.py`
- Тесты: `tests/test_task_processing.py`

## Файловый источник: формат своего JSON

`FileTaskSource` читает любой JSON-файл такого вида:

```json
[
  {"id": "custom-1", "payload": {"kind": "email", "to": "user@example.com"}},
  {"id": "custom-2", "payload": {"kind": "report", "period": "2026-03"}}
]
```

Условия валидности:
- корневой элемент — список;
- каждый элемент содержит `id` и `payload`.

## Мини-пример объединения источников

```python
from task_processing.receiver import TaskReceiver
from task_processing.sources import FileTaskSource, GeneratedTaskSource, APITaskSource, StubTaskAPI

sources = [
    FileTaskSource("demo_tasks.json"),
    GeneratedTaskSource(count=2, prefix="gen"),
    APITaskSource(StubTaskAPI([
        {"id": "api-1", "payload": {"kind": "sync", "target": "crm"}},
    ])),
]

tasks = TaskReceiver().receive(sources)
for task in tasks:
    print(task.id, task.payload)
```

## Ожидаемый результат

На выходе получаешь единый список задач из всех источников, обработанных через общий контракт `TaskSource`, без наследования от общей базовой реализации.

## Запуск через Docker

### 1) Сборка образа
```bash
cd lab1
docker build -t task-processing-lab1 .
```

### 2) Запуск демо
```bash
docker run --rm task-processing-lab1
```

По умолчанию выполняется `python3 -m task_processing`.
Демо использует `demo_tasks.json` из корня проекта.

### 3) Запуск тестов в контейнере
```bash
docker run --rm task-processing-lab1 pytest
```

Порог покрытия уже зашит в конфиг (`--cov-fail-under=80`).
Если покрытие станет ниже 80%, команда завершится ошибкой.

## Локальный запуск

```bash
cd lab1
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
python -m task_processing
pytest
```
