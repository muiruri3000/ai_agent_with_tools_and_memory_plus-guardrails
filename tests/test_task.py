import unittest

from agent.results import ToolResult
from agent.task import AgentTask, TaskStatus


class TestAgentTask(unittest.TestCase):

    def test_new_task_starts_pending(self):
        task = AgentTask(
            goal="Find David",
        )

        self.assertEqual(task.goal, "Find David")
        self.assertEqual(task.status, TaskStatus.PENDING)
        self.assertEqual(task.iteration, 0)
        self.assertEqual(task.tool_calls, [])
        self.assertEqual(task.observations, [])
        self.assertIsNone(task.result)
        self.assertIsNone(task.error)

    def test_start_marks_task_running(self):
        task = AgentTask(goal="Find David")

        task.start()

        self.assertEqual(task.status, TaskStatus.RUNNING)

    def test_next_iteration_increments_counter(self):
        task = AgentTask(goal="Find David")

        self.assertEqual(task.next_iteration(), 1)
        self.assertEqual(task.next_iteration(), 2)
        self.assertEqual(task.iteration, 2)

    def test_tool_call_is_recorded(self):
        task = AgentTask(goal="Find David")

        task.record_tool_call(
            "find_customer",
            {
                "name": "David",
            },
        )

        self.assertEqual(
            task.tool_calls,
            [
                {
                    "function": "find_customer",
                    "arguments": {
                        "name": "David",
                    },
                }
            ],
        )

    def test_tool_call_is_detected_as_duplicate(self):
        task = AgentTask(goal="Find David")

        task.record_tool_call(
            "find_customer",
            {"name": "David"},
        )

        self.assertTrue(
            task.is_duplicate_tool_call(
                "find_customer",
                {"name": "David"},
            )
        )

    def test_different_tool_call_is_not_duplicate(self):
        task = AgentTask(goal="Find David")

        task.record_tool_call(
            "find_customer",
            {"name": "David"},
        )

        self.assertFalse(
            task.is_duplicate_tool_call(
                "find_customer",
                {"name": "Mary"},
            )
        )

    def test_different_function_is_not_duplicate(self):
        task = AgentTask(goal="Find David")

        task.record_tool_call(
            "find_customer",
            {"name": "David"},
        )

        self.assertFalse(
            task.is_duplicate_tool_call(
                "get_customers",
                {"name": "David"},
            )
        )

    def test_argument_order_does_not_affect_duplicate_detection(self):
        task = AgentTask(goal="Find David")

        task.record_tool_call(
            "search",
            {
                "query": "AWS",
                "limit": 5,
            },
        )

        self.assertTrue(
            task.is_duplicate_tool_call(
                "search",
                {
                    "limit": 5,
                    "query": "AWS",
                },
            )
        )

    def test_unrecorded_tool_call_is_not_duplicate(self):
        task = AgentTask(goal="Find David")

        self.assertFalse(
            task.is_duplicate_tool_call(
                "find_customer",
                {"name": "David"},
            )
        )

    def test_three_consecutive_identical_tool_calls_detect_stuck_loop(self):
        task = AgentTask(goal="Find David")

        for _ in range(3):
            task.record_tool_call(
                "find_customer",
                {"name": "David"},
            )

        self.assertTrue(
            task.has_consecutive_tool_call(
                "find_customer",
                {"name": "David"},
            )
        )

    def test_two_repetitions_do_not_trigger_default_threshold(self):
        task = AgentTask(goal="Find David")

        for _ in range(2):
            task.record_tool_call(
                "find_customer",
                {"name": "David"},
            )

        self.assertFalse(
            task.has_consecutive_tool_call(
                "find_customer",
                {"name": "David"},
            )
        )

    def test_intervening_tool_call_breaks_consecutive_sequence(self):
        task = AgentTask(goal="Find David")

        task.record_tool_call(
            "find_customer",
            {"name": "David"},
        )
        task.record_tool_call(
            "get_customers",
            {},
        )
        task.record_tool_call(
            "find_customer",
            {"name": "David"},
        )

        self.assertFalse(
            task.has_consecutive_tool_call(
                "find_customer",
                {"name": "David"},
            )
        )

    def test_custom_repetition_threshold_is_supported(self):
        task = AgentTask(goal="Find David")

        for _ in range(2):
            task.record_tool_call(
                "find_customer",
                {"name": "David"},
            )

        self.assertTrue(
            task.has_consecutive_tool_call(
                "find_customer",
                {"name": "David"},
                repetitions=2,
            )
        )

    def test_invalid_repetition_threshold_is_rejected(self):
        task = AgentTask(goal="Find David")

        with self.assertRaises(ValueError):
            task.has_consecutive_tool_call(
                "find_customer",
                {"name": "David"},
                repetitions=0,
            )

    def test_observation_is_recorded(self):
        task = AgentTask(goal="Find David")

        result = ToolResult(
            success=True,
            action="find_customer",
            message="Found David",
            data={"id": 3},
        )

        task.record_observation(result)

        self.assertEqual(task.observations, [result])

    def test_pending_task_is_not_complete_or_terminal(self):
        task = AgentTask(goal="Find David")

        self.assertFalse(task.is_complete())
        self.assertFalse(task.is_terminal())

    def test_running_task_is_not_complete_or_terminal(self):
        task = AgentTask(goal="Find David")

        task.start()

        self.assertFalse(task.is_complete())
        self.assertFalse(task.is_terminal())

    def test_completed_task_is_complete_and_terminal(self):
        task = AgentTask(goal="Find David")

        task.start()
        task.complete("David was found.")

        self.assertTrue(task.is_complete())
        self.assertTrue(task.is_terminal())

    def test_failed_task_is_not_complete_but_is_terminal(self):
        task = AgentTask(goal="Find David")

        task.start()
        task.fail("Database unavailable.")

        self.assertFalse(task.is_complete())
        self.assertTrue(task.is_terminal())

    def test_complete_marks_task_completed(self):
        task = AgentTask(goal="Find David")

        task.start()
        task.complete("David was found.")

        self.assertEqual(task.status, TaskStatus.COMPLETED)
        self.assertEqual(task.result, "David was found.")
        self.assertIsNone(task.error)

    def test_fail_marks_task_failed(self):
        task = AgentTask(goal="Find David")

        task.start()
        task.fail("Database unavailable.")

        self.assertEqual(task.status, TaskStatus.FAILED)
        self.assertEqual(task.error, "Database unavailable.")
        self.assertIsNone(task.result)
