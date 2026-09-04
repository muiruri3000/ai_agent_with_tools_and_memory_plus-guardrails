import mysql.connector
from mysql.connector import Error

from config.settings import (
    DB_HOST,
    DB_PORT,
    DB_NAME,
    DB_USER,
    DB_PASSWORD,
)


def get_connection():
    """
    Create and return a MySQL database connection.
    """

    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def get_customers():
    """
    Retrieve all customers from the database.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, name, email, city
            FROM customers
            ORDER BY id
            """)

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def get_customer_by_id(customer_id: int) -> dict | None:
    """
    Retrieve a single customer by ID.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, name, email, city
            FROM customers
            WHERE id = %s
            """,
            (customer_id,),
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def get_customer_by_id(customer_id: int) -> dict | None:
    """
    Retrieve a single customer by ID.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT id, name, email, city
            FROM customers
            WHERE id = %s
            """,
            (customer_id,),
        )

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def find_customer(
    name: str = None,
    email: str = None,
    city: str = None,
) -> list:
    """
    Find customers by name, email, or city.

    Multiple supplied conditions use OR matching.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        conditions = []
        values = []

        if name:
            conditions.append("name LIKE %s")
            values.append(f"%{name}%")

        if email:
            conditions.append("email = %s")
            values.append(email)

        if city:
            conditions.append("city LIKE %s")
            values.append(f"%{city}%")

        if not conditions:
            return []

        query = f"""
            SELECT id, name, email, city
            FROM customers
            WHERE {" OR ".join(conditions)}
            ORDER BY id
        """

        cursor.execute(query, values)

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def create_customer(
    name: str,
    email: str,
    city: str,
) -> dict:
    """
    Create a new customer.

    Returns a structured result instead of exposing
    raw database exceptions to the agent.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        # ---------------------------------------------
        # DUPLICATE CHECK
        # ---------------------------------------------

        cursor.execute(
            """
            SELECT id, name, email, city
            FROM customers
            WHERE email = %s
            LIMIT 1
            """,
            (email,),
        )

        existing = cursor.fetchone()

        if existing:
            return {
                "success": False,
                "message": "A customer with this email already exists.",
                "data": existing,
            }

        # ---------------------------------------------
        # INSERT
        # ---------------------------------------------

        cursor.execute(
            """
            INSERT INTO customers
                (name, email, city)
            VALUES
                (%s, %s, %s)
            """,
            (name, email, city),
        )

        connection.commit()

        customer_id = cursor.lastrowid

        return {
            "success": True,
            "message": "Customer created successfully.",
            "data": {
                "id": customer_id,
                "name": name,
                "email": email,
                "city": city,
            },
        }

    except Error as e:

        connection.rollback()

        return {
            "success": False,
            "message": f"Database error: {e}",
            "data": None,
        }

    finally:
        cursor.close()
        connection.close()


def update_customer(
    customer_id: int,
    name: str = None,
    email: str = None,
    city: str = None,
) -> dict:
    """
    Update an existing customer.

    Only supplied fields are modified.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        # ---------------------------------------------
        # VERIFY CUSTOMER EXISTS
        # ---------------------------------------------

        cursor.execute(
            """
            SELECT id, name, email, city
            FROM customers
            WHERE id = %s
            """,
            (customer_id,),
        )

        existing = cursor.fetchone()

        if not existing:

            return {
                "success": False,
                "message": f"Customer with ID {customer_id} was not found.",
                "data": None,
            }

        # ---------------------------------------------
        # BUILD UPDATE
        # ---------------------------------------------

        fields = []
        values = []

        if name is not None:
            fields.append("name = %s")
            values.append(name)

        if email is not None:
            fields.append("email = %s")
            values.append(email)

        if city is not None:
            fields.append("city = %s")
            values.append(city)

        if not fields:

            return {
                "success": False,
                "message": "No fields were provided for update.",
                "data": existing,
            }

        # ---------------------------------------------
        # DUPLICATE EMAIL CHECK
        # ---------------------------------------------

        if email is not None:

            cursor.execute(
                """
                SELECT id
                FROM customers
                WHERE email = %s
                AND id != %s
                LIMIT 1
                """,
                (email, customer_id),
            )

            duplicate = cursor.fetchone()

            if duplicate:

                return {
                    "success": False,
                    "message": "Another customer already uses that email.",
                    "data": None,
                }

        # ---------------------------------------------
        # UPDATE
        # ---------------------------------------------

        values.append(customer_id)

        query = f"""
            UPDATE customers
            SET {", ".join(fields)}
            WHERE id = %s
        """

        cursor.execute(query, values)

        connection.commit()

        # ---------------------------------------------
        # RETURN UPDATED RECORD
        # ---------------------------------------------

        cursor.execute(
            """
            SELECT id, name, email, city
            FROM customers
            WHERE id = %s
            """,
            (customer_id,),
        )

        customer = cursor.fetchone()

        return {
            "success": True,
            "message": "Customer updated successfully.",
            "data": customer,
        }

    except Error as e:

        connection.rollback()

        return {
            "success": False,
            "message": f"Database error: {e}",
            "data": None,
        }

    finally:
        cursor.close()
        connection.close()


def delete_customer(customer_id: int) -> dict:
    """
    Delete a customer by ID.
    """

    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        # ---------------------------------------------
        # GET CUSTOMER BEFORE DELETE
        # ---------------------------------------------

        cursor.execute(
            """
            SELECT id, name, email, city
            FROM customers
            WHERE id = %s
            """,
            (customer_id,),
        )

        customer = cursor.fetchone()

        if not customer:

            return {
                "success": False,
                "message": f"Customer with ID {customer_id} was not found.",
                "data": None,
            }

        # ---------------------------------------------
        # DELETE
        # ---------------------------------------------

        cursor.execute(
            """
            DELETE FROM customers
            WHERE id = %s
            """,
            (customer_id,),
        )

        connection.commit()

        return {
            "success": True,
            "message": "Customer deleted successfully.",
            "data": customer,
        }

    except Error as e:

        connection.rollback()

        return {
            "success": False,
            "message": f"Database error: {e}",
            "data": None,
        }

    finally:
        cursor.close()
        connection.close()
