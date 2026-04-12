from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from .exceptions import (
    InvalidDescriptionError,
    InvalidPriorityError,
    InvalidStatusError,
    InvalidStatusTransitionError,
    InvalidTaskIdError,
)


class DataDescriptor(ABC):
    """Базовый data descriptor: имеет __get__ и __set__."""

    def __set_name__(self, owner: type[object], name: str) -> None:
        self.public_name = name
        self.private_name = f"_{name}"

    def __get__(self, instance: object | None, owner: type[object]) -> Any:
        if instance is None:
            return self

        return getattr(instance, self.private_name)

    def __set__(self, instance: object, value: Any) -> None:
        validated_value = self.validate(instance, value)
        setattr(instance, self.private_name, validated_value)

    @abstractmethod
    def validate(self, instance: object, value: Any) -> Any:
        raise NotImplementedError


class TaskIdDescriptor(DataDescriptor):
    def validate(self, instance: object, value: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise InvalidTaskIdError("Task id must be a non-empty string")

        return value.strip()


class DescriptionDescriptor(DataDescriptor):
    def validate(self, instance: object, value: Any) -> str:
        if not isinstance(value, str) or not value.strip():
            raise InvalidDescriptionError("Description must be a non-empty string")

        text = value.strip()
        if len(text) > 500:
            raise InvalidDescriptionError("Description is too long (max 500 chars)")

        return text


class PriorityDescriptor(DataDescriptor):
    def validate(self, instance: object, value: Any) -> int:
        if not isinstance(value, int):
            raise InvalidPriorityError("Priority must be an integer")

        if value < 1 or value > 5:
            raise InvalidPriorityError("Priority must be in range [1, 5]")

        return value


class StatusDescriptor(DataDescriptor):
    allowed_statuses = {"new", "in_progress", "blocked", "done"}
    transitions = {
        "new": {"in_progress", "blocked", "done"},
        "in_progress": {"blocked", "done"},
        "blocked": {"in_progress", "done"},
        "done": set(),
    }

    def validate(self, instance: object, value: Any) -> str:
        if not isinstance(value, str):
            raise InvalidStatusError("Status must be a string")

        normalized = value.strip()
        if normalized not in self.allowed_statuses:
            raise InvalidStatusError(
                f"Unsupported status '{normalized}'. Allowed: {sorted(self.allowed_statuses)}"
            )

        old_value = getattr(instance, self.private_name, None)
        if old_value is None or old_value == normalized:
            return normalized

        if normalized not in self.transitions[old_value]:
            raise InvalidStatusTransitionError(
                f"Invalid status transition: '{old_value}' -> '{normalized}'"
            )

        return normalized


class RuntimeNoteDescriptor:
    """Non-data descriptor: только __get__, без __set__."""

    def __get__(self, instance: object | None, owner: type[object]) -> str | RuntimeNoteDescriptor:
        if instance is None:
            return self

        return "Non-data descriptor: this value can be overridden on instance"
