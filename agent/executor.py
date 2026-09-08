from dataclasses import asdict, is_dataclass

from agent.registry import TOOLS
from agent.results import ToolResult
from security.permissions import requires_confirmation
from security.tool_registry import TOOL_PERMISSIONS


class ToolExecutor:
    """
    Executes Atlas tools requested by the model.

    The executor is the security boundary between Gemini
    function calls and Atlas tool implementations.
    """

    def __init__(self):
        self.tools = {tool.__name__: tool for tool in TOOLS}

    def get_tool_level(self, function_name: str):
        """
        Return the security permission assigned to a tool.
        """

        level = TOOL_PERMISSIONS.get(function_name)

        if not level:
            raise ValueError(
                f"No authorization policy exists for tool: "
                f"{function_name}"
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
        """

        print("\n⚙️ EXECUTOR")
        print(f"⚙️ FUNCTION: {function_name}")
        print(f"⚙️ ARGUMENTS: {arguments}")

        tool = self.tools.get(function_name)

        if not tool:
            raise ValueError(
                f"Unknown tool requested: {function_name}"
            )

        level = self.get_tool_level(function_name)

        print(f"🔐 PERMISSION LEVEL: {level.value}")
        print(
            "🔐 CONFIRMATION REQUIRED: "
            f"{self.requires_confirmation(function_name)}"
        )

        if not self.authorize(function_name):
            raise PermissionError(
                f"Tool execution is not authorized: "
                f"{function_name}"
            )

        result = tool(**arguments)

        print(f"⚙️ RESULT: {result}")

        return result

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
