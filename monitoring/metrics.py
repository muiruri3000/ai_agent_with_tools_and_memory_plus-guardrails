from collections import Counter
from threading import Lock
from time import monotonic


class Metrics:
    """
    Thread-safe in-process metrics collector for Atlas.

    Tracks operational counters and tool execution timing.
    """

    def __init__(self):
        self._lock = Lock()

        self._counters = Counter()

        self._tool_calls = Counter()
        self._tool_successes = Counter()
        self._tool_failures = Counter()

        self._tool_duration_total = Counter()
        self._tool_duration_count = Counter()

        self._started_at = monotonic()

    def increment(
        self,
        metric: str,
        amount: int = 1,
    ) -> None:
        with self._lock:
            self._counters[metric] += amount

    def record_tool_execution(
        self,
        tool: str,
        *,
        success: bool,
        duration_seconds: float,
    ) -> None:
        with self._lock:
            self._tool_calls[tool] += 1

            if success:
                self._tool_successes[tool] += 1
            else:
                self._tool_failures[tool] += 1

            self._tool_duration_total[tool] += duration_seconds
            self._tool_duration_count[tool] += 1

    def snapshot(self) -> dict:
        """
        Return a point-in-time snapshot of all metrics.
        """
        with self._lock:
            tool_metrics = {}

            tools = set(self._tool_calls)

            for tool in tools:
                calls = self._tool_calls[tool]
                successes = self._tool_successes[tool]
                failures = self._tool_failures[tool]

                duration_total = self._tool_duration_total[tool]
                duration_count = self._tool_duration_count[tool]

                average_duration = (
                    duration_total / duration_count if duration_count else 0.0
                )

                tool_metrics[tool] = {
                    "calls": calls,
                    "successes": successes,
                    "failures": failures,
                    "average_duration_seconds": average_duration,
                }

            return {
                "uptime_seconds": monotonic() - self._started_at,
                "counters": dict(self._counters),
                "tools": tool_metrics,
            }

    def reset(self) -> None:
        """
        Reset collected metrics.
        """
        with self._lock:
            self._counters.clear()
            self._tool_calls.clear()
            self._tool_successes.clear()
            self._tool_failures.clear()
            self._tool_duration_total.clear()
            self._tool_duration_count.clear()
            self._started_at = monotonic()
