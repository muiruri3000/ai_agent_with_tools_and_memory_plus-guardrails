from enum import Enum

from security.permissions import PermissionLevel


class SecurityRole(Enum):
    """
    Security profiles controlling what Atlas is allowed to do.
    """

    READ_ONLY = "read_only"
    STANDARD = "standard"
    ADMIN = "admin"


ROLE_PERMISSIONS = {
    SecurityRole.READ_ONLY: {
        PermissionLevel.READ,
        PermissionLevel.EXTERNAL_READ,
        PermissionLevel.MEMORY_READ,
    },
    SecurityRole.STANDARD: {
        PermissionLevel.READ,
        PermissionLevel.EXTERNAL_READ,
        PermissionLevel.MEMORY_READ,
        PermissionLevel.MEMORY_WRITE,
        PermissionLevel.WRITE,
    },
    SecurityRole.ADMIN: {
        PermissionLevel.READ,
        PermissionLevel.EXTERNAL_READ,
        PermissionLevel.MEMORY_READ,
        PermissionLevel.MEMORY_WRITE,
        PermissionLevel.WRITE,
        PermissionLevel.DESTRUCTIVE,
    },
}


def role_allows(
    role: SecurityRole,
    permission: PermissionLevel,
) -> bool:
    """
    Determine whether a security role permits
    a particular permission level.
    """

    allowed_permissions = ROLE_PERMISSIONS.get(role)

    if allowed_permissions is None:
        raise ValueError(f"No permission policy exists for role: {role}")

    return permission in allowed_permissions
