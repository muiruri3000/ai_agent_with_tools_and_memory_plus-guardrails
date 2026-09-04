from google.genai import types

from agent.tools import (
    get_customers,
    web_search,
    remember,
    recall,
    forget,
    create_customer,
    update_customer,
    delete_customer,
)

# Python functions used by the Atlas executor.
TOOLS = [
    get_customers,
    web_search,
    remember,
    recall,
    forget,
    create_customer,
    update_customer,
    delete_customer,
]


# Explicit Gemini function declarations.
#
# These are deliberately separate from the Python functions.
# Gemini sees these schemas; Atlas executes the actual functions.
GEMINI_TOOLS = types.Tool(
    function_declarations=[
        types.FunctionDeclaration(
            name="get_customers",
            description="Retrieve the complete list of customers from the database.",
            parameters_json_schema={
                "type": "object",
                "properties": {},
            },
        ),
        types.FunctionDeclaration(
            name="web_search",
            description="Search the Internet for current or external information.",
            parameters_json_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query.",
                    }
                },
                "required": ["query"],
            },
        ),
        types.FunctionDeclaration(
            name="remember",
            description="Store a fact in Atlas's persistent memory.",
            parameters_json_schema={
                "type": "object",
                "properties": {
                    "fact": {
                        "type": "string",
                        "description": "The fact to remember.",
                    }
                },
                "required": ["fact"],
            },
        ),
        types.FunctionDeclaration(
            name="recall",
            description="Retrieve facts stored in Atlas's persistent memory.",
            parameters_json_schema={
                "type": "object",
                "properties": {},
            },
        ),
        types.FunctionDeclaration(
            name="forget",
            description="Remove a fact from Atlas's persistent memory.",
            parameters_json_schema={
                "type": "object",
                "properties": {
                    "fact": {
                        "type": "string",
                        "description": "The fact to forget.",
                    }
                },
                "required": ["fact"],
            },
        ),
        types.FunctionDeclaration(
            name="create_customer",
            description="Create a new customer in the database.",
            parameters_json_schema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Customer's full name.",
                    },
                    "email": {
                        "type": "string",
                        "description": "Customer's email address.",
                    },
                    "city": {
                        "type": "string",
                        "description": "Customer's city.",
                    },
                },
                "required": ["name", "email", "city"],
            },
        ),
        types.FunctionDeclaration(
            name="update_customer",
            description="Update an existing customer's information.",
            parameters_json_schema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "integer",
                        "description": "Customer ID.",
                    },
                    "name": {
                        "type": "string",
                        "description": "New customer name.",
                    },
                    "email": {
                        "type": "string",
                        "description": "New customer email.",
                    },
                    "city": {
                        "type": "string",
                        "description": "New customer city.",
                    },
                },
                "required": ["customer_id"],
            },
        ),
        types.FunctionDeclaration(
            name="delete_customer",
            description="Delete a customer from the database after confirmation.",
            parameters_json_schema={
                "type": "object",
                "properties": {
                    "customer_id": {
                        "type": "integer",
                        "description": "Customer ID.",
                    }
                },
                "required": ["customer_id"],
            },
        ),
    ]
)
