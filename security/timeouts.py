from security.tool_registry import TOOL_PERMISSIONS
from security.permissions import PermissionLevel


# Maximum time a tool is allowed to execute.
DEFAULT_TOOL_TIMEOUT_SECONDS = 30


TOOL_TIMEOUTS = {
    PermissionLevel.READ: 10,
    PermissionLevel.EXTERNAL_READ: 30,
    PermissionLevel.MEMORY_READ: 10,
    PermissionLevel.MEMORY_WRITE: 10,
    PermissionLevel.WRITE: 10,
    PermissionLevel.DESTRUCTIVE: 10,
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
