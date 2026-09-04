from enum import Enum


class PermissionLevel(Enum):
    READ = "read"
    WRITE = "write"
    DESTRUCTIVE = "destructive"


def requires_confirmation(level: PermissionLevel) -> bool:
    """
    Determine whether an action requires user confirmation.
    """

    return level in {
        PermissionLevel.WRITE,
        PermissionLevel.DESTRUCTIVE,
    }
