from .models import Task
from .queue import TaskQueue


def build_demo_tasks() -> list[Task]:
    return [
        Task(id="task-1", payload={"kind": "email"}, status="new", priority=2),
        Task(id="task-2", payload={"kind": "report"}, status="done", priority=4),
        Task(id="task-3", payload={"kind": "sync"}, status="new", priority=5),
    ]


def main() -> None:
    queue = TaskQueue(build_demo_tasks())

    print("All tasks:")
    for task in queue:
        print(task)

    print("Ready tasks:")
    for task in queue.filter_by_status("new"):
        print(task)

    print("High priority batches:")
    high_priority = TaskQueue(lambda: queue.filter_by_priority(min_priority=4))
    for batch in high_priority.stream_batches(batch_size=2):
        print(batch)


if __name__ == "__main__":
    main()
