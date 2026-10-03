import unittest
from unittest.mock import patch

from agent.atlas import Atlas
from agent.results import ToolResult
from agent.task import AgentTask


class TestAtlasCustomerLookup(unittest.TestCase):

    @patch("agent.atlas.genai.Client")
    @patch.object(Atlas, "execute_tool")
    def test_find_customer_establishes_context(
        self,
        mock_execute_tool,
        mock_client,
    ):

        customer = {
            "id": 3,
            "name": "David",
            "email": "david@example.com",
            "city": "Thika",
        }

        mock_execute_tool.return_value = ToolResult(
            success=True,
            action="find_customer",
            message="Found 1 matching customer(s).",
            data=[customer],
        )

        atlas = Atlas()

        response = atlas.ask("Find David")

        self.assertIn("David", response)
        self.assertIn("david@example.com", response)
        self.assertIn("Thika", response)

        self.assertEqual(
            atlas.context["customer"],
            customer,
        )

        mock_execute_tool.assert_called_once_with(
            "find_customer",
            {
                "name": "David",
                "email": None,
                "city": None,
            },
        )


class TestAtlasCustomerContext(unittest.TestCase):

    @patch("agent.atlas.genai.Client")
    def test_context_follow_up_email(
        self,
        mock_client,
    ):

        atlas = Atlas()

        atlas.context["customer"] = {
            "id": 3,
            "name": "David",
            "email": "david@example.com",
            "city": "Thika",
        }

        response = atlas.ask("What is his email?")

        self.assertEqual(
            response,
            "David's email is david@example.com.",
        )


class TestAtlasCustomerDelete(unittest.TestCase):

    @patch("agent.atlas.genai.Client")
    @patch.object(Atlas, "execute_tool")
    def test_successful_delete_clears_context(
        self,
        mock_execute_tool,
        mock_client,
    ):

        customer = {
            "id": 3,
            "name": "David",
            "email": "david@example.com",
            "city": "Thika",
        }

        find_result = ToolResult(
            success=True,
            action="find_customer",
            message="Found 1 matching customer(s).",
            data=[customer],
        )

        delete_result = ToolResult(
            success=True,
            action="delete_customer",
            message="Customer deleted successfully.",
            data=customer,
        )

        def execute_tool(name, arguments):
            if name == "find_customer":
                return find_result
            if name == "delete_customer":
                return delete_result
            raise AssertionError(f"Unexpected tool: {name}")

        mock_execute_tool.side_effect = execute_tool

        atlas = Atlas()

        atlas.ask("Find David")

        self.assertIsNotNone(atlas.context["customer"])

        response = atlas.ask("Delete David")

        self.assertIn(
            "David has been successfully deleted",
            response,
        )

        self.assertTrue(
            any(
                call.args == (
                    "delete_customer",
                    {"customer_id": 3},
                )
                for call in mock_execute_tool.call_args_list
            )
        )

        self.assertIsNone(atlas.context["customer"])


class TestAtlasCustomerUpdate(unittest.TestCase):

    @patch("agent.atlas.genai.Client")
    @patch.object(Atlas, "execute_tool")
    def test_successful_update_refreshes_context(
        self,
        mock_execute_tool,
        mock_client,
    ):

        customer = {
            "id": 4,
            "name": "John Kamau",
            "email": "john@example.com",
            "city": "Nairobi",
        }

        updated_customer = {
            "id": 4,
            "name": "John Kamau",
            "email": "john@example.com",
            "city": "Embu",
        }

        def execute_tool(name, arguments):
            if name == "find_customer":
                return ToolResult(
                    success=True,
                    action="find_customer",
                    message="Found 1 matching customer(s).",
                    data=[customer],
                )
            if name == "update_customer":
                return ToolResult(
                    success=True,
                    action="update_customer",
                    message="Customer updated successfully.",
                    data=updated_customer,
                )
            raise AssertionError(f"Unexpected tool: {name}")

        mock_execute_tool.side_effect = execute_tool

        atlas = Atlas()

        atlas.ask("Find John Kamau")

        response = atlas.ask("Change his city to Embu")

        self.assertIn(
            "successfully updated",
            response,
        )

        self.assertEqual(
            atlas.context["customer"]["city"],
            "Embu",
        )


