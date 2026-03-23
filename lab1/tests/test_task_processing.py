import json
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from contextlib import redirect_stdout

from task_processing import (
    APITaskSource,
    FileTaskSource,
    GeneratedTaskSource,
    StubTaskAPI,
    Task,
    TaskReceiver,
    TaskSource,
    is_task_source_class,
)
from task_processing.contracts import is_task_source
from task_processing.demo import main as demo_main


class TaskProcessingTests(unittest.TestCase):
    def test_receiver_collects_tasks_from_all_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "tasks.json"
            file_path.write_text(
                json.dumps(
                    [
                        {"id": "f-1", "payload": {"kind": "file"}},
                        {"id": "f-2", "payload": {"kind": "file"}},
                    ]
                ),
                encoding="utf-8",
            )

            file_source = FileTaskSource(file_path)
            generated_source = GeneratedTaskSource(count=2, prefix="g")
            api_source = APITaskSource(
                StubTaskAPI(
                    [
                        {"id": "api-1", "payload": {"kind": "api"}},
                    ]
                )
            )

            receiver = TaskReceiver()
            tasks = receiver.receive([file_source, generated_source, api_source])

        self.assertEqual([task.id for task in tasks], ["f-1", "f-2", "g-1", "g-2", "api-1"])

    def test_runtime_protocol_checks(self) -> None:
        self.assertTrue(is_task_source_class(FileTaskSource))
        self.assertTrue(issubclass(GeneratedTaskSource, TaskSource))
        self.assertTrue(isinstance(GeneratedTaskSource(count=1), TaskSource))
        self.assertFalse(is_task_source(object()))

    def test_receiver_rejects_invalid_source(self) -> None:
        class InvalidSource:
            pass

        receiver = TaskReceiver()

        with self.assertRaises(TypeError):
            receiver.receive([InvalidSource()])

    def test_new_source_can_be_added_without_changing_receiver(self) -> None:
        class CustomSource:
            def get_tasks(self) -> list[Task]:
                return [Task(id="custom-1", payload={"kind": "custom"})]

        receiver = TaskReceiver()
        tasks = receiver.receive([CustomSource()])

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].id, "custom-1")

    def test_file_source_raises_on_non_list_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "tasks.json"
            file_path.write_text(json.dumps({"id": "one"}), encoding="utf-8")

            source = FileTaskSource(file_path)
            with self.assertRaises(ValueError):
                source.get_tasks()

    def test_file_source_raises_on_invalid_task_item(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = Path(tmp_dir) / "tasks.json"
            file_path.write_text(json.dumps([{"id": "one"}]), encoding="utf-8")

            source = FileTaskSource(file_path)
            with self.assertRaises(ValueError):
                source.get_tasks()

    def test_generated_source_rejects_negative_count(self) -> None:
        with self.assertRaises(ValueError):
            GeneratedTaskSource(count=-1)

    def test_api_source_raises_on_invalid_task_item(self) -> None:
        api_source = APITaskSource(StubTaskAPI([{"id": "only-id"}]))
        with self.assertRaises(ValueError):
            api_source.get_tasks()

    def test_demo_main_prints_received_tasks(self) -> None:
        captured = StringIO()
        with redirect_stdout(captured):
            demo_main()

        output = captured.getvalue()
        self.assertIn("Total tasks received: 6", output)
        self.assertIn("file-1", output)
        self.assertIn("api-2", output)


if __name__ == "__main__":
    unittest.main()
