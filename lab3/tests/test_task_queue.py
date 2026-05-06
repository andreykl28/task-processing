from io import StringIO
from contextlib import redirect_stdout

import pytest

from task_queue.demo import main as demo_main
from task_queue.models import Task
from task_queue.queue import TaskQueue, TaskQueueIterator


def make_tasks() -> list[Task]:
    return [
        Task(id="t-1", payload={"kind": "email"}, status="new", priority=1),
        Task(id="t-2", payload={"kind": "report"}, status="done", priority=4),
        Task(id="t-3", payload={"kind": "sync"}, status="new", priority=5),
    ]


def test_queue_supports_for_list_and_sum() -> None:
    queue = TaskQueue(make_tasks())

    ids = [task.id for task in queue]
    priorities_sum = sum(task.priority for task in queue)

    assert ids == ["t-1", "t-2", "t-3"]
    assert list(queue)[0].payload == {"kind": "email"}
    assert priorities_sum == 10


def test_queue_can_be_iterated_multiple_times() -> None:
    queue = TaskQueue(make_tasks())

    first_pass = [task.id for task in queue]
    second_pass = [task.id for task in queue]

    assert first_pass == second_pass


def test_iterator_raises_stop_iteration() -> None:
    iterator = iter(TaskQueue([Task(id="t-1", payload={})]))

    assert isinstance(iterator, TaskQueueIterator)
    assert next(iterator).id == "t-1"

    with pytest.raises(StopIteration):
        next(iterator)


def test_filter_by_status_is_lazy() -> None:
    produced: list[str] = []

    def source():
        for task in make_tasks():
            produced.append(task.id)
            yield task

    queue = TaskQueue(source)
    filtered = queue.filter_by_status("new")

    assert produced == []
    assert next(filtered).id == "t-1"
    assert produced == ["t-1"]


def test_filter_by_status_returns_matching_tasks() -> None:
    queue = TaskQueue(make_tasks())

    assert [task.id for task in queue.filter_by_status("new")] == ["t-1", "t-3"]


def test_filter_by_priority_range() -> None:
    queue = TaskQueue(make_tasks())

    filtered = queue.filter_by_priority(min_priority=2, max_priority=4)

    assert [task.id for task in filtered] == ["t-2"]


def test_stream_batches_processes_tasks_by_chunks() -> None:
    queue = TaskQueue(make_tasks())

    batches = list(queue.stream_batches(batch_size=2))

    assert [[task.id for task in batch] for batch in batches] == [["t-1", "t-2"], ["t-3"]]


def test_stream_batches_rejects_invalid_size() -> None:
    queue = TaskQueue(make_tasks())

    with pytest.raises(ValueError):
        list(queue.stream_batches(batch_size=0))


def test_large_source_is_consumed_lazily() -> None:
    produced = 0

    def source():
        nonlocal produced
        for index in range(100_000):
            produced += 1
            yield Task(id=f"t-{index}", payload={}, status="new", priority=index % 5 + 1)

    queue = TaskQueue(source)
    first_batch = next(queue.stream_batches(batch_size=3))

    assert [task.id for task in first_batch] == ["t-0", "t-1", "t-2"]
    assert produced == 3


def test_len_for_sized_sources() -> None:
    queue = TaskQueue(make_tasks())

    assert len(queue) == 3


def test_len_for_streaming_sources_is_unknown() -> None:
    queue = TaskQueue(lambda: iter(make_tasks()))

    with pytest.raises(TypeError):
        len(queue)


def test_demo_main_runs() -> None:
    captured = StringIO()

    with redirect_stdout(captured):
        demo_main()

    output = captured.getvalue()
    assert "All tasks:" in output
    assert "Ready tasks:" in output
    assert "High priority batches:" in output
