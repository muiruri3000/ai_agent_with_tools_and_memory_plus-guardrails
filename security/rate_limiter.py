import time
from collections import deque

from security.roles import SecurityRole

ROLE_RATE_LIMITS = {
    SecurityRole.READ_ONLY: (30, 60),
    SecurityRole.STANDARD: (20, 60),
    SecurityRole.ADMIN: (60, 60),
}


class RateLimiter:
    """
    Session-level sliding-window rate limiter.

    Limits the number of tool executions allowed within
    a configured time window for the current security role.
    """

    def __init__(self, role: SecurityRole):
        self.role = role
        self._calls = deque()

    def get_limit(self) -> tuple[int, int]:
        """
        Return (maximum_calls, window_seconds) for the role.
        """

        try:
            return ROLE_RATE_LIMITS[self.role]
        except KeyError as exc:
            raise ValueError(
                f"No rate-limit policy exists for role: {self.role}"
            ) from exc

    def allow(self) -> bool:
        """
        Determine whether another tool execution is allowed.
        """

        max_calls, window_seconds = self.get_limit()
        now = time.monotonic()

        while self._calls and (now - self._calls[0] >= window_seconds):
            self._calls.popleft()

        if len(self._calls) >= max_calls:
            return False

        self._calls.append(now)

        return True

    def remaining(self) -> int:
        """
        Return the number of tool executions remaining
        in the current rate-limit window.
        """

        max_calls, window_seconds = self.get_limit()
        now = time.monotonic()

        while self._calls and (now - self._calls[0] >= window_seconds):
            self._calls.popleft()

        return max_calls - len(self._calls)


ROLE_RATE_LIMITS = {
    SecurityRole.READ_ONLY: (30, 60),
    SecurityRole.STANDARD: (20, 60),
    SecurityRole.ADMIN: (60, 60),
}


class RateLimiter:
    """
    Session-level sliding-window rate limiter.

    Limits the number of tool executions allowed within
    a configured time window for the current security role.
    """

    def __init__(self, role: SecurityRole):
        self.role = role
        self._calls = deque()

    def get_limit(self) -> tuple[int, int]:
        """
        Return (maximum_calls, window_seconds) for the role.
        """

        try:
            return ROLE_RATE_LIMITS[self.role]
        except KeyError as exc:
            raise ValueError(
                f"No rate-limit policy exists for role: {self.role}"
            ) from exc

    def allow(self) -> bool:
        """
        Determine whether another tool execution is allowed.
        """

        max_calls, window_seconds = self.get_limit()
        now = time.monotonic()

        while self._calls and (now - self._calls[0] >= window_seconds):
            self._calls.popleft()

        if len(self._calls) >= max_calls:
            return False

        self._calls.append(now)

        return True

    def remaining(self) -> int:
        """
        Return the number of tool executions remaining
        in the current rate-limit window.
        """

        max_calls, window_seconds = self.get_limit()
        now = time.monotonic()

        while self._calls and (now - self._calls[0] >= window_seconds):
            self._calls.popleft()

        return max_calls - len(self._calls)