class TestAtlasUpdateSafety(unittest.TestCase):

    @patch("agent.atlas.genai.Client")
    @patch.object(Atlas, "execute_tool")
    def test_name_based_update_refreshes_context(
        self,
        mock_execute_tool,
        mock_client,
    ):

        customer = {
            "id": 4,
            "name": "John Kamau",
            "email": "john@example.com",
            "city": "Nairobi",
        }

        updated_customer = {
            "id": 4,
            "name": "John Mwangi",
            "email": "john@example.com",
            "city": "Nairobi",
        }

        def execute_tool(name, arguments):
            if name == "find_customer":
                return ToolResult(
                    success=True,
                    action="find_customer",
                    message="Found 1 matching customer(s).",
                    data=[customer],
                )
            if name == "update_customer":
                return ToolResult(
                    success=True,
                    action="update_customer",
                    message="Customer updated successfully.",
                    data=updated_customer,
                )
            raise AssertionError(f"Unexpected tool: {name}")

        mock_execute_tool.side_effect = execute_tool

        atlas = Atlas()

        atlas.ask("Find John Kamau")

        response = atlas.ask(
            "Change John Kamau's name to John Mwangi"
        )

        self.assertIn(
            "successfully updated",
            response,
        )

        self.assertTrue(
            any(
                call.args == (
                    "update_customer",
                    {
                        "customer_id": 4,
                        "name": "John Mwangi",
                        "email": None,
                        "city": None,
                    },
                )
                for call in mock_execute_tool.call_args_list
            )
        )

        self.assertEqual(
            atlas.context["customer"],
            updated_customer,
        )

    @patch("agent.atlas.genai.Client")
    @patch.object(Atlas, "execute_tool")
    def test_id_based_update_refreshes_context(
        self,
        mock_execute_tool,
        mock_client,
    ):

        customer = {
            "id": 4,
            "name": "John Kamau",
            "email": "john@example.com",
            "city": "Nairobi",
        }

        updated_customer = {
            "id": 4,
            "name": "John Kamau",
            "email": "john@example.com",
            "city": "Embu",
        }

        def execute_tool(name, arguments):
            if name == "get_customer_by_id":
                return ToolResult(
                    success=True,
                    action="get_customer_by_id",
                    message="Customer retrieved successfully.",
                    data=customer,
                )
            if name == "update_customer":
                return ToolResult(
                    success=True,
                    action="update_customer",
                    message="Customer updated successfully.",
                    data=updated_customer,
                )
            raise AssertionError(f"Unexpected tool: {name}")

        mock_execute_tool.side_effect = execute_tool

        atlas = Atlas()

        response = atlas.ask(
            "Change customer ID 4's city to Embu"
        )

        self.assertIn(
            "successfully updated",
            response,
        )

        self.assertTrue(
            any(
                call.args == (
                    "get_customer_by_id",
                    {"customer_id": 4},
                )
                for call in mock_execute_tool.call_args_list
            )
        )

        self.assertTrue(
            any(
                call.args == (
                    "update_customer",
                    {
                        "customer_id": 4,
                        "name": None,
                        "email": None,
                        "city": "Embu",
                    },
                )
                for call in mock_execute_tool.call_args_list
            )
        )

        self.assertEqual(
            atlas.context["customer"],
            updated_customer,
        )

    @patch("agent.atlas.genai.Client")
    @patch.object(Atlas, "execute_tool")
    def test_ambiguous_update_does_not_change_context(
        self,
        mock_execute_tool,
        mock_client,
    ):

        john_one = {
            "id": 1,
            "name": "John",
            "email": "john1@example.com",
            "city": "Nairobi",
        }

        john_two = {
            "id": 2,
            "name": "John",
            "email": "john2@example.com",
            "city": "Thika",
        }

        david = {
            "id": 3,
            "name": "David",
            "email": "david@example.com",
            "city": "Thika",
        }

        atlas = Atlas()
        atlas.context["customer"] = david

        mock_execute_tool.return_value = ToolResult(
            success=True,
            action="find_customer",
            message="Found 2 matching customer(s).",
            data=[john_one, john_two],
        )

        response = atlas.ask(
            "Change John city's city to Embu"
        )

        self.assertIn(
            "2 customers matching",
            response.lower(),
        )

        self.assertFalse(
            any(
                call.args[0] == "update_customer"
                for call in mock_execute_tool.call_args_list
            )
        )

        self.assertEqual(
            atlas.context["customer"],
            david,
        )

    @patch("agent.atlas.genai.Client")
    @patch.object(Atlas, "execute_tool")
    def test_failed_update_preserves_context(
        self,
        mock_execute_tool,
        mock_client,
    ):

        customer = {
            "id": 4,
            "name": "John Kamau",
            "email": "john@example.com",
            "city": "Nairobi",
        }

        atlas = Atlas()
        atlas.context["customer"] = customer

        def execute_tool(name, arguments):
            if name == "find_customer":
                return ToolResult(
                    success=True,
                    action="find_customer",
                    message="Found 1 matching customer(s).",
                    data=[customer],
                )
            if name == "update_customer":
                return ToolResult(
                    success=False,
                    action="update_customer",
                    message="Update failed.",
                    data=None,
                )
            raise AssertionError(f"Unexpected tool: {name}")

        mock_execute_tool.side_effect = execute_tool

        response = atlas.ask(
            "Change John Kamau's city to Embu"
        )

        self.assertIn(
            "update failed",
            response.lower(),
        )

        self.assertEqual(
            atlas.context["customer"],
            customer,
        )


class TestAtlasLookupSafety(unittest.TestCase):

    @patch("agent.atlas.genai.Client")
    @patch.object(Atlas, "execute_tool")
    def test_ambiguous_lookup_does_not_establish_context(
        self,
        mock_execute_tool,
        mock_client,
    ):

        customers = [
            {
                "id": 1,
                "name": "John",
                "email": "john1@example.com",
                "city": "Nairobi",
            },
            {
                "id": 2,
                "name": "John",
                "email": "john2@example.com",
                "city": "Thika",
            },
        ]

        mock_execute_tool.return_value = ToolResult(
            success=True,
            action="find_customer",
            message="Found 2 matching customer(s).",
            data=customers,
        )

        atlas = Atlas()

        response = atlas.ask("Find John")

        self.assertIn(
            "2 matching customers",
            response.lower(),
        )

        self.assertIsNone(
            atlas.context["customer"]
        )

    @patch("agent.atlas.genai.Client")
    @patch.object(Atlas, "execute_tool")
    def test_failed_lookup_does_not_establish_context(
        self,
        mock_execute_tool,
        mock_client,
    ):

        mock_execute_tool.return_value = ToolResult(
            success=True,
            action="find_customer",
            message="Found 0 matching customer(s).",
            data=[],
        )

        atlas = Atlas()

        response = atlas.ask("Find Nobody")

        self.assertIn(
            "could not find",
            response.lower(),
        )

        self.assertIsNone(
            atlas.context["customer"]
        )


