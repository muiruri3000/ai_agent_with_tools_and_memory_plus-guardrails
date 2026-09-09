import unittest
from unittest.mock import patch
from unittest.mock import Mock, patch

from agent.executor import ToolExecutor
from security.rate_limiter import (
    ROLE_RATE_LIMITS,
    RateLimiter,
)
from security.roles import SecurityRole


class TestRateLimiter(unittest.TestCase):

    def test_standard_role_has_expected_limit(self):
        limiter = RateLimiter(SecurityRole.STANDARD)

        self.assertEqual(
            limiter.get_limit(),
            ROLE_RATE_LIMITS[SecurityRole.STANDARD],
        )

    def test_read_only_role_has_expected_limit(self):
        limiter = RateLimiter(SecurityRole.READ_ONLY)

        self.assertEqual(
            limiter.get_limit(),
            ROLE_RATE_LIMITS[SecurityRole.READ_ONLY],
        )

    def test_admin_role_has_expected_limit(self):
        limiter = RateLimiter(SecurityRole.ADMIN)

        self.assertEqual(
            limiter.get_limit(),
            ROLE_RATE_LIMITS[SecurityRole.ADMIN],
        )

    def test_first_call_is_allowed(self):
        limiter = RateLimiter(SecurityRole.STANDARD)

        self.assertTrue(limiter.allow())

    def test_limit_is_enforced(self):
        limiter = RateLimiter(SecurityRole.STANDARD)

        max_calls, _ = limiter.get_limit()

        for _ in range(max_calls):
            self.assertTrue(limiter.allow())

        self.assertFalse(limiter.allow())

    def test_remaining_decreases_after_call(self):
        limiter = RateLimiter(SecurityRole.STANDARD)

        max_calls, _ = limiter.get_limit()

        self.assertEqual(
            limiter.remaining(),
            max_calls,
        )

        limiter.allow()

        self.assertEqual(
            limiter.remaining(),
            max_calls - 1,
        )

    def test_expired_calls_are_removed(self):
        limiter = RateLimiter(SecurityRole.STANDARD)

        max_calls, window_seconds = limiter.get_limit()

        current_time = 1000.0

        with patch(
            "security.rate_limiter.time.monotonic",
            return_value=current_time,
        ):
            for _ in range(max_calls):
                self.assertTrue(limiter.allow())

            self.assertFalse(limiter.allow())

        with patch(
            "security.rate_limiter.time.monotonic",
            return_value=current_time + window_seconds + 1,
        ):
            self.assertTrue(limiter.allow())

    def test_unknown_role_policy_raises_error(self):
        limiter = RateLimiter.__new__(RateLimiter)
        limiter.role = object()

        with self.assertRaises(ValueError):
            limiter.get_limit()


class TestToolExecutorRateLimit(unittest.TestCase):

    def test_executor_blocks_tool_when_rate_limit_is_exceeded(self):
        executor = ToolExecutor(SecurityRole.STANDARD)

        executor.rate_limiter.allow = Mock(return_value=False)

        executor.audit_logger.log = Mock()

        with self.assertRaises(RuntimeError) as context:
            executor.execute(
                "get_customers",
                {},
            )

        self.assertIn(
            "rate limit exceeded",
            str(context.exception).lower(),
        )

        executor.audit_logger.log.assert_called_once()

        audit_call = executor.audit_logger.log.call_args.kwargs

        self.assertEqual(
            audit_call["event"],
            "tool_rate_limited",
        )

        self.assertFalse(audit_call["success"])


if __name__ == "__main__":
    unittest.main()
