# Лабораторная работа №2: Модель задачи, дескрипторы и @property

## Цель
Реализовать безопасную доменную модель `Task` с инкапсуляцией, валидацией атрибутов и защитой инвариантов.

## Реализация

- Модель задачи: `src/task_model/models.py`
  - атрибуты: `id`, `description`, `priority`, `status`, `created_at`
  - вычисляемые свойства: `is_ready_for_execution`, `can_be_edited`
  - read-only `created_at` через `@property`
- Дескрипторы: `src/task_model/descriptors.py`
  - data descriptors: `TaskIdDescriptor`, `DescriptionDescriptor`, `PriorityDescriptor`, `StatusDescriptor`
  - non-data descriptor: `RuntimeNoteDescriptor`
- Исключения инвариантов: `src/task_model/exceptions.py`
  - `InvalidTaskIdError`, `InvalidDescriptionError`, `InvalidPriorityError`, `InvalidStatusError`,
    `InvalidCreatedAtError`, `InvalidStatusTransitionError`
- Тесты: `tests/test_task_model.py`
  - валидация атрибутов
  - переходы статусов
  - различия data/non-data descriptors
  - проверка `@property`

## Что это за лаба и в чем суть

Эта работа про то, как не допускать "ломаное" состояние объекта.
`Task` нельзя создать с пустым id, плохим приоритетом или неверным статусом.
Все такие случаи ловятся сразу и выбрасывают специализированные исключения.

Также показывается разница:
- data descriptor (с `__set__`) контролирует запись и не даёт обойти валидацию обычным присваиванием;
- non-data descriptor (только `__get__`) можно переопределить на уровне экземпляра.

## Запуск через Docker

### 1) Сборка образа
```bash
cd lab2
docker build -t task-model-lab2 .
```

### 2) Запуск демо
```bash
docker run --rm task-model-lab2
```

### 3) Запуск тестов
```bash
docker run --rm task-model-lab2 pytest
```

Порог покрытия уже включён в конфиг: `--cov-fail-under=80`.

## Локальный запуск

```bash
cd lab2
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e .
python -m task_model
pytest
```

## Итог

Сделан чистый и безопасный публичный API для `Task`:
- валидация атрибутов через пользовательские дескрипторы;
- вычисляемые и защищённые свойства через `@property`;
- контроль инвариантов и понятные специализированные исключения.
