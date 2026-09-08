from dataclasses import asdict, is_dataclass

from agent.registry import TOOLS
from agent.results import ToolResult
from security.permissions import requires_confirmation
from security.tool_registry import TOOL_PERMISSIONS
from audit.logger import AuditLogger


class ToolExecutor:
    """
    Executes Atlas tools requested by the model.

    The executor is the security boundary between Gemini
    function calls and Atlas tool implementations.
    """

    def __init__(self):
        self.tools = {tool.__name__: tool for tool in TOOLS}
        self.audit_logger = AuditLogger()

    def get_tool_level(self, function_name: str):
        """
        Return the security permission assigned to a tool.
        """

        level = TOOL_PERMISSIONS.get(function_name)

        if not level:
            raise ValueError(
                f"No authorization policy exists for tool: " f"{function_name}"
            )

        return level

    def authorize(self, function_name: str) -> bool:
        """
        Determine whether a registered tool has a valid
        security policy.
        """

        if function_name not in self.tools:
            return False

        self.get_tool_level(function_name)

        return True

    def requires_confirmation(self, function_name: str) -> bool:
        """
        Determine whether a tool requires explicit
        user confirmation according to the security policy.
        """

        level = self.get_tool_level(function_name)

        return requires_confirmation(level)

    def execute(self, function_name: str, arguments: dict):
        """
        Execute a registered and authorized tool by name.

        Every execution attempt and outcome is recorded
        in the audit log.
        """

        print("\n⚙️ EXECUTOR")
        print(f"⚙️ FUNCTION: {function_name}")
        print(f"⚙️ ARGUMENTS: {arguments}")

        tool = self.tools.get(function_name)

        if not tool:
            raise ValueError(f"Unknown tool requested: {function_name}")

        level = self.get_tool_level(function_name)
        confirmation_required = self.requires_confirmation(function_name)

        print(f"🔐 PERMISSION LEVEL: {level.value}")
        print("🔐 CONFIRMATION REQUIRED: " f"{confirmation_required}")

        if not self.authorize(function_name):
            self.audit_logger.log(
                event="tool_denied",
                tool=function_name,
                permission=level.value,
                arguments=arguments,
                confirmation_required=confirmation_required,
                success=False,
                message="Tool execution was not authorized.",
            )

            raise PermissionError(
                f"Tool execution is not authorized: " f"{function_name}"
            )

        self.audit_logger.log(
            event="tool_requested",
            tool=function_name,
            permission=level.value,
            arguments=arguments,
            confirmation_required=confirmation_required,
        )

        try:
            result = tool(**arguments)

            success = result.success if isinstance(result, ToolResult) else True

            message = result.message if isinstance(result, ToolResult) else str(result)

            self.audit_logger.log(
                event="tool_completed",
                tool=function_name,
                permission=level.value,
                arguments=arguments,
                confirmation_required=confirmation_required,
                success=success,
                message=message,
            )

            print(f"⚙️ RESULT: {result}")

            return result

        except Exception as exc:
            self.audit_logger.log(
                event="tool_failed",
                tool=function_name,
                permission=level.value,
                arguments=arguments,
                confirmation_required=confirmation_required,
                success=False,
                message=str(exc),
            )

            print(f"❌ TOOL ERROR: {function_name}: {exc}")

            raise

    def serialize_result(self, result) -> dict:
        """
        Convert a tool result into a JSON-serializable dictionary
        suitable for sending back to Gemini.
        """

        if is_dataclass(result):
            return asdict(result)

        if isinstance(result, dict):
            return result

        return {
            "success": True,
            "message": str(result),
            "data": result,
        }
