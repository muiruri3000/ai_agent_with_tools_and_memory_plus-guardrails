from security.permissions import PermissionLevel, requires_confirmation


def request_confirmation(
    action: str,
    description: str,
    permission_level: PermissionLevel,
) -> bool:
    """
    Ask the user to confirm an action when the assigned
    permission level requires explicit confirmation.

    The permission policy is defined centrally in
    security.permissions.
    """

    if not requires_confirmation(permission_level):
        return True

    print()
    print("⚠️  CONFIRMATION REQUIRED")
    print(f"Action: {action}")
    print(f"Permission: {permission_level.value}")
    print(f"Details: {description}")
    print()

    answer = input("Do you want Atlas to proceed? [y/N]: ")

    return answer.strip().lower() in {
        "y",
        "yes",
    }