class TestAtlasDeleteSafety(unittest.TestCase):

    @patch("agent.atlas.genai.Client")
    @patch.object(Atlas, "execute_tool")
    def test_failed_delete_preserves_context(
        self,
        mock_execute_tool,
        mock_client,
    ):

        customer = {
            "id": 3,
            "name": "David",
            "email": "david@example.com",
            "city": "Thika",
        }

        def execute_tool(name, arguments):
            if name == "find_customer":
                return ToolResult(
                    success=True,
                    action="find_customer",
                    message="Found 1 matching customer(s).",
                    data=[customer],
                )
            if name == "delete_customer":
                return ToolResult(
                    success=False,
                    action="delete_customer",
                    message="User declined customer deletion.",
                    data=None,
                )
            raise AssertionError(f"Unexpected tool: {name}")

        mock_execute_tool.side_effect = execute_tool

        atlas = Atlas()

        atlas.ask("Find David")

        response = atlas.ask("Delete David")

        self.assertIn(
            "declined",
            response.lower(),
        )

        self.assertEqual(
            atlas.context["customer"]["id"],
            3,
        )


class TestAtlasAgenticLoop(unittest.TestCase):

    @patch("agent.atlas.genai.Client")
    def test_dependent_multi_step_workflow(self, mock_client):
        atlas = Atlas()

        find_call = type(
            "FunctionCall",
            (),
            {
                "name": "find_customer",
                "args": {
                    "name": "John Kamau",
                    "email": None,
                    "city": None,
                },
            },
        )()

        update_call = type(
            "FunctionCall",
            (),
            {
                "name": "update_customer",
                "args": {
                    "customer_id": 7,
                    "name": None,
                    "email": None,
                    "city": "Thika",
                },
            },
        )()

        first_response = type(
            "Response",
            (),
            {
                "function_calls": [find_call],
                "text": None,
            },
        )()

        second_response = type(
            "Response",
            (),
            {
                "function_calls": [update_call],
                "text": None,
            },
        )()

        final_response = type(
            "Response",
            (),
            {
                "function_calls": [],
                "text": "John Kamau's city has been updated to Thika.",
            },
        )()

        atlas.chat.send_message.side_effect = [
            first_response,
            second_response,
            final_response,
        ]

        customer = {
            "id": 7,
            "name": "John Kamau",
            "email": "john@example.com",
            "city": "Nairobi",
        }

        updated_customer = {
            **customer,
            "city": "Thika",
        }

        atlas.executor.execute = unittest.mock.Mock(
            side_effect=[
                ToolResult(
                    success=True,
                    action="find_customer",
                    message="Found 1 matching customer(s).",
                    data=[customer],
                ),
                ToolResult(
                    success=True,
                    action="update_customer",
                    message="Customer updated successfully.",
                    data=updated_customer,
                ),
            ]
        )

        atlas.executor.serialize_result = unittest.mock.Mock(
            side_effect=lambda result: {
                "success": result.success,
                "action": result.action,
                "message": result.message,
                "data": result.data,
            }
        )

        response = atlas.handle_gemini(
            "Find John Kamau and change his city to Thika."
        )

        self.assertEqual(
            response,
            "John Kamau's city has been updated to Thika.",
        )

        self.assertEqual(
            atlas.executor.execute.call_count,
            2,
        )

        calls = atlas.executor.execute.call_args_list

        self.assertEqual(
            calls[0].args[0],
            "find_customer",
        )

        self.assertEqual(
            calls[1].args[0],
            "update_customer",
        )

        self.assertEqual(
            calls[1].args[1]["customer_id"],
            7,
        )

        self.assertEqual(
            atlas.chat.send_message.call_count,
            3,
        )

    @patch("agent.atlas.genai.Client")
    def test_ask_runs_complete_agentic_workflow(
        self,
        mock_client,
    ):
        atlas = Atlas()

        tool_call = type(
            "FunctionCall",
            (),
            {
                "name": "web_search",
                "args": {"query": "AWS STS"},
            },
        )()

        first_response = type(
            "Response",
            (),
            {
                "function_calls": [tool_call],
                "text": None,
            },
        )()

        final_response = type(
            "Response",
            (),
            {
                "function_calls": [],
                "text": "AWS STS provides temporary security credentials.",
            },
        )()

        atlas.chat.send_message.side_effect = [
            first_response,
            final_response,
        ]

        atlas.executor.execute = unittest.mock.Mock(
            return_value=ToolResult(
                success=True,
                action="web_search",
                message="AWS STS documentation result",
                data=["Temporary security credentials"],
            )
        )

        atlas.executor.serialize_result = unittest.mock.Mock(
            side_effect=lambda result: {
                "success": result.success,
                "action": result.action,
                "message": result.message,
                "data": result.data,
            }
        )

        response = atlas.ask(
            "What is AWS STS?"
        )

        self.assertEqual(
            response,
            "AWS STS provides temporary security credentials.",
        )

        atlas.executor.execute.assert_called_once_with(
            "web_search",
            {"query": "AWS STS"},
        )

        self.assertEqual(
            atlas.chat.send_message.call_count,
            2,
        )

        first_request = atlas.chat.send_message.call_args_list[0].args[0]

        self.assertEqual(
            first_request,
            "What is AWS STS?",
        )

        second_request = atlas.chat.send_message.call_args_list[1].args[0]

        self.assertEqual(
            len(second_request),
            1,
        )

        observation = second_request[0]

        self.assertEqual(
            observation.function_response.name,
            "web_search",
        )

        self.assertEqual(
            observation.function_response.response,
            {
                "success": True,
                "action": "web_search",
                "message": "AWS STS documentation result",
                "data": ["Temporary security credentials"],
            },
        )


    @patch("agent.atlas.genai.Client")
    def test_multiple_tool_calls_in_one_iteration(
        self,
        mock_client,
    ):
        atlas = Atlas()

        tool_call_1 = type(
            "FunctionCall",
            (),
            {
                "name": "web_search",
                "args": {"query": "latest AWS Lambda features"},
            },
        )()

        tool_call_2 = type(
            "FunctionCall",
            (),
            {
                "name": "web_search",
                "args": {"query": "latest AWS Step Functions features"},
            },
        )()

        first_response = type(
            "Response",
            (),
            {
                "function_calls": [tool_call_1, tool_call_2],
                "text": None,
            },
        )()

        final_response = type(
            "Response",
            (),
            {
                "function_calls": [],
                "text": "Here is the comparison.",
            },
        )()

        atlas.chat.send_message.side_effect = [
            first_response,
            final_response,
        ]

        atlas.executor.execute = unittest.mock.Mock(
            side_effect=[
                ToolResult(
                    success=True,
                    action="web_search",
                    message="Lambda results",
                    data=[],
                ),
                ToolResult(
                    success=True,
                    action="web_search",
                    message="Step Functions results",
                    data=[],
                ),
            ]
        )

        atlas.executor.serialize_result = unittest.mock.Mock(
            side_effect=lambda result: {
                "success": result.success,
                "action": result.action,
                "message": result.message,
                "data": result.data,
            }
        )

        response = atlas.handle_gemini(
            "Compare the latest AWS Lambda and Step Functions features."
        )

        self.assertEqual(
            response,
            "Here is the comparison.",
        )

        self.assertEqual(
            atlas.executor.execute.call_count,
            2,
        )

        calls = atlas.executor.execute.call_args_list

        self.assertEqual(
            calls[0].args[0],
            "web_search",
        )

        self.assertEqual(
            calls[0].args[1],
            {"query": "latest AWS Lambda features"},
        )

        self.assertEqual(
            calls[1].args[0],
            "web_search",
        )

        self.assertEqual(
            calls[1].args[1],
            {"query": "latest AWS Step Functions features"},
        )

        self.assertEqual(
            atlas.chat.send_message.call_count,
            2,
        )
    @patch("agent.atlas.genai.Client")
    def test_find_customer_result_is_returned_to_gemini(
        self,
        mock_client,
    ):
        atlas = Atlas()

        tool_call = type(
            "FunctionCall",
            (),
            {
                "name": "find_customer",
                "args": {
                    "name": "John Kamau",
                    "email": None,
                    "city": None,
                },
            },
        )()

        first_response = type(
            "Response",
            (),
            {
                "function_calls": [tool_call],
                "text": None,
            },
        )()

        final_response = type(
            "Response",
            (),
            {
                "function_calls": [],
                "text": "John Kamau lives in Nairobi.",
            },
        )()

        atlas.chat.send_message.side_effect = [
            first_response,
            final_response,
        ]

        customer = {
            "id": 7,
            "name": "John Kamau",
            "email": "john@example.com",
            "city": "Nairobi",
        }

        atlas.executor.execute = unittest.mock.Mock(
            return_value=ToolResult(
                success=True,
                action="find_customer",
                message="Found 1 matching customer(s).",
                data=[customer],
            )
        )

        atlas.executor.serialize_result = unittest.mock.Mock(
            side_effect=lambda result: {
                "success": result.success,
                "action": result.action,
                "message": result.message,
                "data": result.data,
            }
        )

        response = atlas.handle_gemini(
            "What city does John Kamau currently live in?"
        )

        self.assertEqual(
            response,
            "John Kamau lives in Nairobi.",
        )

        atlas.executor.execute.assert_called_once_with(
            "find_customer",
            {
                "name": "John Kamau",
                "email": None,
                "city": None,
            },
        )

        self.assertEqual(
            atlas.chat.send_message.call_count,
            2,
        )

        function_response_message = (
            atlas.chat.send_message.call_args_list[1].args[0]
        )

        self.assertEqual(
            len(function_response_message),
            1,
        )

        function_response = function_response_message[0]

        self.assertEqual(
            function_response.function_response.name,
            "find_customer",
        )
    
    @patch("agent.atlas.genai.Client")
    def test_sequential_tool_calls_across_iterations(
        self,
        mock_client,
    ):
        atlas = Atlas()

        tool_call_1 = type(
            "FunctionCall",
            (),
            {
                "name": "web_search",
                "args": {"query": "AWS Lambda"},
            },
        )()

        tool_call_2 = type(
            "FunctionCall",
            (),
            {
                "name": "web_search",
                "args": {"query": "AWS Step Functions"},
            },
        )()

        response_1 = type(
            "Response",
            (),
            {
                "function_calls": [tool_call_1],
                "text": None,
            },
        )()

        response_2 = type(
            "Response",
            (),
            {
                "function_calls": [tool_call_2],
                "text": None,
            },
        )()

        final_response = type(
            "Response",
            (),
            {
                "function_calls": [],
                "text": "Comparison complete.",
            },
        )()

        atlas.chat.send_message.side_effect = [
            response_1,
            response_2,
            final_response,
        ]

        atlas.executor.execute = unittest.mock.Mock(
            side_effect=[
                ToolResult(
                    success=True,
                    action="web_search",
                    message="Lambda result",
                    data=[],
                ),
                ToolResult(
                    success=True,
                    action="web_search",
                    message="Step Functions result",
                    data=[],
                ),
            ]
        )

        atlas.executor.serialize_result = unittest.mock.Mock(
            side_effect=lambda result: {
                "success": result.success,
                "action": result.action,
                "message": result.message,
                "data": result.data,
            }
        )

        response = atlas.handle_gemini(
            "Compare Lambda and Step Functions."
        )

        self.assertEqual(
            response,
            "Comparison complete.",
        )

        self.assertEqual(
            atlas.executor.execute.call_count,
            2,
        )

        self.assertEqual(
            atlas.chat.send_message.call_count,
            3,
        )
                # The observation from the first tool must be returned to Gemini
        # before Gemini decides on the next tool call.
        second_request = atlas.chat.send_message.call_args_list[1].args[0]

        self.assertEqual(
            len(second_request),
            1,
        )

        first_observation = second_request[0]

        self.assertEqual(
            first_observation.function_response.name,
            "web_search",
        )

        self.assertEqual(
            first_observation.function_response.response,
            {
                "success": True,
                "action": "web_search",
                "message": "Lambda result",
                "data": [],
            },
        )

        calls = atlas.executor.execute.call_args_list

        self.assertEqual(
            calls[0].args[1],
            {"query": "AWS Lambda"},
        )

        self.assertEqual(
            calls[1].args[1],
            {"query": "AWS Step Functions"},
        )


    @patch("agent.atlas.genai.Client")
    def test_max_tool_iterations_stops_runaway_loop(
        self,
        mock_client,
    ):
        atlas = Atlas()

        tool_call = type(
            "FunctionCall",
            (),
            {
                "name": "web_search",
                "args": {"query": "AWS Lambda"},
            },
        )()

        looping_response = type(
            "Response",
            (),
            {
                "function_calls": [tool_call],
                "text": None,
            },
        )()

        atlas.chat.send_message.return_value = looping_response

        atlas.executor.execute = unittest.mock.Mock(
            return_value=ToolResult(
                success=True,
                action="web_search",
                message="Search result",
                data=[],
            )
        )

        atlas.executor.serialize_result = unittest.mock.Mock(
            return_value={
                "success": True,
                "action": "web_search",
                "message": "Search result",
                "data": [],
            }
        )

        response = atlas.handle_gemini(
            "Keep searching forever."
        )

        self.assertEqual(
            response,
            "I stopped the tool execution because the maximum "
            "number of tool iterations was reached.",
        )

        self.assertEqual(
            atlas.executor.execute.call_count,
            Atlas.MAX_TOOL_ITERATIONS,
        )

        self.assertEqual(
            atlas.chat.send_message.call_count,
            Atlas.MAX_TOOL_ITERATIONS + 1,
        )

