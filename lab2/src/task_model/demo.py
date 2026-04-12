from .models import Task


def main() -> None:
    task = Task(
        id="task-1",
        description="Send a notification to user",
        priority=2,
        status="new",
    )

    print("Created task:")
    print(task.to_dict())

    task.status = "in_progress"
    print("After status update:")
    print(task.to_dict())


if __name__ == "__main__":
    main()
