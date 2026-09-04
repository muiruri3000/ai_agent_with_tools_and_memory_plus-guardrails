from database.db import (
    get_customers as db_get_customers,
    get_customer_by_id as db_get_customer_by_id,
    create_customer as db_create_customer,
    find_customer as db_find_customer,
    update_customer as db_update_customer,
    delete_customer as db_delete_customer,
)
from tools.web import web_search as perform_web_search
from security.confirmation import request_confirmation
from memory.memory import (
    remember as store_memory,
    recall as get_memories,
    forget as delete_memory,
)


def get_customers() -> list:
    """
    Return the complete list of all customers.

    IMPORTANT:
    Use this tool ONLY when the user explicitly asks for:
    - all customers
    - a list of customers
    - the complete customer list
    - every customer

    Do NOT use this tool to find a specific customer.
    For a specific customer, use find_customer instead.
    """

    print("\n🔧 TOOL CALLED: get_customers()")

    results = db_get_customers()

    print(f"🔧 DATABASE RESULT: {len(results)} customers")

    return results


def find_customer(
    name: str = None,
    email: str = None,
    city: str = None,
) -> list:
    """
    Search for specific customers.

    Use this tool when the user wants to:
    - find a customer
    - identify a customer
    - look up a customer
    - ask for a customer's details
    - find customers by name
    - find customers by email
    - find customers by city

    Do NOT use get_customers for these requests.
    """

    print("\n🔎 TOOL CALLED: find_customer()")

    if name:
        print(f"🔎 NAME: {name}")

    if email:
        print(f"🔎 EMAIL: {email}")

    if city:
        print(f"🔎 CITY: {city}")

    results = db_find_customer(
        name=name,
        email=email,
        city=city,
    )

    print(f"🔎 MATCHES FOUND: {len(results)}")

    return results


def web_search(query: str) -> list:
    """
    Search the Internet for current or external information.

    Args:
        query: Search query.

    Returns:
        Search results.
    """

    print("\n🌐 TOOL CALLED: web_search()")
    print(f"🌐 QUERY: {query}")

    results = perform_web_search(query)

    print(f"🌐 RESULTS: {len(results)}")

    return results


def remember(fact: str) -> dict:
    """
    Store an important fact in persistent memory.
    """

    print("\n🧠 TOOL CALLED: remember()")

    approved = request_confirmation(
        action="Save memory",
        description=(f"Atlas wants to remember: {fact}"),
    )

    if not approved:

        print("🧠 MEMORY NOT SAVED")

        return {
            "success": False,
            "action": "remember",
            "message": ("User declined the memory request."),
            "fact": fact,
        }

    print(f"🧠 MEMORY: {fact}")

    result = store_memory(fact)

    print("🧠 MEMORY SAVED")

    return {
        "success": True,
        "action": "remember",
        "message": result,
        "fact": fact,
    }


def recall() -> list:
    """
    Retrieve persistent memories.
    """

    print("\n🧠 TOOL CALLED: recall()")

    memories = get_memories()

    print(f"🧠 MEMORIES FOUND: {len(memories)}")

    return memories


def forget(fact: str) -> dict:
    """
    Remove a specific fact from persistent memory.
    """

    print("\n🧠 TOOL CALLED: forget()")

    approved = request_confirmation(
        action="Delete memory",
        description=(f"Atlas wants to forget: {fact}"),
    )

    if not approved:

        print("🧠 MEMORY NOT DELETED")

        return {
            "success": False,
            "action": "forget",
            "message": ("User declined the memory deletion."),
            "fact": fact,
        }

    print(f"🧠 MEMORY TO REMOVE: {fact}")

    result = delete_memory(fact)

    print("🧠 MEMORY DELETED")

    return {
        "success": True,
        "action": "forget",
        "message": result,
        "fact": fact,
    }


def create_customer(
    name: str,
    email: str,
    city: str,
) -> dict:
    """
    Create a new customer in the database.

    This is a WRITE operation and requires
    explicit user confirmation.
    """

    print("\n📝 TOOL CALLED: create_customer()")

    # ---------------------------------------------
    # CONFIRMATION
    # ---------------------------------------------

    approved = request_confirmation(
        action="Create customer",
        description=(f"Name: {name}\n" f"Email: {email}\n" f"City: {city}"),
    )

    if not approved:

        print("📝 CUSTOMER NOT CREATED")

        return {
            "success": False,
            "action": "create_customer",
            "message": "User declined customer creation.",
            "data": None,
        }

    # ---------------------------------------------
    # DATABASE CREATE
    # ---------------------------------------------

    try:

        result = db_create_customer(
            name=name,
            email=email,
            city=city,
        )

        # -----------------------------------------
        # DATABASE REPORTED FAILURE
        # -----------------------------------------

        if not result["success"]:

            existing = result.get("data")

            if existing:

                print("⚠️ CUSTOMER NOT CREATED: " f"{result['message']}")

                return {
                    "success": False,
                    "action": "create_customer",
                    "message": result["message"],
                    "data": existing,
                }

            print("❌ CUSTOMER CREATION FAILED: " f"{result['message']}")

            return {
                "success": False,
                "action": "create_customer",
                "message": result["message"],
                "data": None,
            }

        # -----------------------------------------
        # SUCCESS
        # -----------------------------------------

        customer = result["data"]

        print("📝 CUSTOMER CREATED: " f"{customer['id']}")

        return {
            "success": True,
            "action": "create_customer",
            "message": result["message"],
            "data": customer,
        }

    except Exception as e:

        print("❌ CUSTOMER CREATION FAILED: " f"{e}")

        return {
            "success": False,
            "action": "create_customer",
            "message": "Customer creation failed.",
            "data": None,
        }