class TestAtlasAgentContext(unittest.TestCase):

    @patch("agent.atlas.genai.Client")
    def test_agentic_request_receives_current_customer_context(
        self,
        mock_client,
    ):
        atlas = Atlas()

        atlas.context["customer"] = {
            "id": 7,
            "name": "John Kamau",
            "email": "john@example.com",
            "city": "Nairobi",
        }

        final_response = type(
            "Response",
            (),
            {
                "function_calls": [],
                "text": "John Kamau is currently associated with Nairobi.",
            },
        )()

        atlas.chat.send_message.return_value = final_response

        response = atlas.handle_gemini(
            "Tell me something about the current customer."
        )

        self.assertEqual(
            response,
            "John Kamau is currently associated with Nairobi.",
        )

        sent_message = atlas.chat.send_message.call_args.args[0]

        self.assertIn(
            "Tell me something about the current customer.",
            sent_message,
        )

        self.assertIn(
            "CURRENT ATLAS CUSTOMER CONTEXT",
            sent_message,
        )

        self.assertIn(
            "Customer ID: 7",
            sent_message,
        )

        self.assertIn(
            "Name: John Kamau",
            sent_message,
        )

        self.assertIn(
            "Email: john@example.com",
            sent_message,
        )

        self.assertIn(
            "City: Nairobi",
            sent_message,
        )

    @patch("agent.atlas.genai.Client")
    def test_agentic_request_without_customer_context_preserves_message(
        self,
        mock_client,
    ):
        atlas = Atlas()

        final_response = type(
            "Response",
            (),
            {
                "function_calls": [],
                "text": "Here is the answer.",
            },
        )()

        atlas.chat.send_message.return_value = final_response

        atlas.handle_gemini("What is AWS STS?")

        sent_message = atlas.chat.send_message.call_args.args[0]

        self.assertEqual(
            sent_message,
            "What is AWS STS?",
        )

        self.assertNotIn(
            "CURRENT ATLAS CUSTOMER CONTEXT",
            sent_message,
        )


