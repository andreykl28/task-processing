from datetime import datetime, timezone
from io import StringIO
from contextlib import redirect_stdout

import pytest

from task_model.exceptions import (
    InvalidCreatedAtError,
    InvalidDescriptionError,
    InvalidPriorityError,
    InvalidStatusError,
    InvalidStatusTransitionError,
    InvalidTaskIdError,
)
from task_model.models import Task
from task_model.demo import main as demo_main


def test_task_creation_success() -> None:
    task = Task(id="t-1", description="Process order", priority=2, status="new")

    assert task.id == "t-1"
    assert task.description == "Process order"
    assert task.priority == 2
    assert task.status == "new"
    assert task.is_ready_for_execution is True
    assert task.can_be_edited is True


def test_invalid_id_raises_specific_exception() -> None:
    with pytest.raises(InvalidTaskIdError):
        Task(id="  ", description="ok")


def test_invalid_description_raises_specific_exception() -> None:
    with pytest.raises(InvalidDescriptionError):
        Task(id="t-1", description="")


def test_invalid_priority_raises_specific_exception() -> None:
    with pytest.raises(InvalidPriorityError):
        Task(id="t-1", description="ok", priority=10)


def test_invalid_status_raises_specific_exception() -> None:
    with pytest.raises(InvalidStatusError):
        Task(id="t-1", description="ok", status="queued")


def test_invalid_created_at_raises_specific_exception() -> None:
    with pytest.raises(InvalidCreatedAtError):
        Task(id="t-1", description="ok", created_at=datetime.now())


def test_created_at_is_read_only_property() -> None:
    task = Task(id="t-1", description="ok")

    with pytest.raises(AttributeError):
        task.created_at = datetime.now(timezone.utc)


def test_status_transition_rules() -> None:
    task = Task(id="t-1", description="ok", status="new")

    task.status = "in_progress"
    task.status = "done"

    with pytest.raises(InvalidStatusTransitionError):
        task.status = "blocked"


def test_is_ready_for_execution_depends_on_status() -> None:
    task = Task(id="t-1", description="ok", status="new")
    assert task.is_ready_for_execution is True

    task.status = "blocked"
    assert task.is_ready_for_execution is False


def test_data_descriptor_cannot_be_shadowed_by_instance_dict() -> None:
    task = Task(id="t-1", description="ok", priority=3)

    task.__dict__["priority"] = 999
    assert task.priority == 3


def test_non_data_descriptor_can_be_shadowed() -> None:
    task = Task(id="t-1", description="ok")

    assert "Non-data descriptor" in task.runtime_note
    task.runtime_note = "manual override"
    assert task.runtime_note == "manual override"


def test_to_dict_contains_public_state() -> None:
    created_at = datetime(2026, 4, 12, 12, 0, tzinfo=timezone.utc)
    task = Task(id="t-1", description="ok", created_at=created_at)

    data = task.to_dict()
    assert data["id"] == "t-1"
    assert data["created_at"] == created_at.isoformat()
    assert data["status"] == "new"


def test_demo_main_runs() -> None:
    captured = StringIO()
    with redirect_stdout(captured):
        demo_main()

    output = captured.getvalue()
    assert "Created task:" in output
    assert "After status update:" in output
