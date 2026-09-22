import unittest

from agent.executor import ToolExecutor
from security.roles import SecurityRole

from monitoring.metrics import Metrics


class TestMetrics(unittest.TestCase):

    def test_counter_increment(self):
        metrics = Metrics()

        metrics.increment("agent_requests")
        metrics.increment("agent_requests")
        metrics.increment("agent_requests", 3)

        snapshot = metrics.snapshot()

        self.assertEqual(
            snapshot["counters"]["agent_requests"],
            5,
        )

    def test_tool_success_is_recorded(self):
        metrics = Metrics()

        metrics.record_tool_execution(
            "web_search",
            success=True,
            duration_seconds=0.5,
        )

        snapshot = metrics.snapshot()

        tool = snapshot["tools"]["web_search"]

        self.assertEqual(
            tool["calls"],
            1,
        )

        self.assertEqual(
            tool["successes"],
            1,
        )

        self.assertEqual(
            tool["failures"],
            0,
        )

        self.assertAlmostEqual(
            tool["average_duration_seconds"],
            0.5,
        )

    def test_tool_failure_is_recorded(self):
        metrics = Metrics()

        metrics.record_tool_execution(
            "web_search",
            success=False,
            duration_seconds=1.0,
        )

        snapshot = metrics.snapshot()

        tool = snapshot["tools"]["web_search"]

        self.assertEqual(
            tool["calls"],
            1,
        )

        self.assertEqual(
            tool["successes"],
            0,
        )

        self.assertEqual(
            tool["failures"],
            1,
        )

    def test_average_tool_duration(self):
        metrics = Metrics()

        metrics.record_tool_execution(
            "get_customers",
            success=True,
            duration_seconds=1.0,
        )

        metrics.record_tool_execution(
            "get_customers",
            success=True,
            duration_seconds=3.0,
        )

        snapshot = metrics.snapshot()

        tool = snapshot["tools"]["get_customers"]

        self.assertEqual(
            tool["calls"],
            2,
        )

        self.assertAlmostEqual(
            tool["average_duration_seconds"],
            2.0,
        )

    def test_multiple_tools_are_tracked_separately(self):
        metrics = Metrics()

        metrics.record_tool_execution(
            "get_customers",
            success=True,
            duration_seconds=0.2,
        )

        metrics.record_tool_execution(
            "web_search",
            success=False,
            duration_seconds=1.5,
        )

        snapshot = metrics.snapshot()

        self.assertIn(
            "get_customers",
            snapshot["tools"],
        )

        self.assertIn(
            "web_search",
            snapshot["tools"],
        )

        self.assertEqual(
            snapshot["tools"]["get_customers"]["successes"],
            1,
        )

        self.assertEqual(
            snapshot["tools"]["web_search"]["failures"],
            1,
        )

    def test_reset_clears_metrics(self):
        metrics = Metrics()

        metrics.increment("agent_requests")

        metrics.record_tool_execution(
            "web_search",
            success=True,
            duration_seconds=0.5,
        )

        metrics.reset()

        snapshot = metrics.snapshot()

        self.assertEqual(
            snapshot["counters"],
            {},
        )

        self.assertEqual(
            snapshot["tools"],
            {},
        )

    def test_tool_failure_is_counted(self):
        metrics = Metrics()

        metrics.record_tool_execution(
            "create_customer",
            success=False,
            duration_seconds=0.25,
        )

        snapshot = metrics.snapshot()

        self.assertEqual(
            snapshot["tools"]["create_customer"]["calls"],
            1,
        )

        self.assertEqual(
            snapshot["tools"]["create_customer"]["failures"],
            1,
        )

    def test_security_counters(self):
        metrics = Metrics()

        metrics.increment("authorization_denied")
        metrics.increment("rate_limit_exceeded")
        metrics.increment("validation_failed")
        metrics.increment("constraint_failed")

        snapshot = metrics.snapshot()

        self.assertEqual(
            snapshot["counters"]["authorization_denied"],
            1,
        )

        self.assertEqual(
            snapshot["counters"]["rate_limit_exceeded"],
            1,
        )

        self.assertEqual(
            snapshot["counters"]["validation_failed"],
            1,
        )

        self.assertEqual(
            snapshot["counters"]["constraint_failed"],
            1,
        )

        def test_executor_records_successful_tool_execution(self):
            executor = ToolExecutor(role=SecurityRole.STANDARD)

            def fake_tool():
                return "success"

            executor.tools["get_customers"] = fake_tool

            result = executor.execute(
                "get_customers",
                {},
            )

            self.assertEqual(
                result,
                "success",
            )

            snapshot = executor.metrics.snapshot()

            self.assertEqual(
                snapshot["tools"]["get_customers"]["calls"],
                1,
            )

            self.assertEqual(
                snapshot["tools"]["get_customers"]["successes"],
                1,
            )

            self.assertEqual(
                snapshot["tools"]["get_customers"]["failures"],
                0,
            )

            self.assertGreaterEqual(
                snapshot["tools"]["get_customers"]["average_duration_seconds"],
                0,
            )

    def test_executor_records_failed_tool_execution(self):
        executor = ToolExecutor(role=SecurityRole.STANDARD)

        def failing_tool():
            raise RuntimeError("Simulated tool failure")

        executor.tools["get_customers"] = failing_tool

        with self.assertRaises(RuntimeError):
            executor.execute(
                "get_customers",
                {},
            )

        snapshot = executor.metrics.snapshot()

        self.assertEqual(
            snapshot["tools"]["get_customers"]["calls"],
            1,
        )

        self.assertEqual(
            snapshot["tools"]["get_customers"]["successes"],
            0,
        )

        self.assertEqual(
            snapshot["tools"]["get_customers"]["failures"],
            1,
        )

    def test_executor_records_rate_limit_event(self):
        executor = ToolExecutor(role=SecurityRole.STANDARD)

        executor.rate_limiter.allow = lambda: False

        with self.assertRaises(RuntimeError):
            executor.execute(
                "get_customers",
                {},
            )

        snapshot = executor.metrics.snapshot()

        self.assertEqual(
            snapshot["counters"]["rate_limit_exceeded"],
            1,
        )


if __name__ == "__main__":
    unittest.main()