class TestAtlasTaskState(unittest.TestCase):

    @patch("agent.atlas.genai.Client")
    def test_ask_creates_and_completes_task(
        self,
        mock_client,
    ):
        atlas = Atlas()

        final_response = type(
            "Response",
            (),
            {
                "function_calls": [],
                "text": "Here is the answer.",
            },
        )()

        atlas.chat.send_message.return_value = final_response

        response = atlas.ask("What is AWS STS?")

        self.assertEqual(response, "Here is the answer.")
        self.assertIsNotNone(atlas.current_task)
        self.assertEqual(atlas.current_task.goal, "What is AWS STS?")
        self.assertEqual(
            atlas.current_task.status.value,
            "completed",
        )
        self.assertEqual(
            atlas.current_task.result,
            "Here is the answer.",
        )

    @patch("agent.atlas.genai.Client")
    def test_deterministic_request_completes_task(
        self,
        mock_client,
    ):
        atlas = Atlas()

        atlas.handle_customer_lookup = unittest.mock.Mock(
            return_value="Customer found."
        )

        response = atlas.ask("Find John Kamau")

        self.assertEqual(response, "Customer found.")
        self.assertIsNotNone(atlas.current_task)
        self.assertEqual(
            atlas.current_task.goal,
            "Find John Kamau",
        )
        self.assertEqual(
            atlas.current_task.status.value,
            "completed",
        )
        self.assertEqual(
            atlas.current_task.result,
            "Customer found.",
        )

    @patch("agent.atlas.genai.Client")
    def test_gemini_tool_loop_tracks_task_iterations(
        self,
        mock_client,
    ):
        atlas = Atlas()

        tool_call = type(
            "FunctionCall",
            (),
            {
                "name": "web_search",
                "args": {
                    "query": "AWS STS",
                },
            },
        )()

        first_response = type(
            "Response",
            (),
            {
                "function_calls": [tool_call],
                "text": None,
            },
        )()

        final_response = type(
            "Response",
            (),
            {
                "function_calls": [],
                "text": "AWS STS provides temporary credentials.",
            },
        )()

        atlas.chat.send_message.side_effect = [
            first_response,
            final_response,
        ]

        atlas.executor.execute = unittest.mock.Mock(
            return_value=ToolResult(
                success=True,
                action="web_search",
                message="Search completed.",
                data=[],
            )
        )

        atlas.executor.serialize_result = unittest.mock.Mock(
            side_effect=lambda result: {
                "success": result.success,
                "action": result.action,
                "message": result.message,
                "data": result.data,
            }
        )

        atlas.current_task = AgentTask(
            goal="Explain AWS STS"
        )
        atlas.current_task.start()

        response = atlas.handle_gemini("Explain AWS STS")

        self.assertEqual(
            response,
            "AWS STS provides temporary credentials.",
        )
        self.assertEqual(
            atlas.current_task.iteration,
            1,
        )
        self.assertEqual(
            atlas.current_task.status.value,
            "completed",
        )
        self.assertEqual(
            atlas.current_task.result,
            "AWS STS provides temporary credentials.",
        )

    @patch("agent.atlas.genai.Client")
    def test_failed_gemini_request_marks_task_failed(
        self,
        mock_client,
    ):
        atlas = Atlas()

        atlas.current_task = AgentTask(
            goal="Explain AWS STS"
        )
        atlas.current_task.start()

        atlas.chat.send_message.side_effect = RuntimeError(
            "Gemini unavailable."
        )

        with self.assertRaises(RuntimeError):
            atlas.handle_gemini("Explain AWS STS")

        self.assertEqual(
            atlas.current_task.status.value,
            "failed",
        )
        self.assertEqual(
            atlas.current_task.error,
            "Gemini unavailable.",
        )


