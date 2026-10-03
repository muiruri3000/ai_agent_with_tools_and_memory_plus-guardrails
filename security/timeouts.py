from security.tool_registry import TOOL_PERMISSIONS
from security.permissions import PermissionLevel

from config.settings import (
    DEFAULT_TOOL_TIMEOUT_SECONDS,
    TOOL_TIMEOUT_DESTRUCTIVE_SECONDS,
    TOOL_TIMEOUT_EXTERNAL_READ_SECONDS,
    TOOL_TIMEOUT_MEMORY_READ_SECONDS,
    TOOL_TIMEOUT_MEMORY_WRITE_SECONDS,
    TOOL_TIMEOUT_READ_SECONDS,
    TOOL_TIMEOUT_WRITE_SECONDS,
)


TOOL_TIMEOUTS = {
    PermissionLevel.READ: TOOL_TIMEOUT_READ_SECONDS,
    PermissionLevel.EXTERNAL_READ: TOOL_TIMEOUT_EXTERNAL_READ_SECONDS,
    PermissionLevel.MEMORY_READ: TOOL_TIMEOUT_MEMORY_READ_SECONDS,
    PermissionLevel.MEMORY_WRITE: TOOL_TIMEOUT_MEMORY_WRITE_SECONDS,
    PermissionLevel.WRITE: TOOL_TIMEOUT_WRITE_SECONDS,
    PermissionLevel.DESTRUCTIVE: TOOL_TIMEOUT_DESTRUCTIVE_SECONDS,
}


def get_tool_timeout(function_name: str) -> int:
    """
    Return the execution timeout for a registered tool.
    """

    permission = TOOL_PERMISSIONS.get(function_name)

    if permission is None:
        raise ValueError(
            f"No timeout policy exists for tool: {function_name}"
        )

    return TOOL_TIMEOUTS.get(
        permission,
        DEFAULT_TOOL_TIMEOUT_SECONDS,
    )
