import os

import mysql.connector
from dotenv import load_dotenv

load_dotenv()


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        database=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


def get_customers():
    connection = get_connection()

    try:
        cursor = connection.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, name, email, city
            FROM customers
        """)

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


if __name__ == "__main__":
    customers = get_customers()

    print("\nCustomers:\n")

    for customer in customers:
        print(customer)
