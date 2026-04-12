class TaskValidationError(ValueError):
    """Базовая ошибка валидации модели задачи."""


class InvalidTaskIdError(TaskValidationError):
    """Некорректный идентификатор задачи."""


class InvalidDescriptionError(TaskValidationError):
    """Некорректное описание задачи."""


class InvalidPriorityError(TaskValidationError):
    """Некорректный приоритет задачи."""


class InvalidStatusError(TaskValidationError):
    """Некорректный статус задачи."""


class InvalidCreatedAtError(TaskValidationError):
    """Некорректное время создания задачи."""


class InvalidStatusTransitionError(TaskValidationError):
    """Недопустимый переход статуса задачи."""
