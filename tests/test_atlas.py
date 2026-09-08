import unittest
from unittest.mock import patch

from agent.atlas import Atlas
from agent.results import ToolResult


class TestAtlasCustomerLookup(unittest.TestCase):

    @patch("agent.atlas.find_customer")
    @patch("agent.atlas.genai.Client")
    def test_find_customer_establishes_context(
        self,
        mock_client,
        mock_find_customer,
    ):

        customer = {
            "id": 3,
            "name": "David",
            "email": "david@example.com",
            "city": "Thika",
        }

        mock_find_customer.return_value = ToolResult(
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

        mock_find_customer.assert_called_once_with(
            name="David",
            email=None,
            city=None,
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

    @patch("agent.atlas.delete_customer")
    @patch("agent.atlas.find_customer")
    @patch("agent.atlas.genai.Client")
    def test_successful_delete_clears_context(
        self,
        mock_client,
        mock_find_customer,
        mock_delete_customer,
    ):

        customer = {
            "id": 3,
            "name": "David",
            "email": "david@example.com",
            "city": "Thika",
        }

        mock_find_customer.return_value = ToolResult(
            success=True,
            action="find_customer",
            message="Found 1 matching customer(s).",
            data=[customer],
        )

        mock_delete_customer.return_value = ToolResult(
            success=True,
            action="delete_customer",
            message="Customer deleted successfully.",
            data=customer,
        )

        atlas = Atlas()

        # Establish context first.
        atlas.ask("Find David")

        self.assertIsNotNone(atlas.context["customer"])

        # Delete customer.
        response = atlas.ask("Delete David")

        self.assertIn(
            "David has been successfully deleted",
            response,
        )

        mock_delete_customer.assert_called_once_with(
            customer_id=3,
        )

        self.assertIsNone(atlas.context["customer"])


class TestAtlasCustomerUpdate(unittest.TestCase):

    @patch("agent.atlas.update_customer")
    @patch("agent.atlas.find_customer")
    @patch("agent.atlas.genai.Client")
    def test_successful_update_refreshes_context(
        self,
        mock_client,
        mock_find_customer,
        mock_update_customer,
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

        mock_find_customer.return_value = ToolResult(
            success=True,
            action="find_customer",
            message="Found 1 matching customer(s).",
            data=[customer],
        )

        mock_update_customer.return_value = ToolResult(
            success=True,
            action="update_customer",
            message="Customer updated successfully.",
            data=updated_customer,
        )

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

    @patch("agent.atlas.update_customer")
    @patch("agent.atlas.find_customer")
    @patch("agent.atlas.genai.Client")
    def test_name_based_update_refreshes_context(
        self,
        mock_client,
        mock_find_customer,
        mock_update_customer,
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

        mock_find_customer.return_value = ToolResult(
            success=True,
            action="find_customer",
            message="Found 1 matching customer(s).",
            data=[customer],
        )

        mock_update_customer.return_value = ToolResult(
            success=True,
            action="update_customer",
            message="Customer updated successfully.",
            data=updated_customer,
        )

        atlas = Atlas()

        atlas.ask("Find John Kamau")

        response = atlas.ask("Change John Kamau's name to John Mwangi")

        self.assertIn(
            "successfully updated",
            response,
        )

        mock_update_customer.assert_called_once_with(
            customer_id=4,
            name="John Mwangi",
            email=None,
            city=None,
        )

        self.assertEqual(
            atlas.context["customer"],
            updated_customer,
        )

    @patch("agent.atlas.update_customer")
    @patch("agent.atlas.get_customer_by_id")
    @patch("agent.atlas.genai.Client")
    def test_id_based_update_refreshes_context(
        self,
        mock_client,
        mock_get_customer_by_id,
        mock_update_customer,
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

        mock_get_customer_by_id.return_value = ToolResult(
            success=True,
            action="get_customer_by_id",
            message="Customer retrieved successfully.",
            data=customer,
        )

        mock_update_customer.return_value = ToolResult(
            success=True,
            action="update_customer",
            message="Customer updated successfully.",
            data=updated_customer,
        )

        atlas = Atlas()

        response = atlas.ask("Change customer ID 4's city to Embu")

        self.assertIn(
            "successfully updated",
            response,
        )

        mock_get_customer_by_id.assert_called_once_with(4)

        mock_update_customer.assert_called_once_with(
            customer_id=4,
            name=None,
            email=None,
            city="Embu",
        )

        self.assertEqual(
            atlas.context["customer"],
            updated_customer,
        )

    @patch("agent.atlas.update_customer")
    @patch("agent.atlas.find_customer")
    @patch("agent.atlas.genai.Client")
    def test_ambiguous_update_does_not_change_context(
        self,
        mock_client,
        mock_find_customer,
        mock_update_customer,
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

        mock_find_customer.return_value = ToolResult(
            success=True,
            action="find_customer",
            message="Found 2 matching customer(s).",
            data=[
                john_one,
                john_two,
            ],
        )

        response = atlas.ask("Change John city's city to Embu")

        self.assertIn(
            "2 customers matching",
            response.lower(),
        )

        mock_update_customer.assert_not_called()

        self.assertEqual(
            atlas.context["customer"],
            david,
        )

    @patch("agent.atlas.update_customer")
    @patch("agent.atlas.find_customer")
    @patch("agent.atlas.genai.Client")
    def test_failed_update_preserves_context(
        self,
        mock_client,
        mock_find_customer,
        mock_update_customer,
    ):

        customer = {
            "id": 4,
            "name": "John Kamau",
            "email": "john@example.com",
            "city": "Nairobi",
        }

        atlas = Atlas()

        atlas.context["customer"] = customer

        mock_find_customer.return_value = ToolResult(
            success=True,
            action="find_customer",
            message="Found 1 matching customer(s).",
            data=[customer],
        )

        mock_update_customer.return_value = ToolResult(
            success=False,
            action="update_customer",
            message="Update failed.",
            data=None,
        )

        response = atlas.ask("Change John Kamau's city to Embu")

        self.assertIn(
            "update failed",
            response.lower(),
        )

        self.assertEqual(
            atlas.context["customer"],
            customer,
        )


class TestAtlasLookupSafety(unittest.TestCase):

    @patch("agent.atlas.find_customer")
    @patch("agent.atlas.genai.Client")
    def test_ambiguous_lookup_does_not_establish_context(
        self,
        mock_client,
        mock_find_customer,
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

        mock_find_customer.return_value = ToolResult(
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

        self.assertIsNone(atlas.context["customer"])

    @patch("agent.atlas.find_customer")
    @patch("agent.atlas.genai.Client")
    def test_failed_lookup_does_not_establish_context(
        self,
        mock_client,
        mock_find_customer,
    ):

        mock_find_customer.return_value = ToolResult(
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

        self.assertIsNone(atlas.context["customer"])


class TestAtlasDeleteSafety(unittest.TestCase):

    @patch("agent.atlas.delete_customer")
    @patch("agent.atlas.find_customer")
    @patch("agent.atlas.genai.Client")
    def test_failed_delete_preserves_context(
        self,
        mock_client,
        mock_find_customer,
        mock_delete_customer,
    ):

        customer = {
            "id": 3,
            "name": "David",
            "email": "david@example.com",
            "city": "Thika",
        }

        mock_find_customer.return_value = ToolResult(
            success=True,
            action="find_customer",
            message="Found 1 matching customer(s).",
            data=[customer],
        )

        mock_delete_customer.return_value = ToolResult(
            success=False,
            action="delete_customer",
            message="User declined customer deletion.",
            data=None,
        )

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


if __name__ == "__main__":
    unittest.main()


class TestAtlasAgenticLoop(unittest.TestCase):

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


if __name__ == "__main__":
    unittest.main()


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


if __name__ == "__main__":
    unittest.main()


class TestToolAuthorization(unittest.TestCase):

    def test_all_registered_tools_have_authorization_policy(self):
        from agent.executor import ToolExecutor

        executor = ToolExecutor()

        for tool_name in executor.tools:
            self.assertIn(
                tool_name,
                executor.TOOL_LEVELS,
            )

    def test_read_tool_is_authorized(self):
        from agent.executor import ToolExecutor

        executor = ToolExecutor()

        self.assertEqual(
            executor.get_tool_level("get_customers"),
            "READ",
        )

        self.assertTrue(
            executor.authorize("get_customers")
        )

    def test_external_read_tool_is_authorized(self):
        from agent.executor import ToolExecutor

        executor = ToolExecutor()

        self.assertEqual(
            executor.get_tool_level("web_search"),
            "EXTERNAL_READ",
        )

        self.assertTrue(
            executor.authorize("web_search")
        )

    def test_memory_read_tool_is_authorized(self):
        from agent.executor import ToolExecutor

        executor = ToolExecutor()

        self.assertEqual(
            executor.get_tool_level("recall"),
            "MEMORY_READ",
        )

        self.assertTrue(
            executor.authorize("recall")
        )

    def test_memory_write_tool_has_correct_level(self):
        from agent.executor import ToolExecutor

        executor = ToolExecutor()

        self.assertEqual(
            executor.get_tool_level("remember"),
            "MEMORY_WRITE",
        )

        self.assertTrue(
            executor.authorize("remember")
        )

    def test_customer_write_tools_have_write_level(self):
        from agent.executor import ToolExecutor

        executor = ToolExecutor()

        self.assertEqual(
            executor.get_tool_level("create_customer"),
            "WRITE",
        )

        self.assertEqual(
            executor.get_tool_level("update_customer"),
            "WRITE",
        )

        self.assertTrue(
            executor.authorize("create_customer")
        )

        self.assertTrue(
            executor.authorize("update_customer")
        )

    def test_delete_customer_has_destructive_level(self):
        from agent.executor import ToolExecutor

        executor = ToolExecutor()

        self.assertEqual(
            executor.get_tool_level("delete_customer"),
            "DESTRUCTIVE",
        )

        self.assertTrue(
            executor.authorize("delete_customer")
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


if __name__ == "__main__":
    unittest.main()