class TestAtlasToolFailureRecovery(unittest.TestCase):

    @patch("agent.atlas.genai.Client")
    def test_tool_failure_is_returned_to_gemini(
        self,
        mock_client,
    ):
        atlas = Atlas()

        tool_call = type(
            "FunctionCall",
            (),
            {
                "name": "web_search",
                "args": {
                    "query": "latest AWS Lambda features"
                },
            },
        )()

        first_response = type(
            "Response",
            (),
            {
                "function_calls": [tool_call],
                "text": None,
            },
        )()

        final_response = type(
            "Response",
            (),
            {
                "function_calls": [],
                "text": "The search failed, so I cannot verify the latest features.",
            },
        )()

        atlas.chat.send_message.side_effect = [
            first_response,
            final_response,
        ]

        atlas.executor.execute = unittest.mock.Mock(
            side_effect=RuntimeError(
                "Network connection failed."
            )
        )

        atlas.executor.serialize_result = unittest.mock.Mock(
            side_effect=lambda result: {
                "success": result.success,
                "action": result.action,
                "message": result.message,
                "data": result.data,
            }
        )

        response = atlas.handle_gemini(
            "Find the latest AWS Lambda features."
        )

        self.assertEqual(
            response,
            "The search failed, so I cannot verify the latest features.",
        )

        atlas.executor.execute.assert_called_once_with(
            "web_search",
            {
                "query": "latest AWS Lambda features"
            },
        )

        atlas.executor.serialize_result.assert_called_once()

        failed_result = (
            atlas.executor.serialize_result.call_args.args[0]
        )

        self.assertFalse(
            failed_result.success
        )

        self.assertEqual(
            failed_result.action,
            "web_search",
        )

        self.assertIn(
            "Tool execution failed",
            failed_result.message,
        )

        self.assertIn(
            "Network connection failed",
            failed_result.message,
        )

        self.assertEqual(
            atlas.chat.send_message.call_count,
            2,
        )


    @patch("agent.atlas.genai.Client")
    def test_tool_failure_does_not_break_remaining_tool_calls(
        self,
        mock_client,
    ):
        atlas = Atlas()

        failed_call = type(
            "FunctionCall",
            (),
            {
                "name": "web_search",
                "args": {
                    "query": "AWS Lambda"
                },
            },
        )()

        successful_call = type(
            "FunctionCall",
            (),
            {
                "name": "web_search",
                "args": {
                    "query": "AWS Step Functions"
                },
            },
        )()

        first_response = type(
            "Response",
            (),
            {
                "function_calls": [
                    failed_call,
                    successful_call,
                ],
                "text": None,
            },
        )()

        final_response = type(
            "Response",
            (),
            {
                "function_calls": [],
                "text": "I recovered from the failed Lambda search.",
            },
        )()

        atlas.chat.send_message.side_effect = [
            first_response,
            final_response,
        ]

        atlas.executor.execute = unittest.mock.Mock(
            side_effect=[
                RuntimeError("Lambda search failed."),
                ToolResult(
                    success=True,
                    action="web_search",
                    message="Step Functions search succeeded.",
                    data=[],
                ),
            ]
        )

        atlas.executor.serialize_result = unittest.mock.Mock(
            side_effect=lambda result: {
                "success": result.success,
                "action": result.action,
                "message": result.message,
                "data": result.data,
            }
        )

        response = atlas.handle_gemini(
            "Search Lambda and Step Functions."
        )

        self.assertEqual(
            response,
            "I recovered from the failed Lambda search.",
        )

        self.assertEqual(
            atlas.executor.execute.call_count,
            2,
        )

        self.assertEqual(
            atlas.executor.serialize_result.call_count,
            2,
        )

        results = [
            call.args[0]
            for call in atlas.executor.serialize_result.call_args_list
        ]

        self.assertFalse(results[0].success)
        self.assertTrue(results[1].success)
