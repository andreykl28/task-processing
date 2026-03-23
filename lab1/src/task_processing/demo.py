from .receiver import TaskReceiver
from .sources import APITaskSource, FileTaskSource, GeneratedTaskSource, StubTaskAPI


def main() -> None:
    demo_file = "demo_tasks.json"

    file_source = FileTaskSource(demo_file)
    generated_source = GeneratedTaskSource(count=2, prefix="gen")
    api_source = APITaskSource(
        StubTaskAPI(
            [
                {"id": "api-1", "payload": {"source": "api", "priority": "high"}},
                {"id": "api-2", "payload": {"source": "api", "priority": "normal"}},
            ]
        )
    )

    receiver = TaskReceiver()
    tasks = receiver.receive([file_source, generated_source, api_source])

    print(f"Total tasks received: {len(tasks)}")
    for task in tasks:
        print(f"- {task.id}: {task.payload}")


if __name__ == "__main__":
    main()
