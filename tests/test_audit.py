import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from audit.logger import AuditLogger
from agent.executor import ToolExecutor
from agent.results import ToolResult

from security.input_constraints import (
    validate_tool_values,
)

from security.audit_redaction import (
    REDACTED,
    redact_sensitive_data,
)


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

            records = log_path.read_text(encoding="utf-8").splitlines()

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
            self.assertTrue(record["success"])
            self.assertIn(
                "timestamp",
                record,
            )


class TestExecutorAuditLogging(unittest.TestCase):

    def test_successful_tool_execution_is_audited(self):
        executor = ToolExecutor()

        with tempfile.TemporaryDirectory() as tmpdir:
            executor.audit_logger = AuditLogger(Path(tmpdir) / "audit.jsonl")

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
                    executor.audit_logger.log_path.read_text(
                        encoding="utf-8"
                    ).splitlines()
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

            self.assertTrue(records[1]["success"])

    def test_failed_tool_execution_is_audited(self):
        executor = ToolExecutor()

        with tempfile.TemporaryDirectory() as tmpdir:
            executor.audit_logger = AuditLogger(Path(tmpdir) / "audit.jsonl")

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
                    executor.audit_logger.log_path.read_text(
                        encoding="utf-8"
                    ).splitlines()
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

            self.assertFalse(records[1]["success"])

            self.assertEqual(
                records[1]["message"],
                "Simulated failure",
            )

    def test_unknown_tool_is_audited(self):
        executor = ToolExecutor()

        with tempfile.TemporaryDirectory() as tmpdir:
            executor.audit_logger = AuditLogger(Path(tmpdir) / "audit.jsonl")

            with self.assertRaises(ValueError):
                executor.execute(
                    "unknown_tool",
                    {},
                )

            records = [
                json.loads(line)
                for line in (
                    executor.audit_logger.log_path.read_text(
                        encoding="utf-8"
                    ).splitlines()
                )
            ]

            self.assertEqual(
                len(records),
                1,
            )

            self.assertEqual(
                records[0]["event"],
                "tool_denied",
            )

            self.assertEqual(
                records[0]["tool"],
                "unknown_tool",
            )

            self.assertEqual(
                records[0]["permission"],
                "unknown",
            )

            self.assertFalse(records[0]["success"])

            self.assertIn(
                "Unknown tool",
                records[0]["message"],
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
            executor.audit_logger = AuditLogger(Path(tmpdir) / "audit.jsonl")

            with patch(
                "agent.executor.get_tool_timeout",
                return_value=1,
            ):
                with patch.dict(
                    executor.tools,
                    {"get_customers": lambda: (__import__("time").sleep(2))},
                ):
                    with self.assertRaises(TimeoutError):
                        executor.execute(
                            "get_customers",
                            {},
                        )

            records = [
                json.loads(line)
                for line in (
                    executor.audit_logger.log_path.read_text(
                        encoding="utf-8"
                    ).splitlines()
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

            self.assertFalse(records[1]["success"])

            self.assertIn(
                "timed out",
                records[1]["message"],
            )


class TestToolArgumentValidation(unittest.TestCase):

    def test_unknown_argument_is_rejected(self):
        executor = ToolExecutor()

        with self.assertRaises(TypeError):
            executor.execute(
                "get_customers",
                {"unexpected": "value"},
            )

    def test_missing_required_argument_is_rejected(self):
        executor = ToolExecutor()

        with self.assertRaises(TypeError):
            executor.execute(
                "web_search",
                {},
            )

    def test_invalid_argument_type_is_rejected(self):
        executor = ToolExecutor()

        with self.assertRaises(TypeError):
            executor.execute(
                "web_search",
                {"query": 123},
            )

    def test_valid_arguments_are_accepted(self):
        executor = ToolExecutor()

        with patch(
            "agent.executor.get_tool_timeout",
            return_value=1,
        ):
            with patch.dict(
                executor.tools,
                {
                    "web_search": lambda query: ToolResult(
                        success=True,
                        action="web_search",
                        message="Test search completed.",
                        data={"query": query},
                    )
                },
            ):
                result = executor.execute(
                    "web_search",
                    {"query": "AWS"},
                )

        self.assertIsInstance(
            result,
            ToolResult,
        )

        self.assertTrue(result.success)

    def test_invalid_arguments_are_rejected_before_tool_execution(
        self,
    ):
        executor = ToolExecutor()

        tool_called = False

        def test_tool(query):
            nonlocal tool_called
            tool_called = True

        with patch.dict(
            executor.tools,
            {
                "web_search": test_tool,
            },
        ):
            with self.assertRaises(TypeError):
                executor.execute(
                    "web_search",
                    {"wrong_argument": "value"},
                )

        self.assertFalse(tool_called)

    def test_invalid_arguments_are_audited(self):
        executor = ToolExecutor()

        with tempfile.TemporaryDirectory() as tmpdir:
            executor.audit_logger = AuditLogger(Path(tmpdir) / "audit.jsonl")

            with self.assertRaises(TypeError):
                executor.execute(
                    "web_search",
                    {"wrong_argument": "value"},
                )

            records = [
                json.loads(line)
                for line in (
                    executor.audit_logger.log_path.read_text(
                        encoding="utf-8"
                    ).splitlines()
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
                "tool_validation_failed",
            )

            self.assertEqual(
                records[1]["tool"],
                "web_search",
            )

            self.assertFalse(records[1]["success"])

            self.assertIn(
                "Invalid arguments",
                records[1]["message"],
            )

    def test_non_dict_arguments_are_rejected_and_audited(self):
        executor = ToolExecutor()

        with tempfile.TemporaryDirectory() as tmpdir:
            executor.audit_logger = AuditLogger(Path(tmpdir) / "audit.jsonl")

            with self.assertRaises(TypeError):
                executor.execute(
                    "get_customers",
                    None,
                )

            records = [
                json.loads(line)
                for line in (
                    executor.audit_logger.log_path.read_text(
                        encoding="utf-8"
                    ).splitlines()
                )
            ]

            self.assertEqual(
                len(records),
                2,
            )

            self.assertEqual(
                records[1]["event"],
                "tool_validation_failed",
            )

            self.assertFalse(records[1]["success"])


class TestToolInputConstraints(unittest.TestCase):

    def test_positive_customer_id_is_accepted(self):
        validate_tool_values(
            "get_customer_by_id",
            {"customer_id": 1},
        )

    def test_zero_customer_id_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_tool_values(
                "get_customer_by_id",
                {"customer_id": 0},
            )

    def test_negative_customer_id_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_tool_values(
                "get_customer_by_id",
                {"customer_id": -1},
            )

    def test_empty_name_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_tool_values(
                "create_customer",
                {
                    "name": "   ",
                    "email": "john@example.com",
                    "city": "Nairobi",
                },
            )

    def test_invalid_email_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_tool_values(
                "create_customer",
                {
                    "name": "John Doe",
                    "email": "not-an-email",
                    "city": "Nairobi",
                },
            )

    def test_valid_email_is_accepted(self):
        validate_tool_values(
            "create_customer",
            {
                "name": "John Doe",
                "email": "john@example.com",
                "city": "Nairobi",
            },
        )

    def test_empty_city_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_tool_values(
                "create_customer",
                {
                    "name": "John Doe",
                    "email": "john@example.com",
                    "city": "   ",
                },
            )

    def test_empty_fact_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_tool_values(
                "remember",
                {"fact": "   "},
            )

    def test_empty_query_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_tool_values(
                "web_search",
                {"query": "   "},
            )

    def test_excessively_long_name_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_tool_values(
                "create_customer",
                {
                    "name": "A" * 151,
                    "email": "john@example.com",
                    "city": "Nairobi",
                },
            )

    def test_excessively_long_query_is_rejected(self):
        with self.assertRaises(ValueError):
            validate_tool_values(
                "web_search",
                {"query": "A" * 501},
            )


class TestAuditRedaction(unittest.TestCase):

    def test_sensitive_arguments_are_redacted(self):
        arguments = {
            "customer_id": 15,
            "email": "john@example.com",
            "city": "Nairobi",
            "fact": "Sensitive personal information",
            "password": "secret-password",
            "token": "abc123",
        }

        result = redact_sensitive_data(arguments)

        self.assertEqual(
            result["customer_id"],
            15,
        )

        self.assertEqual(
            result["city"],
            "Nairobi",
        )

        self.assertEqual(
            result["email"],
            REDACTED,
        )

        self.assertEqual(
            result["fact"],
            REDACTED,
        )

        self.assertEqual(
            result["password"],
            REDACTED,
        )

        self.assertEqual(
            result["token"],
            REDACTED,
        )

    def test_nested_sensitive_arguments_are_redacted(self):
        arguments = {
            "customer": {
                "customer_id": 15,
                "email": "john@example.com",
                "city": "Nairobi",
            },
            "metadata": [
                {
                    "secret": "hidden",
                }
            ],
        }

        result = redact_sensitive_data(arguments)

        self.assertEqual(
            result["customer"]["customer_id"],
            15,
        )

        self.assertEqual(
            result["customer"]["email"],
            REDACTED,
        )

        self.assertEqual(
            result["customer"]["city"],
            "Nairobi",
        )

        self.assertEqual(
            result["metadata"][0]["secret"],
            REDACTED,
        )

    def test_non_sensitive_arguments_are_preserved(self):
        arguments = {
            "customer_id": 42,
            "city": "Nairobi",
            "name": "John Doe",
        }

        result = redact_sensitive_data(arguments)

        self.assertEqual(
            result,
            arguments,
        )

    def test_redaction_does_not_modify_original_data(self):
        arguments = {
            "email": "john@example.com",
            "customer_id": 42,
        }

        result = redact_sensitive_data(arguments)

        self.assertEqual(
            arguments["email"],
            "john@example.com",
        )

        self.assertEqual(
            result["email"],
            REDACTED,
        )

    def test_audit_logger_redacts_sensitive_arguments(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = AuditLogger(Path(tmpdir) / "audit.jsonl")

            logger.log(
                event="tool_requested",
                tool="create_customer",
                permission="write",
                arguments={
                    "customer_id": 15,
                    "email": "john@example.com",
                    "city": "Nairobi",
                    "fact": "private information",
                },
            )

            record = json.loads(logger.log_path.read_text(encoding="utf-8").strip())

            self.assertEqual(
                record["arguments"]["customer_id"],
                15,
            )

            self.assertEqual(
                record["arguments"]["city"],
                "Nairobi",
            )

            self.assertEqual(
                record["arguments"]["email"],
                REDACTED,
            )

            self.assertEqual(
                record["arguments"]["fact"],
                REDACTED,
            )

            self.assertNotIn(
                "john@example.com",
                record["arguments"].values(),
            )


if __name__ == "__main__":
    unittest.main()
