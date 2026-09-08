from dataclasses import asdict, is_dataclass

from agent.registry import TOOLS
from agent.results import ToolResult


class ToolExecutor:
    """
    Executes Atlas tools requested by the model.

    The executor is the security boundary between Gemini
    function calls and Atlas tool implementations.
    """

    TOOL_LEVELS = {
        "get_customers": "READ",
        "web_search": "EXTERNAL_READ",
        "remember": "MEMORY_WRITE",
        "recall": "MEMORY_READ",
        "forget": "MEMORY_WRITE",
        "create_customer": "WRITE",
        "update_customer": "WRITE",
        "delete_customer": "DESTRUCTIVE",
    }

    ALLOWED_LEVELS = {
        "READ",
        "EXTERNAL_READ",
        "MEMORY_READ",
        "MEMORY_WRITE",
        "WRITE",
        "DESTRUCTIVE",
    }

    def __init__(self):
        self.tools = {tool.__name__: tool for tool in TOOLS}

    def get_tool_level(self, function_name: str) -> str:
        """
        Return the authorization level assigned to a tool.
        """

        level = self.TOOL_LEVELS.get(function_name)

        if not level:
            raise ValueError(
                f"No authorization policy exists for tool: "
                f"{function_name}"
            )

        return level

    def authorize(self, function_name: str) -> bool:
        """
        Determine whether a registered tool is authorized
        to execute.

        Confirmation for writes/destructive operations is
        handled by the tools themselves.
        """

        if function_name not in self.tools:
            return False

        level = self.get_tool_level(function_name)

        return level in self.ALLOWED_LEVELS

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

        print(f"🔐 AUTHORIZATION LEVEL: {level}")

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
