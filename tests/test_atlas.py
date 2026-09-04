import unittest
from unittest.mock import patch

from agent.atlas import Atlas


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

        mock_find_customer.return_value = [customer]

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

        mock_find_customer.return_value = [customer]

        mock_delete_customer.return_value = {
            "success": True,
            "action": "delete_customer",
            "message": "Customer deleted successfully.",
            "data": customer,
        }

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

        mock_find_customer.return_value = [customer]

        mock_update_customer.return_value = {
            "success": True,
            "action": "update_customer",
            "message": "Customer updated successfully.",
            "data": updated_customer,
        }

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

        mock_find_customer.return_value = [customer]

        mock_update_customer.return_value = {
            "success": True,
            "action": "update_customer",
            "message": "Customer updated successfully.",
            "data": updated_customer,
        }

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

        mock_get_customer_by_id.return_value = customer

        mock_update_customer.return_value = {
            "success": True,
            "action": "update_customer",
            "message": "Customer updated successfully.",
            "data": updated_customer,
        }

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

        mock_find_customer.return_value = [
            john_one,
            john_two,
        ]

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

        mock_find_customer.return_value = [customer]

        mock_update_customer.return_value = {
            "success": False,
            "action": "update_customer",
            "message": "Update failed.",
            "data": None,
        }

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

        mock_find_customer.return_value = customers

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

        mock_find_customer.return_value = []

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

        mock_find_customer.return_value = [customer]

        mock_delete_customer.return_value = {
            "success": False,
            "action": "delete_customer",
            "message": "User declined customer deletion.",
            "data": None,
        }

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
