from dataclasses import dataclass
from typing import Any


@dataclass
class ToolResult:
    """
    Structured result returned by an Atlas tool or action.
    """

    success: bool
    action: str
    message: str
    data: Any = None
