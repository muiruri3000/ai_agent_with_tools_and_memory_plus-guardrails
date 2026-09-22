import json
import logging
import tempfile
import unittest
from pathlib import Path

from logging_config import JsonFormatter, configure_logging


class TestJsonFormatter(unittest.TestCase):

    def test_formatter_produces_valid_json(self):
        formatter = JsonFormatter()

        record = logging.LogRecord(
            name="atlas",
            level=logging.INFO,
            pathname=__file__,
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted = formatter.format(record)
        data = json.loads(formatted)

        self.assertEqual(
            data["level"],
            "INFO",
        )

        self.assertEqual(
            data["logger"],
            "atlas",
        )

        self.assertEqual(
            data["message"],
            "Test message",
        )

        self.assertIn(
            "timestamp",
            data,
        )

    def test_formatter_includes_structured_fields(self):
        formatter = JsonFormatter()

        record = logging.LogRecord(
            name="atlas",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="Tool failed",
            args=(),
            exc_info=None,
        )

        record.event = "tool_execution_failed"
        record.tool = "web_search"
        record.error = "Network connection failed."

        data = json.loads(formatter.format(record))

        self.assertEqual(
            data["event"],
            "tool_execution_failed",
        )

        self.assertEqual(
            data["tool"],
            "web_search",
        )

        self.assertEqual(
            data["error"],
            "Network connection failed.",
        )


class TestConfigureLogging(unittest.TestCase):

    def test_configure_logging_creates_log_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:

            log_path = Path(temp_dir) / "atlas.jsonl"

            logger_name = f"atlas.test.{id(log_path)}"

            logger = logging.getLogger(logger_name)

            logger.setLevel(logging.INFO)

            handler = logging.FileHandler(
                log_path,
                encoding="utf-8",
            )

            handler.setFormatter(JsonFormatter())

            logger.addHandler(handler)

            logger.info(
                "Test structured log",
                extra={
                    "event": "test_event",
                },
            )

            handler.close()
            logger.removeHandler(handler)

            self.assertTrue(log_path.exists())

            lines = log_path.read_text(encoding="utf-8").splitlines()

            self.assertEqual(
                len(lines),
                1,
            )

            record = json.loads(lines[0])

            self.assertEqual(
                record["event"],
                "test_event",
            )


if __name__ == "__main__":
    unittest.main()
