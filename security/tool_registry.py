from security.permissions import PermissionLevel

TOOL_PERMISSIONS = {
    "get_customers": PermissionLevel.READ,
    "web_search": PermissionLevel.READ,
    "remember": PermissionLevel.WRITE,
    "recall": PermissionLevel.READ,
    "forget": PermissionLevel.WRITE,
    "create_customer": PermissionLevel.WRITE,
}
