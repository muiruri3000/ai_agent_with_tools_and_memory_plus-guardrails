from agent.tools import (
    get_customers,
    find_customer,
    get_customer_by_id,
    update_customer,
    delete_customer,
)
from agent.executor import ToolExecutor
from agent.results import ToolResult
from google import genai
from google.genai import types
import re

from config.settings import (
    GEMINI_API_KEY,
    MODEL_NAME,
)

from config.personas import ATLAS

from agent.registry import GEMINI_TOOLS

from agent.router import (
    route_request,
    extract_customer_query,
    extract_customer_update,
)


class Atlas:

    MAX_TOOL_ITERATIONS = 5

    def __init__(self, persona=ATLAS):
        self.persona = persona
        self.context = {
            "customer": None,
        }
        self.client = genai.Client(api_key=GEMINI_API_KEY)

        self.executor = ToolExecutor()

        self.chat = self.client.chats.create(
            model=MODEL_NAME,
            config=types.GenerateContentConfig(
                system_instruction=self.persona.build_system_instruction(),
                tools=[GEMINI_TOOLS],
                automatic_function_calling=types.AutomaticFunctionCallingConfig(
                    disable=True
                ),
            ),
        )

    def handle_customer_context(self, message: str) -> str | None:
        """
        Handle follow-up questions about the currently
        selected customer.

        Returns:
            A response string if the message can be handled
            using customer context, otherwise None.
        """

        customer = self.context.get("customer")

        if not customer:
            return None

        text = message.lower().strip()

        # ---------------------------------------------
        # EMAIL
        # ---------------------------------------------

        if (
            "his email" in text
            or "her email" in text
            or "their email" in text
            or "email" in text
            and ("what" in text or "what's" in text or "tell me" in text)
        ):
            return f"{customer['name']}'s email is " f"{customer['email']}."

        # ---------------------------------------------
        # CITY
        # ---------------------------------------------

        if (
            "his city" in text
            or "her city" in text
            or "their city" in text
            or "where does" in text
            or "where do" in text
        ):
            return f"{customer['name']} lives in " f"{customer['city']}."

        # ---------------------------------------------
        # NAME
        # ---------------------------------------------

        if "his name" in text or "her name" in text or "their name" in text:
            return f"The customer's name is " f"{customer['name']}."

        return None

    def set_customer_context(self, customer: dict) -> None:
        """
        Store a verified customer as the current
        conversational customer.
        """

        self.context["customer"] = {
            "id": customer["id"],
            "name": customer["name"],
            "email": customer["email"],
            "city": customer["city"],
        }

        print(f"🧠 CONTEXT: customer = " f"{customer['id']} / {customer['name']}")

    def handle_context_update(self, message: str) -> str | None:
        """
        Handle customer update requests that refer to the
        currently selected customer using pronouns such as
        'his', 'her', or 'their'.

        Returns:
            A response string if the request can be handled
            using customer context, otherwise None.
        """

        customer = self.context.get("customer")

        if not customer:
            return None

        text = message.lower().strip()

        # ---------------------------------------------
        # DETECT PRONOUN-BASED UPDATE
        # ---------------------------------------------

        pronouns = (
            "his ",
            "her ",
            "their ",
        )

        has_pronoun = any(pronoun in text for pronoun in pronouns)

        update_words = (
            "change",
            "update",
            "edit",
            "modify",
        )

        has_update_word = any(word in text for word in update_words)

        if not has_pronoun or not has_update_word:
            return None

        # ---------------------------------------------
        # DETERMINE FIELD
        # ---------------------------------------------

        field = None

        if "city" in text:
            field = "city"

        elif "email" in text:
            field = "email"

        elif "name" in text:
            field = "name"

        if not field:
            return None

        # ---------------------------------------------
        # EXTRACT NEW VALUE
        # ---------------------------------------------

        match = re.search(
            rf"\b{field}\s+(?:to|into)\s+(.+?)(?:\?|$)",
            message,
            re.IGNORECASE,
        )

        if not match:
            return None

        new_value = match.group(1).strip()
        new_value = new_value.rstrip("?.!, ")

        if not new_value:
            return None

        # ---------------------------------------------
        # CHECK WHETHER CHANGE IS NECESSARY
        # ---------------------------------------------

        current_value = customer[field]

        if str(current_value).strip().lower() == str(new_value).strip().lower():
            return (
                f"{customer['name']}'s {field} is already "
                f"set to {current_value}. No update was "
                "necessary."
            )

        # ---------------------------------------------
        # PREPARE UPDATE
        # ---------------------------------------------

        name = None
        email = None
        city = None

        if field == "name":
            name = new_value

        elif field == "email":
            email = new_value

        elif field == "city":
            city = new_value

        # ---------------------------------------------
        # REQUEST CONFIRMATION + UPDATE
        # ---------------------------------------------

        result = update_customer(
            customer_id=customer["id"],
            name=name,
            email=email,
            city=city,
        )

        # ---------------------------------------------
        # HANDLE RESULT
        # ---------------------------------------------

        if not result.success:
            return result.message

        # ---------------------------------------------
        # UPDATE CONTEXT
        # ---------------------------------------------

        updated_customer = result.data

        self.set_customer_context(updated_customer)

        return (
            f"{updated_customer['name']}'s "
            f"{field} has been successfully updated "
            f"to {updated_customer[field]}."
        )

    def clear_customer_context(self) -> None:
        """
        Clear the currently selected customer.
        """

        self.context["customer"] = None

        print("🧠 CONTEXT: customer cleared")

    def handle_customer_lookup(self, message: str) -> str:
        """
        Handle deterministic customer lookup requests.
        """

        query = extract_customer_query(message)

        if not any(query.values()):
            return (
                "I understood this as a customer lookup, "
                "but I could not determine which customer "
                "you are referring to."
            )

        result = find_customer(
            name=query["name"],
            email=query["email"],
            city=query["city"],
        )

        if not result.success:
            return result.message

        results = result.data

        if not results:
            return "I could not find a matching customer."

        if len(results) == 1:

            customer = results[0]

            self.set_customer_context(customer)

            return (
                "**Customer Details:**\n\n"
                f"- **ID:** {customer['id']}\n"
                f"- **Name:** {customer['name']}\n"
                f"- **Email:** {customer['email']}\n"
                f"- **City:** {customer['city']}"
            )

        response = f"I found {len(results)} matching customers:\n\n"

        for customer in results:
            response += (
                f"- **ID:** {customer['id']} — "
                f"{customer['name']} — "
                f"{customer['email']} — "
                f"{customer['city']}\n"
            )

        return response

    def handle_customer_update(self, message: str) -> str:
        """
        Handle deterministic customer update requests.
        """

        update = extract_customer_update(message)

        # ---------------------------------------------
        # VALIDATE CUSTOMER
        # ---------------------------------------------

        if not update["name"] and update["customer_id"] is None:
            return (
                "I understood this as a customer update, "
                "but I could not determine which customer "
                "you are referring to."
            )

        # ---------------------------------------------
        # VALIDATE FIELD
        # ---------------------------------------------

        if not update["field"]:
            return (
                "I understood which customer you mean, "
                "but I could not determine which field "
                "you want to update."
            )

        # ---------------------------------------------
        # VALIDATE VALUE
        # ---------------------------------------------

        if not update["value"]:
            return (
                "I understood which field you want to "
                "update, but I could not determine the "
                "new value."
            )

        # ---------------------------------------------
        # IDENTIFY CUSTOMER
        # ---------------------------------------------

        customer = None

        # ---------------------------------------------
        # ID-BASED CUSTOMER LOOKUP
        # ---------------------------------------------

        if update["customer_id"] is not None:

            result = get_customer_by_id(update["customer_id"])

            if not result.success:
                return result.message

            customer = result.data

        # ---------------------------------------------
        # NAME-BASED CUSTOMER LOOKUP
        # ---------------------------------------------

        else:

            result = find_customer(name=update["name"])

            if not result.success:
                return result.message

            results = result.data

            if not results:
                return "I could not find the customer " f"'{update['name']}'."

            # -----------------------------------------
            # HANDLE AMBIGUOUS CUSTOMER
            # -----------------------------------------

            if len(results) > 1:

                response = (
                    f"I found {len(results)} customers "
                    f"matching '{update['name']}':\n\n"
                )

                for result_customer in results:
                    response += (
                        f"- **ID:** "
                        f"{result_customer['id']} — "
                        f"{result_customer['name']} — "
                        f"{result_customer['email']} — "
                        f"{result_customer['city']}\n"
                    )

                response += (
                    "\nPlease specify the customer "
                    "more precisely before I make "
                    "the update."
                )

                return response

            customer = results[0]

        # ---------------------------------------------
        # IDENTIFY UPDATE
        # ---------------------------------------------

        field = update["field"]
        new_value = update["value"]

        # ---------------------------------------------
        # VALIDATE FIELD
        # ---------------------------------------------

        if field not in {
            "name",
            "email",
            "city",
        }:
            return f"I cannot update the '{field}' field."

        # ---------------------------------------------
        # GET CURRENT VALUE
        # ---------------------------------------------

        current_value = customer[field]

        # ---------------------------------------------
        # CHECK WHETHER CHANGE IS NECESSARY
        # ---------------------------------------------

        if str(current_value).strip().lower() == str(new_value).strip().lower():
            return (
                f"{customer['name']}'s {field} is already "
                f"set to {current_value}. No update was "
                "necessary."
            )

        # ---------------------------------------------
        # PREPARE UPDATE
        # ---------------------------------------------

        name = None
        email = None
        city = None

        if field == "name":
            name = new_value

        elif field == "email":
            email = new_value

        elif field == "city":
            city = new_value

        # ---------------------------------------------
        # PERFORM UPDATE
        # ---------------------------------------------

        result = update_customer(
            customer_id=customer["id"],
            name=name,
            email=email,
            city=city,
        )

        # ---------------------------------------------
        # HANDLE UPDATE RESULT
        # ---------------------------------------------

        if not result.success:
            return result.message

        updated_customer = result.data

        self.set_customer_context(updated_customer)

        return (
            f"{updated_customer['name']}'s "
            f"{field} has been successfully updated "
            f"to {updated_customer[field]}."
        )

    def handle_customer_delete(self, message: str) -> str:
        """
        Handle deterministic customer deletion requests.
        """

        query = extract_customer_query(message)

        if not any(query.values()):
            return (
                "I understood this as a customer deletion, "
                "but I could not determine which customer "
                "you are referring to."
            )

        result = find_customer(
            name=query["name"],
            email=query["email"],
            city=query["city"],
        )

        if not result.success:
            return result.message

        results = result.data

        if not results:

            identifier = (
                query["name"]
                or query["email"]
                or query["city"]
                or "the specified customer"
            )

            return "I could not find a customer matching " f"'{identifier}'."

        # ---------------------------------------------
        # HANDLE AMBIGUOUS CUSTOMER
        # ---------------------------------------------

        if len(results) > 1:

            identifier = (
                query["name"] or query["email"] or query["city"] or "your request"
            )

            response = "I found multiple customers matching " f"'{identifier}':\n\n"

            for customer in results:
                response += (
                    f"- **ID:** {customer['id']} — "
                    f"{customer['name']} — "
                    f"{customer['email']} — "
                    f"{customer['city']}\n"
                )

            response += "\nPlease specify which customer " "you want to delete."

            return response

            # ---------------------------------------------
        # DELETE CUSTOMER
        # ---------------------------------------------

        customer = results[0]

        result = delete_customer(customer_id=customer["id"])

        # ---------------------------------------------
        # HANDLE DELETE RESULT
        # ---------------------------------------------

        if not result.success:
            return result.message

        deleted = result.data

        # ---------------------------------------------
        # CLEAR CONTEXT IF CURRENT CUSTOMER
        # ---------------------------------------------

        current_customer = self.context.get("customer")

        if current_customer and current_customer["id"] == deleted["id"]:
            self.clear_customer_context()

        return f"{deleted['name']} has been successfully " "deleted from the database."

    def handle_customer_list(self) -> str:
        """
        Handle deterministic customer list requests.
        """

        result = get_customers()

        if not result.success:
            return result.message

        results = result.data

        if not results:
            return "There are no customers in the database."

        response = "Here are the customers in the database:\n\n"

        for customer in results:
            response += (
                f"- **ID {customer['id']}:** "
                f"{customer['name']} — "
                f"{customer['email']} — "
                f"{customer['city']}\n"
            )

        return response

    def handle_gemini(self, message: str) -> str:
        """
        Handle requests that require Gemini reasoning and tools.

        Tool failures are converted into structured ToolResults
        and returned to Gemini so the model can decide whether
        to recover, retry, use another tool, or explain the
        limitation to the user.
        """

        response = self.chat.send_message(message)

        tool_iterations = 0

        while response.function_calls:
            tool_iterations += 1

            if tool_iterations > self.MAX_TOOL_ITERATIONS:
                return (
                    "I stopped the tool execution because the maximum "
                    "number of tool iterations was reached."
                )

            print(f"\n🧠 AGENT ITERATION: {tool_iterations}")

            function_responses = []

            for function_call in response.function_calls:

                try:
                    result = self.executor.execute(
                        function_call.name,
                        dict(function_call.args),
                    )

                except Exception as exc:
                    print(
                        f"❌ TOOL ERROR: {function_call.name}: {exc}"
                    )

                    result = ToolResult(
                        success=False,
                        action=function_call.name,
                        message=(
                            f"Tool execution failed: {exc}"
                        ),
                        data=None,
                    )

                serialized_result = self.executor.serialize_result(
                    result
                )

                function_responses.append(
                    types.Part.from_function_response(
                        name=function_call.name,
                        response=serialized_result,
                    )
                )

            response = self.chat.send_message(function_responses)

        return response.text

    def ask(self, message: str) -> str:
        """
        Main Atlas request coordinator.

        This method determines which part of the
        system should handle the user's request.
        """

        # ---------------------------------------------
        # CONTEXT-AWARE CUSTOMER UPDATE
        # ---------------------------------------------

        context_update_response = self.handle_context_update(message)

        if context_update_response:
            return context_update_response

        # ---------------------------------------------
        # CONVERSATIONAL CONTEXT
        # ---------------------------------------------

        context_response = self.handle_customer_context(message)

        if context_response:
            return context_response

        # ---------------------------------------------
        # DETERMINE ROUTE
        # ---------------------------------------------

        route = route_request(message)

        # ---------------------------------------------
        # CUSTOMER OPERATIONS
        # ---------------------------------------------

        if route == "find_customer":
            return self.handle_customer_lookup(message)

        if route == "update_customer":
            return self.handle_customer_update(message)

        if route == "delete_customer":
            return self.handle_customer_delete(message)

        if route == "get_customers":
            return self.handle_customer_list()

        # ---------------------------------------------
        # EVERYTHING ELSE → GEMINI
        # ---------------------------------------------

        return self.handle_gemini(message)
