from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from agent.results import ToolResult


class TaskStatus(str, Enum):
    """
    Lifecycle states for an Atlas agent task.
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AgentTask:
    """
    State container for a single Atlas agent task.

    This class intentionally contains no Gemini-specific logic.
    It records the task's goal, execution progress, observations,
    and final outcome.
    """

    goal: str
    status: TaskStatus = TaskStatus.PENDING
    iteration: int = 0

    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    observations: list[ToolResult] = field(default_factory=list)

    result: str | None = None
    error: str | None = None

    def start(self) -> None:
        """Mark the task as running."""

        self.status = TaskStatus.RUNNING

    def next_iteration(self) -> int:
        """
        Advance the task iteration counter and return its value.
        """

        self.iteration += 1
        return self.iteration

    def record_tool_call(
        self,
        function_name: str,
        arguments: dict[str, Any],
    ) -> None:
        """Record a tool invocation."""

        self.tool_calls.append(
            {
                "function": function_name,
                "arguments": arguments,
            }
        )

    def record_observation(self, result: ToolResult) -> None:
        """Record a tool result observed by the agent."""

        self.observations.append(result)

    def is_duplicate_tool_call(
        self,
        function_name: str,
        arguments: dict[str, Any],
    ) -> bool:
        """
        Return True when the same tool call has already been recorded.

        Argument ordering does not affect duplicate detection.
        """

        normalized_arguments = dict(arguments)

        return any(
            call["function"] == function_name
            and dict(call["arguments"]) == normalized_arguments
            for call in self.tool_calls
        )

    def has_consecutive_tool_call(
        self,
        function_name: str,
        arguments: dict[str, Any],
        repetitions: int = 3,
    ) -> bool:
        """
        Return True when the same tool call occurred consecutively
        at least the requested number of times.
        """

        if repetitions <= 0:
            raise ValueError("repetitions must be greater than zero")

        if len(self.tool_calls) < repetitions:
            return False

        normalized_arguments = dict(arguments)
        recent_calls = self.tool_calls[-repetitions:]

        return all(
            call["function"] == function_name
            and dict(call["arguments"]) == normalized_arguments
            for call in recent_calls
        )

    def is_complete(self) -> bool:
        """Return True when the task completed successfully."""

        return self.status == TaskStatus.COMPLETED

    def is_terminal(self) -> bool:
        """Return True when the task can no longer continue running."""

        return self.status in {
            TaskStatus.COMPLETED,
            TaskStatus.FAILED,
        }

    def complete(self, result: str) -> None:
        """Mark the task as successfully completed."""

        self.status = TaskStatus.COMPLETED
        self.result = result
        self.error = None

    def fail(self, error: str) -> None:
        """Mark the task as failed."""

        self.status = TaskStatus.FAILED
        self.error = error
