import unittest
from unittest.mock import MagicMock, patch

from database import db


class TestGetCustomers(unittest.TestCase):

    @patch("database.db.get_connection")
    def test_get_customers(self, mock_get_connection):

        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "name": "Joseph",
                "email": "joseph@example.com",
                "city": "Nairobi",
            },
            {
                "id": 3,
                "name": "David",
                "email": "david@example.com",
                "city": "Thika",
            },
        ]

        mock_connection.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection

        results = db.get_customers()

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["name"], "Joseph")
        self.assertEqual(results[1]["city"], "Thika")

        mock_cursor.execute.assert_called_once()


class TestFindCustomer(unittest.TestCase):

    @patch("database.db.get_connection")
    def test_find_by_name(self, mock_get_connection):

        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_cursor.fetchall.return_value = [
            {
                "id": 4,
                "name": "John Kamau",
                "email": "john@example.com",
                "city": "Nairobi",
            }
        ]

        mock_connection.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection

        results = db.find_customer(name="John Kamau")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "John Kamau")

        mock_cursor.execute.assert_called_once()

    @patch("database.db.get_connection")
    def test_find_by_email(self, mock_get_connection):

        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_cursor.fetchall.return_value = [
            {
                "id": 4,
                "name": "John Kamau",
                "email": "john@example.com",
                "city": "Nairobi",
            }
        ]

        mock_connection.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection

        results = db.find_customer(email="john@example.com")

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0]["email"],
            "john@example.com",
        )

    @patch("database.db.get_connection")
    def test_find_by_city(self, mock_get_connection):

        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_cursor.fetchall.return_value = [
            {
                "id": 3,
                "name": "David",
                "email": "david@example.com",
                "city": "Thika",
            }
        ]

        mock_connection.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection

        results = db.find_customer(city="Thika")

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["city"], "Thika")

    @patch("database.db.get_connection")
    def test_find_without_criteria(self, mock_get_connection):

        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_connection.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection

        results = db.find_customer()

        self.assertEqual(results, [])

        mock_cursor.execute.assert_not_called()


class TestCreateCustomer(unittest.TestCase):

    @patch("database.db.get_connection")
    def test_create_customer_success(self, mock_get_connection):

        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        # First query checks for duplicate email.
        mock_cursor.fetchone.side_effect = [
            None,
        ]

        mock_cursor.lastrowid = 10

        mock_connection.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection

        result = db.create_customer(
            name="Alice",
            email="alice@example.com",
            city="Nairobi",
        )

        self.assertTrue(result["success"])
        self.assertEqual(
            result["message"],
            "Customer created successfully.",
        )

        self.assertEqual(result["data"]["id"], 10)
        self.assertEqual(result["data"]["name"], "Alice")
        self.assertEqual(
            result["data"]["email"],
            "alice@example.com",
        )
        self.assertEqual(
            result["data"]["city"],
            "Nairobi",
        )

        mock_connection.commit.assert_called_once()

    @patch("database.db.get_connection")
    def test_create_duplicate_email(self, mock_get_connection):

        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_cursor.fetchone.return_value = {
            "id": 4,
            "name": "John Kamau",
            "email": "john@example.com",
            "city": "Nairobi",
        }

        mock_connection.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection

        result = db.create_customer(
            name="Another John",
            email="john@example.com",
            city="Thika",
        )

        self.assertFalse(result["success"])

        self.assertEqual(
            result["message"],
            "A customer with this email already exists.",
        )

        mock_connection.commit.assert_not_called()


class TestUpdateCustomer(unittest.TestCase):

    @patch("database.db.get_connection")
    def test_update_customer_success(self, mock_get_connection):

        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        existing_customer = {
            "id": 5,
            "name": "Peter Mwangi",
            "email": "peter@example.com",
            "city": "Thika",
        }

        updated_customer = {
            "id": 5,
            "name": "Peter Mwangi",
            "email": "peter@example.com",
            "city": "Nairobi",
        }

        mock_cursor.fetchone.side_effect = [
            existing_customer,
            updated_customer,
        ]

        mock_connection.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection

        result = db.update_customer(
            customer_id=5,
            city="Nairobi",
        )

        self.assertTrue(result["success"])
        self.assertEqual(
            result["data"]["city"],
            "Nairobi",
        )

        mock_connection.commit.assert_called_once()

    @patch("database.db.get_connection")
    def test_update_nonexistent_customer(self, mock_get_connection):

        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_cursor.fetchone.return_value = None

        mock_connection.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection

        result = db.update_customer(
            customer_id=999,
            city="Nairobi",
        )

        self.assertFalse(result["success"])

        self.assertEqual(
            result["message"],
            "Customer with ID 999 was not found.",
        )

        mock_connection.commit.assert_not_called()

    @patch("database.db.get_connection")
    def test_update_without_fields(self, mock_get_connection):

        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        existing_customer = {
            "id": 5,
            "name": "Peter Mwangi",
            "email": "peter@example.com",
            "city": "Thika",
        }

        mock_cursor.fetchone.return_value = existing_customer

        mock_connection.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection

        result = db.update_customer(
            customer_id=5,
        )

        self.assertFalse(result["success"])

        self.assertEqual(
            result["message"],
            "No fields were provided for update.",
        )

        mock_connection.commit.assert_not_called()

    @patch("database.db.get_connection")
    def test_update_duplicate_email(self, mock_get_connection):

        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        existing_customer = {
            "id": 5,
            "name": "Peter Mwangi",
            "email": "peter@example.com",
            "city": "Thika",
        }

        duplicate_customer = {
            "id": 4,
        }

        mock_cursor.fetchone.side_effect = [
            existing_customer,
            duplicate_customer,
        ]

        mock_connection.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection

        result = db.update_customer(
            customer_id=5,
            email="john@example.com",
        )

        self.assertFalse(result["success"])

        self.assertEqual(
            result["message"],
            "Another customer already uses that email.",
        )

        mock_connection.commit.assert_not_called()


class TestDeleteCustomer(unittest.TestCase):

    @patch("database.db.get_connection")
    def test_delete_customer_success(self, mock_get_connection):

        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        customer = {
            "id": 5,
            "name": "Peter Mwangi",
            "email": "peter@example.com",
            "city": "Thika",
        }

        mock_cursor.fetchone.return_value = customer

        mock_connection.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection

        result = db.delete_customer(customer_id=5)

        self.assertTrue(result["success"])

        self.assertEqual(
            result["message"],
            "Customer deleted successfully.",
        )

        self.assertEqual(
            result["data"]["name"],
            "Peter Mwangi",
        )

        mock_connection.commit.assert_called_once()

    @patch("database.db.get_connection")
    def test_delete_nonexistent_customer(self, mock_get_connection):

        mock_connection = MagicMock()
        mock_cursor = MagicMock()

        mock_cursor.fetchone.return_value = None

        mock_connection.cursor.return_value = mock_cursor
        mock_get_connection.return_value = mock_connection

        result = db.delete_customer(customer_id=999)

        self.assertFalse(result["success"])

        self.assertEqual(
            result["message"],
            "Customer with ID 999 was not found.",
        )

        mock_connection.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
