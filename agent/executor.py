from dataclasses import asdict, is_dataclass
import inspect
import signal
from typing import get_type_hints

from agent.registry import TOOLS
from agent.results import ToolResult
from security.permissions import requires_confirmation
from security.tool_registry import TOOL_PERMISSIONS
from audit.logger import AuditLogger
from security.timeouts import get_tool_timeout
from security.input_constraints import validate_tool_values

from security.roles import SecurityRole, role_allows


class ToolExecutor:
    """
    Executes Atlas tools requested by the model.

    The executor is the security boundary between Gemini
    function calls and Atlas tool implementations.
    """

    def __init__(
        self,
        role: SecurityRole = SecurityRole.STANDARD,
    ):
        self.tools = {tool.__name__: tool for tool in TOOLS}
        self.audit_logger = AuditLogger()
        self.role = role

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

    def role_allows_tool(self, function_name: str) -> bool:
        """
        Determine whether the current security role
        is permitted to execute a tool.
        """

        permission = self.get_tool_level(function_name)

        return role_allows(
            self.role,
            permission,
        )

    def authorize(self, function_name: str) -> bool:
        """
        Determine whether a registered tool has a valid
        security policy.
        """

        if function_name not in self.tools:
            return False

        self.get_tool_level(function_name)

        return True

    def role_authorizes(self, function_name: str) -> bool:
        """
        Determine whether the current security role is permitted
        to execute a tool.
        """

        if not self.role_authorizes(function_name):
            return False

        return self.role_allows_tool(function_name)

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

        Every execution attempt, validation failure, timeout,
        tool failure, and successful outcome is recorded
        in the audit log.
        """

        print("\n⚙️ EXECUTOR")
        print(f"⚙️ FUNCTION: {function_name}")
        print(f"⚙️ ARGUMENTS: {arguments}")
        print(f"🔐 SECURITY ROLE: {self.role.value}")
        tool = self.tools.get(function_name)

        if not tool:
            self.audit_logger.log(
                event="tool_denied",
                tool=function_name,
                permission="unknown",
                arguments=arguments,
                confirmation_required=False,
                success=False,
                message=(f"Unknown tool requested: " f"{function_name}"),
            )

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
                message=(f"Tool execution denied for role " f"{self.role.value}."),
            )

            raise PermissionError(
                f"Tool execution is not authorized for role "
                f"{self.role.value}: {function_name}"
            )

        self.audit_logger.log(
            event="tool_requested",
            tool=function_name,
            permission=level.value,
            arguments=arguments,
            confirmation_required=confirmation_required,
        )

        # -------------------------------------------------
        # ARGUMENT VALIDATION
        # -------------------------------------------------

        try:
            self.validate_arguments(
                tool,
                arguments,
            )

        except TypeError as exc:
            self.audit_logger.log(
                event="tool_validation_failed",
                tool=function_name,
                permission=level.value,
                arguments=arguments,
                confirmation_required=confirmation_required,
                success=False,
                message=str(exc),
            )

            print(f"❌ ARGUMENT VALIDATION FAILED: " f"{function_name}: {exc}")

            raise
        # Semantic value constraints are audited.
        try:
            validate_tool_values(
                function_name,
                arguments,
            )

        except ValueError as exc:
            self.audit_logger.log(
                event="tool_constraint_failed",
                tool=function_name,
                permission=level.value,
                arguments=arguments,
                confirmation_required=confirmation_required,
                success=False,
                message=str(exc),
            )

            print(f"❌ VALUE CONSTRAINT FAILED: " f"{function_name}: {exc}")

            raise
        # -------------------------------------------------
        # TOOL TIMEOUT
        # -------------------------------------------------

        timeout_seconds = get_tool_timeout(function_name)

        print(f"⏱️ TIMEOUT: " f"{timeout_seconds} seconds")

        try:
            result = self._run_with_timeout(
                tool,
                arguments,
                timeout_seconds,
            )

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

        except TimeoutError as exc:
            self.audit_logger.log(
                event="tool_timeout",
                tool=function_name,
                permission=level.value,
                arguments=arguments,
                confirmation_required=confirmation_required,
                success=False,
                message=str(exc),
            )

            print(f"⏱️ TOOL TIMEOUT: " f"{function_name}: {exc}")

            raise

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

            print(f"❌ TOOL ERROR: " f"{function_name}: {exc}")

            raise

    def validate_arguments(self, tool, arguments: dict):
        """
        Validate tool arguments before execution.

        The tool's Python signature is the source of truth for:
        - accepted argument names
        - required arguments
        - runtime argument types
        """

        if not isinstance(arguments, dict):
            raise TypeError("Tool arguments must be provided as a dictionary.")

        signature = inspect.signature(tool)

        try:
            signature.bind(**arguments)
        except TypeError as exc:
            raise TypeError(
                f"Invalid arguments for tool " f"{tool.__name__}: {exc}"
            ) from exc

        type_hints = get_type_hints(tool)

        for name, value in arguments.items():
            expected_type = type_hints.get(name)

            if expected_type is None:
                continue

            if not isinstance(value, expected_type):
                raise TypeError(
                    f"Invalid type for argument '{name}' "
                    f"of tool '{tool.__name__}': "
                    f"expected {expected_type.__name__}, "
                    f"got {type(value).__name__}."
                )

    def _run_with_timeout(
        self,
        tool,
        arguments,
        timeout_seconds,
    ):
        """
        Execute a tool with a hard execution timeout.

        SIGALRM is used so a timed-out tool does not continue
        executing in the background.
        """

        def handle_timeout(signum, frame):
            raise TimeoutError(
                f"Tool execution timed out after " f"{timeout_seconds} seconds."
            )

        previous_handler = signal.signal(
            signal.SIGALRM,
            handle_timeout,
        )

        signal.alarm(timeout_seconds)

        try:
            return tool(**arguments)

        finally:
            signal.alarm(0)
            signal.signal(
                signal.SIGALRM,
                previous_handler,
            )

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
