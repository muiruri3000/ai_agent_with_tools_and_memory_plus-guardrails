import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from audit.logger import AuditLogger
from agent.executor import ToolExecutor
from agent.results import ToolResult


class TestAuditLogger(unittest.TestCase):

    def test_logger_writes_structured_json_line(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log_path = Path(tmpdir) / "audit.jsonl"
            logger = AuditLogger(log_path)

            logger.log(
                event="test",
                tool="get_customers",
                permission="read",
                arguments={},
                confirmation_required=False,
                success=True,
                message="Test event.",
            )

            records = log_path.read_text(
                encoding="utf-8"
            ).splitlines()

            self.assertEqual(len(records), 1)

            record = json.loads(records[0])

            self.assertEqual(
                record["event"],
                "test",
            )
            self.assertEqual(
                record["tool"],
                "get_customers",
            )
            self.assertEqual(
                record["permission"],
                "read",
            )
            self.assertTrue(
                record["success"]
            )
            self.assertIn(
                "timestamp",
                record,
            )


class TestExecutorAuditLogging(unittest.TestCase):

    def test_successful_tool_execution_is_audited(self):
        executor = ToolExecutor()

        with tempfile.TemporaryDirectory() as tmpdir:
            executor.audit_logger = AuditLogger(
                Path(tmpdir) / "audit.jsonl"
            )

            result = executor.execute(
                "get_customers",
                {},
            )

            self.assertIsInstance(
                result,
                ToolResult,
            )

            records = [
                json.loads(line)
                for line in (
                    executor.audit_logger.log_path
                    .read_text(encoding="utf-8")
                    .splitlines()
                )
            ]

            self.assertEqual(
                len(records),
                2,
            )

            self.assertEqual(
                records[0]["event"],
                "tool_requested",
            )
            self.assertEqual(
                records[1]["event"],
                "tool_completed",
            )

            self.assertEqual(
                records[0]["tool"],
                "get_customers",
            )
            self.assertEqual(
                records[1]["tool"],
                "get_customers",
            )

            self.assertTrue(
                records[1]["success"]
            )

    def test_failed_tool_execution_is_audited(self):
        executor = ToolExecutor()

        with tempfile.TemporaryDirectory() as tmpdir:
            executor.audit_logger = AuditLogger(
                Path(tmpdir) / "audit.jsonl"
            )

            with patch.dict(
                executor.tools,
                {
                    "get_customers": lambda: (_ for _ in ()).throw(
                        RuntimeError("Simulated failure")
                    )
                },
            ):
                with self.assertRaises(RuntimeError):
                    executor.execute(
                        "get_customers",
                        {},
                    )

            records = [
                json.loads(line)
                for line in (
                    executor.audit_logger.log_path
                    .read_text(encoding="utf-8")
                    .splitlines()
                )
            ]

            self.assertEqual(
                len(records),
                2,
            )

            self.assertEqual(
                records[0]["event"],
                "tool_requested",
            )
            self.assertEqual(
                records[1]["event"],
                "tool_failed",
            )

            self.assertFalse(
                records[1]["success"]
            )
            self.assertEqual(
                records[1]["message"],
                "Simulated failure",
            )




class TestToolTimeout(unittest.TestCase):

    def test_tool_timeout_raises_timeout_error(self):
        executor = ToolExecutor()

        def slow_tool():
            import time
            time.sleep(2)

        with self.assertRaises(TimeoutError):
            executor._run_with_timeout(
                slow_tool,
                {},
                1,
            )

    def test_tool_timeout_is_audited(self):
        executor = ToolExecutor()

        with tempfile.TemporaryDirectory() as tmpdir:
            executor.audit_logger = AuditLogger(
                Path(tmpdir) / "audit.jsonl"
            )

            with patch(
                "agent.executor.get_tool_timeout",
                return_value=1,
            ):
                with patch.dict(
                    executor.tools,
                    {
                        "get_customers": lambda: (
                            __import__("time").sleep(2)
                        )
                    },
                ):
                    with self.assertRaises(TimeoutError):
                        executor.execute(
                            "get_customers",
                            {},
                        )

            records = [
                json.loads(line)
                for line in (
                    executor.audit_logger.log_path
                    .read_text(encoding="utf-8")
                    .splitlines()
                )
            ]

            self.assertEqual(
                len(records),
                2,
            )

            self.assertEqual(
                records[0]["event"],
                "tool_requested",
            )

            self.assertEqual(
                records[1]["event"],
                "tool_timeout",
            )

            self.assertEqual(
                records[1]["tool"],
                "get_customers",
            )

            self.assertFalse(
                records[1]["success"]
            )

            self.assertIn(
                "timed out",
                records[1]["message"],
            )

if __name__ == "__main__":
    unittest.main()
