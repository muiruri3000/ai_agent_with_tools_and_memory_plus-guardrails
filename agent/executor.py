from dataclasses import asdict, is_dataclass

from agent.registry import TOOLS


class ToolExecutor:
    """
    Executes Atlas tools requested by the model.

    The executor provides a single boundary between
    Gemini function calls and Atlas tool implementations.
    """

    def __init__(self):
        self.tools = {tool.__name__: tool for tool in TOOLS}

    def execute(self, function_name: str, arguments: dict):
        """
        Execute a registered tool by name.

        Args:
            function_name: Name of the requested tool.
            arguments: Arguments supplied by Gemini.

        Returns:
            ToolResult returned by the tool.
        """

        print("\n⚙️ EXECUTOR")
        print(f"⚙️ FUNCTION: {function_name}")
        print(f"⚙️ ARGUMENTS: {arguments}")

        tool = self.tools.get(function_name)

        if not tool:
            raise ValueError(f"Unknown tool requested: {function_name}")

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
