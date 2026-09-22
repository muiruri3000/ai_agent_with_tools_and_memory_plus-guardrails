import json
import logging
from datetime import datetime, timezone
from pathlib import Path


class JsonFormatter(logging.Formatter):
    """
    Format application logs as JSON Lines.
    """

    def format(self, record):
        log_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if hasattr(record, "event"):
            log_record["event"] = record.event

        if hasattr(record, "tool"):
            log_record["tool"] = record.tool

        if hasattr(record, "error"):
            log_record["error"] = record.error

        return json.dumps(
            log_record,
            ensure_ascii=False,
            default=str,
        )


def configure_logging(
    log_path="logs/atlas.jsonl",
):
    """
    Configure structured application logging for Atlas.
    """

    path = Path(log_path)

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    logger = logging.getLogger("atlas")

    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    handler = logging.FileHandler(
        path,
        encoding="utf-8",
    )

    handler.setFormatter(JsonFormatter())

    logger.addHandler(handler)

    logger.propagate = False

    return logger
