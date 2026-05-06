from collections.abc import Callable, Iterable, Iterator, Sized

from .models import Task


TaskSource = Iterable[Task] | Callable[[], Iterable[Task]]


class TaskQueueIterator:
    """Iterator over tasks stored in a queue source."""

    def __init__(self, tasks: Iterable[Task]) -> None:
        self._iterator = iter(tasks)

    def __iter__(self) -> "TaskQueueIterator":
        return self

    def __next__(self) -> Task:
        return next(self._iterator)


class TaskQueue:
    """Reusable task queue with lazy filtering operations."""

    def __init__(self, tasks: TaskSource) -> None:
        self._tasks = tasks

    def __iter__(self) -> TaskQueueIterator:
        return TaskQueueIterator(self._iter_tasks())

    def __len__(self) -> int:
        if isinstance(self._tasks, Sized):
            return len(self._tasks)

        raise TypeError("TaskQueue length is unknown for streaming sources")

    def filter_by_status(self, status: str) -> Iterator[Task]:
        return (task for task in self if task.status == status)

    def filter_by_priority(
        self,
        *,
        min_priority: int | None = None,
        max_priority: int | None = None,
    ) -> Iterator[Task]:
        return (
            task
            for task in self
            if self._matches_priority(task, min_priority, max_priority)
        )

    def stream_batches(self, batch_size: int) -> Iterator[tuple[Task, ...]]:
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than 0")

        batch: list[Task] = []
        for task in self:
            batch.append(task)
            if len(batch) == batch_size:
                yield tuple(batch)
                batch.clear()

        if batch:
            yield tuple(batch)

    def _iter_tasks(self) -> Iterable[Task]:
        if callable(self._tasks):
            return self._tasks()

        return self._tasks

    @staticmethod
    def _matches_priority(
        task: Task,
        min_priority: int | None,
        max_priority: int | None,
    ) -> bool:
        if min_priority is not None and task.priority < min_priority:
            return False
        if max_priority is not None and task.priority > max_priority:
            return False

        return True
