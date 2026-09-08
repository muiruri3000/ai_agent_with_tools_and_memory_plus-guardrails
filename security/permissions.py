from enum import Enum


class PermissionLevel(Enum):
    """
    Permission levels used by Atlas security policy.
    """

    READ = "read"
    EXTERNAL_READ = "external_read"
    MEMORY_READ = "memory_read"
    MEMORY_WRITE = "memory_write"
    WRITE = "write"
    DESTRUCTIVE = "destructive"


def requires_confirmation(level: PermissionLevel) -> bool:
    """
    Determine whether an action requires explicit
    user confirmation before execution.
    """

    return level in {
        PermissionLevel.MEMORY_WRITE,
        PermissionLevel.WRITE,
        PermissionLevel.DESTRUCTIVE,
    }