class TestToolAuthorization(unittest.TestCase):

    def test_all_registered_tools_have_authorization_policy(self):
        from agent.executor import ToolExecutor
        from security.tool_registry import TOOL_PERMISSIONS

        executor = ToolExecutor()

        for tool_name in executor.tools:
            self.assertIn(
                tool_name,
                TOOL_PERMISSIONS,
            )

    def test_read_tools_have_read_level(self):
        from agent.executor import ToolExecutor
        from security.permissions import PermissionLevel

        executor = ToolExecutor()

        for tool_name in [
            "get_customers",
        ]:
            self.assertEqual(
                executor.get_tool_level(tool_name),
                PermissionLevel.READ,
            )

            self.assertTrue(
                executor.authorize(tool_name)
            )

    def test_external_read_tool_has_external_read_level(self):
        from agent.executor import ToolExecutor
        from security.permissions import PermissionLevel

        executor = ToolExecutor()

        self.assertEqual(
            executor.get_tool_level("web_search"),
            PermissionLevel.EXTERNAL_READ,
        )

        self.assertTrue(
            executor.authorize("web_search")
        )

    def test_memory_read_tool_has_memory_read_level(self):
        from agent.executor import ToolExecutor
        from security.permissions import PermissionLevel

        executor = ToolExecutor()

        self.assertEqual(
            executor.get_tool_level("recall"),
            PermissionLevel.MEMORY_READ,
        )

        self.assertTrue(
            executor.authorize("recall")
        )

    def test_memory_write_tools_have_memory_write_level(self):
        from agent.executor import ToolExecutor
        from security.permissions import PermissionLevel

        executor = ToolExecutor()

        for tool_name in [
            "remember",
            "forget",
        ]:
            self.assertEqual(
                executor.get_tool_level(tool_name),
                PermissionLevel.MEMORY_WRITE,
            )

            self.assertTrue(
                executor.authorize(tool_name)
            )

    def test_customer_write_tools_have_write_level(self):
        from agent.executor import ToolExecutor
        from security.permissions import PermissionLevel

        executor = ToolExecutor()

        for tool_name in [
            "create_customer",
            "update_customer",
        ]:
            self.assertEqual(
                executor.get_tool_level(tool_name),
                PermissionLevel.WRITE,
            )

            self.assertTrue(
                executor.authorize(tool_name)
            )

    def test_delete_customer_has_destructive_level(self):
        from agent.executor import ToolExecutor
        from security.permissions import PermissionLevel

        executor = ToolExecutor()

        self.assertEqual(
            executor.get_tool_level("delete_customer"),
            PermissionLevel.DESTRUCTIVE,
        )

        self.assertTrue(
            executor.authorize("delete_customer")
        )

    def test_read_operations_do_not_require_confirmation(self):
        from agent.executor import ToolExecutor

        executor = ToolExecutor()

        for tool_name in [
            "get_customers",
            "get_customer_by_id",
            "find_customer",
            "web_search",
            "recall",
        ]:
            self.assertFalse(
                executor.requires_confirmation(tool_name)
            )

    def test_write_operations_require_confirmation(self):
        from agent.executor import ToolExecutor

        executor = ToolExecutor()

        for tool_name in [
            "remember",
            "forget",
            "create_customer",
            "update_customer",
            "delete_customer",
        ]:
            self.assertTrue(
                executor.requires_confirmation(tool_name)
            )

    def test_unknown_tool_has_no_authorization_policy(self):
        from agent.executor import ToolExecutor

        executor = ToolExecutor()

        with self.assertRaises(ValueError):
            executor.get_tool_level("unknown_tool")

    def test_unknown_tool_is_not_authorized(self):
        from agent.executor import ToolExecutor

        executor = ToolExecutor()

        self.assertFalse(
            executor.authorize("unknown_tool")
        )


class TestToolRegistryContract(unittest.TestCase):

    def test_find_customer_is_registered_for_executor_and_gemini(self):
        from agent.registry import GEMINI_TOOLS, TOOLS

        tool_names = {
            tool.__name__
            for tool in TOOLS
        }

        gemini_tool_names = {
            declaration.name
            for declaration in GEMINI_TOOLS.function_declarations
        }

        self.assertIn(
            "find_customer",
            tool_names,
        )

        self.assertIn(
            "find_customer",
            gemini_tool_names,
        )


class TestConfirmationPolicy(unittest.TestCase):

    def test_read_permission_does_not_require_confirmation(self):
        from security.confirmation import request_confirmation
        from security.permissions import PermissionLevel
        from unittest.mock import patch

        with patch("builtins.input") as mock_input:
            result = request_confirmation(
                action="Read customers",
                description="Retrieve customer list.",
                permission_level=PermissionLevel.READ,
            )

        self.assertTrue(result)
        mock_input.assert_not_called()

    def test_external_read_permission_does_not_require_confirmation(self):
        from security.confirmation import request_confirmation
        from security.permissions import PermissionLevel
        from unittest.mock import patch

        with patch("builtins.input") as mock_input:
            result = request_confirmation(
                action="Web search",
                description="Search the Internet.",
                permission_level=PermissionLevel.EXTERNAL_READ,
            )

        self.assertTrue(result)
        mock_input.assert_not_called()

    def test_memory_read_permission_does_not_require_confirmation(self):
        from security.confirmation import request_confirmation
        from security.permissions import PermissionLevel
        from unittest.mock import patch

        with patch("builtins.input") as mock_input:
            result = request_confirmation(
                action="Recall memory",
                description="Retrieve stored memories.",
                permission_level=PermissionLevel.MEMORY_READ,
            )

        self.assertTrue(result)
        mock_input.assert_not_called()

    def test_memory_write_permission_requires_confirmation(self):
        from security.confirmation import request_confirmation
        from security.permissions import PermissionLevel
        from unittest.mock import patch

        with patch("builtins.input", return_value="y") as mock_input:
            result = request_confirmation(
                action="Save memory",
                description="Remember this fact.",
                permission_level=PermissionLevel.MEMORY_WRITE,
            )

        self.assertTrue(result)
        mock_input.assert_called_once()

    def test_write_permission_requires_confirmation(self):
        from security.confirmation import request_confirmation
        from security.permissions import PermissionLevel
        from unittest.mock import patch

        with patch("builtins.input", return_value="y") as mock_input:
            result = request_confirmation(
                action="Create customer",
                description="Create a new customer.",
                permission_level=PermissionLevel.WRITE,
            )

        self.assertTrue(result)
        mock_input.assert_called_once()

    def test_destructive_permission_requires_confirmation(self):
        from security.confirmation import request_confirmation
        from security.permissions import PermissionLevel
        from unittest.mock import patch

        with patch("builtins.input", return_value="y") as mock_input:
            result = request_confirmation(
                action="Delete customer",
                description="Delete customer 10.",
                permission_level=PermissionLevel.DESTRUCTIVE,
            )

        self.assertTrue(result)
        mock_input.assert_called_once()

    def test_confirmation_decline_returns_false(self):
        from security.confirmation import request_confirmation
        from security.permissions import PermissionLevel
        from unittest.mock import patch

        with patch("builtins.input", return_value="n"):
            result = request_confirmation(
                action="Delete customer",
                description="Delete customer 10.",
                permission_level=PermissionLevel.DESTRUCTIVE,
            )

        self.assertFalse(result)