def update_customer(
    customer_id: int,
    name: str = None,
    email: str = None,
    city: str = None,
) -> dict:
    """
    Update an existing customer.

    This is a WRITE operation and requires
    explicit user confirmation.

    The current customer record is retrieved
    before confirmation so the user can see
    the exact before-and-after change.
    """

    print("\n📝 TOOL CALLED: update_customer()")

    # ---------------------------------------------
    # GET CURRENT CUSTOMER
    # ---------------------------------------------

    try:

        current_customer = db_get_customer_by_id(customer_id)

    except Exception as e:

        print(f"❌ FAILED TO READ CUSTOMER: {e}")

        return {
            "success": False,
            "action": "update_customer",
            "message": ("Could not retrieve the current " "customer record."),
            "data": None,
        }

    if not current_customer:

        print(f"❌ CUSTOMER NOT FOUND: {customer_id}")

        return {
            "success": False,
            "action": "update_customer",
            "message": "Customer not found.",
            "data": None,
        }

    # ---------------------------------------------
    # DETERMINE CHANGED FIELD
    # ---------------------------------------------

    changes = []

    if name is not None:

        changes.append(
            (
                "Name",
                current_customer["name"],
                name,
            )
        )

    if email is not None:

        changes.append(
            (
                "Email",
                current_customer["email"],
                email,
            )
        )

    if city is not None:

        changes.append(
            (
                "City",
                current_customer["city"],
                city,
            )
        )

    if not changes:

        print("❌ NO CUSTOMER CHANGES PROVIDED")

        return {
            "success": False,
            "action": "update_customer",
            "message": ("No changes were provided."),
            "data": current_customer,
        }

    # ---------------------------------------------
    # BUILD BEFORE / AFTER CONFIRMATION
    # ---------------------------------------------

    description_lines = [
        f"Customer: {current_customer['name']}",
        f"Customer ID: {current_customer['id']}",
        "",
    ]

    for field, old_value, new_value in changes:

        description_lines.extend(
            [
                f"Field: {field}",
                f"Current value: {old_value}",
                f"New value: {new_value}",
            ]
        )

    description = "\n".join(description_lines)

    # ---------------------------------------------
    # CONFIRMATION
    # ---------------------------------------------

    approved = request_confirmation(
        action="Update customer",
        description=description,
    )

    if not approved:

        print("📝 CUSTOMER UPDATE NOT PERFORMED")

        return {
            "success": False,
            "action": "update_customer",
            "message": ("User declined customer update."),
            "data": None,
        }

    # ---------------------------------------------
    # DATABASE UPDATE
    # ---------------------------------------------

    try:

        result = db_update_customer(
            customer_id=customer_id,
            name=name,
            email=email,
            city=city,
        )

        if not result["success"]:

            print(f"❌ CUSTOMER UPDATE FAILED: " f"{result['message']}")

            return {
                "success": False,
                "action": "update_customer",
                "message": result["message"],
                "data": None,
            }

        customer = result["data"]

        print(f"📝 CUSTOMER UPDATED: " f"{customer['id']}")

        return {
            "success": True,
            "action": "update_customer",
            "message": ("Customer updated successfully."),
            "data": customer,
        }

    except Exception as e:

        print(f"❌ CUSTOMER UPDATE FAILED: {e}")

        return {
            "success": False,
            "action": "update_customer",
            "message": ("Customer update failed."),
            "data": None,
        }


def get_customer_by_id(customer_id: int) -> dict | None:
    """
    Retrieve a single customer by ID.

    This is a read-only operation.
    """

    print("\n🔎 TOOL CALLED: get_customer_by_id()")
    print(f"🔎 CUSTOMER ID: {customer_id}")

    customer = db_get_customer_by_id(customer_id)

    if not customer:
        print(f"🔎 CUSTOMER NOT FOUND: {customer_id}")
        return None

    print(f"🔎 CUSTOMER FOUND: {customer['name']}")

    return customer


def delete_customer(customer_id: int) -> dict:
    """
    Delete an existing customer.

    This is a destructive database operation and always
    requires explicit user confirmation.
    """

    print("\n🗑️ TOOL CALLED: delete_customer()")

    # ---------------------------------------------
    # FIND CUSTOMER
    # ---------------------------------------------

    customers = db_find_customer()

    # We cannot use the generic find_customer() here
    # because it requires a search parameter.
    #
    # Instead, retrieve the customer directly through
    # the database layer.

    from database.db import get_customer_by_id

    customer = get_customer_by_id(customer_id)

    if not customer:

        print(f"❌ CUSTOMER NOT FOUND: {customer_id}")

        return {
            "success": False,
            "action": "delete_customer",
            "message": "Customer not found.",
            "data": None,
        }

    # ---------------------------------------------
    # CONFIRMATION
    # ---------------------------------------------

    approved = request_confirmation(
        action="Delete customer",
        description=(
            f"Customer ID: {customer['id']}\n"
            f"Name: {customer['name']}\n"
            f"Email: {customer['email']}\n"
            f"City: {customer['city']}"
        ),
    )

    if not approved:

        print("🗑️ CUSTOMER NOT DELETED")

        return {
            "success": False,
            "action": "delete_customer",
            "message": "User declined customer deletion.",
            "data": None,
        }

    # ---------------------------------------------
    # DELETE
    # ---------------------------------------------

    result = db_delete_customer(
        customer_id=customer_id,
    )

    if not result["success"]:

        print(f"❌ CUSTOMER DELETE FAILED: " f"{result['message']}")

        return {
            "success": False,
            "action": "delete_customer",
            "message": result["message"],
            "data": None,
        }

    print(f"🗑️ CUSTOMER DELETED: " f"{customer['id']}")

    return {
        "success": True,
        "action": "delete_customer",
        "message": "Customer deleted successfully.",
        "data": customer,
    }
