from security.permissions import PermissionLevel


TOOL_PERMISSIONS = {
    "get_customers": PermissionLevel.READ,
    "get_customer_by_id": PermissionLevel.READ,
    "find_customer": PermissionLevel.READ,

    "web_search": PermissionLevel.EXTERNAL_READ,

    "recall": PermissionLevel.MEMORY_READ,
    "remember": PermissionLevel.MEMORY_WRITE,
    "forget": PermissionLevel.MEMORY_WRITE,

    "create_customer": PermissionLevel.WRITE,
    "update_customer": PermissionLevel.WRITE,
    "delete_customer": PermissionLevel.DESTRUCTIVE,
}