if __name__ == "__main__":
    unittest.main()


class TestAtlasExecutorBoundary(unittest.TestCase):
    @patch("agent.atlas.genai.Client")
    def test_deterministic_customer_list_uses_executor_and_records_metrics(
        self,
        mock_client,
    ):
        atlas = Atlas()
        atlas.metrics.reset()

        with patch.object(
            atlas.executor,
            "execute",
            wraps=atlas.executor.execute,
        ) as mock_execute:
            response = atlas.ask("Show all customers")

        mock_execute.assert_called_once_with(
            "get_customers",
            {},
        )

        snapshot = atlas.metrics.snapshot()
        tool_metrics = snapshot["tools"]["get_customers"]

        self.assertEqual(tool_metrics["calls"], 1)
        self.assertEqual(tool_metrics["successes"], 1)
        self.assertEqual(tool_metrics["failures"], 0)

        self.assertIsInstance(response, str)


class TestGeminiToolSelectionGuidance(unittest.TestCase):

    def test_customer_tool_descriptions_distinguish_list_from_lookup(self):
        from agent.registry import GEMINI_TOOLS

        descriptions = {
            declaration.name: declaration.description
            for declaration in GEMINI_TOOLS.function_declarations
        }

        self.assertIn(
            "Do NOT use this tool to find a specific customer",
            descriptions["get_customers"],
        )

        self.assertIn(
            "use find_customer instead",
            descriptions["get_customers"],
        )

        self.assertIn(
            "Do NOT use get_customers for a specific customer",
            descriptions["find_customer"],
        )

    def test_web_search_description_defines_external_information_boundary(self):
        from agent.registry import GEMINI_TOOLS

        descriptions = {
            declaration.name: declaration.description
            for declaration in GEMINI_TOOLS.function_declarations
        }

        self.assertIn(
            "current, recent, or external information",
            descriptions["web_search"],
        )
    @patch("agent.atlas.genai.Client")
    def test_failed_lookup_can_stop_dependent_workflow(
        self,
        mock_client,
    ):
        atlas = Atlas()

        find_call = type(
            "FunctionCall",
            (),
            {
                "name": "find_customer",
                "args": {
                    "name": "John Kamau",
                    "email": None,
                    "city": None,
                },
            },
        )()

        first_response = type(
            "Response",
            (),
            {
                "function_calls": [find_call],
                "text": None,
            },
        )()

        final_response = type(
            "Response",
            (),
            {
                "function_calls": [],
                "text": (
                    "I could not find John Kamau, so I did not "
                    "make the requested change."
                ),
            },
        )()

        atlas.chat.send_message.side_effect = [
            first_response,
            final_response,
        ]

        atlas.executor.execute = unittest.mock.Mock(
            return_value=ToolResult(
                success=False,
                action="find_customer",
                message="Customer lookup failed.",
                data=None,
            )
        )

        atlas.executor.serialize_result = unittest.mock.Mock(
            side_effect=lambda result: {
                "success": result.success,
                "action": result.action,
                "message": result.message,
                "data": result.data,
            }
        )

        response = atlas.handle_gemini(
            "Find John Kamau and change his city to Thika."
        )

        self.assertEqual(
            response,
            "I could not find John Kamau, so I did not "
            "make the requested change.",
        )

        atlas.executor.execute.assert_called_once_with(
            "find_customer",
            {
                "name": "John Kamau",
                "email": None,
                "city": None,
            },
        )

        failed_result = (
            atlas.executor.serialize_result.call_args.args[0]
        )

        self.assertFalse(failed_result.success)

        self.assertEqual(
            failed_result.action,
            "find_customer",
        )

        self.assertEqual(
            failed_result.message,
            "Customer lookup failed.",
        )

        self.assertEqual(
            atlas.chat.send_message.call_count,
            2,
        )
class TestGeminiMemorySelectionGuidance(unittest.TestCase):
    def test_memory_tool_descriptions_define_when_to_use_them(self):
        from agent.registry import GEMINI_TOOLS

        descriptions = {
            declaration.name: declaration.description
            for declaration in GEMINI_TOOLS.function_declarations
        }

        self.assertIn(
            "ONLY when the user explicitly asks Atlas to remember",
            descriptions["remember"],
        )

        self.assertIn(
            "request depends on something that may have been remembered previously",
            descriptions["recall"],
        )

        self.assertIn(
            "NOT use this as a substitute for current database or Internet information",
            descriptions["recall"],
        )

        self.assertIn(
            "ONLY when the user explicitly asks Atlas to forget",
            descriptions["forget"],
        )

    def test_atlas_persona_defines_memory_reasoning_boundary(self):
        from config.personas import ATLAS

        instructions = ATLAS.build_system_instruction()

        self.assertIn(
            "Use persistent memory when the user's request depends on",
            instructions,
        )
        self.assertIn(
            "Use recall to retrieve previously stored facts",
            instructions,
        )
        self.assertIn(
            "Use remember only when the user explicitly asks",
            instructions,
        )
        self.assertIn(
            "Use forget only when the user explicitly asks",
            instructions,
        )
        self.assertIn(
    "Do not use persistent memory as a substitute for",
    instructions,
)