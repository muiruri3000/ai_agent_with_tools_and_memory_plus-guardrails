import json
from datetime import datetime, timezone
from pathlib import Path
from security.audit_redaction import redact_sensitive_data


class AuditLogger:
    """
    Structured audit logger for security-relevant Atlas events.

    Events are written as JSON Lines so each audit record
    is independently parseable.
    """

    def __init__(self, log_path="logs/audit.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

    def log(
        self,
        *,
        event: str,
        tool: str,
        permission: str,
        arguments=None,
        confirmation_required=False,
        confirmation_granted=None,
        success=None,
        message=None,
    ):
        """
        Write one structured audit event.
        """

        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "tool": tool,
            "permission": permission,
            "arguments": redact_sensitive_data(arguments or {}),
            "confirmation_required": confirmation_required,
            "confirmation_granted": confirmation_granted,
            "success": success,
            "message": message,
        }

        with self.log_path.open(
            "a",
            encoding="utf-8",
        ) as file:
            file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                    default=str,
                )
                + "\n"
            )
