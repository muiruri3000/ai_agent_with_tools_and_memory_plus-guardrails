import unittest

from agent.router import (
    route_request,
    extract_customer_query,
    extract_customer_update,
)


class TestRouteRequest(unittest.TestCase):

    # ---------------------------------------------
    # CUSTOMER LOOKUP
    # ---------------------------------------------

    def test_find_customer(self):

        self.assertEqual(
            route_request("Find John Kamau"),
            "find_customer",
        )

    def test_find_by_email(self):

        self.assertEqual(
            route_request("Find john@example.com"),
            "find_customer",
        )

    def test_find_by_city(self):

        self.assertEqual(
            route_request("Which customer lives in Thika?"),
            "find_customer",
        )

    def test_customer_email_question(self):

        self.assertEqual(
            route_request("What's Mary's email?"),
            "find_customer",
        )

    # ---------------------------------------------
    # CUSTOMER LIST
    # ---------------------------------------------

    def test_list_customers(self):

        self.assertEqual(
            route_request("List customers"),
            "get_customers",
        )

    def test_show_all_customers(self):

        self.assertEqual(
            route_request("Show all customers"),
            "get_customers",
        )

    # ---------------------------------------------
    # CUSTOMER UPDATE
    # ---------------------------------------------

    def test_update_by_name(self):

        self.assertEqual(
            route_request("Change Peter's city to Nairobi"),
            "update_customer",
        )

    def test_update_by_id(self):

        self.assertEqual(
            route_request("Change customer 5's city to Thika"),
            "update_customer",
        )

    # ---------------------------------------------
    # CUSTOMER DELETE
    # ---------------------------------------------

    def test_delete_customer(self):

        self.assertEqual(
            route_request("Delete Mary"),
            "delete_customer",
        )

    def test_remove_customer(self):

        self.assertEqual(
            route_request("Remove John Kamau"),
            "delete_customer",
        )

    # ---------------------------------------------
    # WEB SEARCH
    # ---------------------------------------------

    def test_current_information(self):

        self.assertEqual(
            route_request("What is the current population of Kenya?"),
            "web_search",
        )

    def test_weather(self):

        self.assertEqual(
            route_request("What's the weather today?"),
            "web_search",
        )


class TestExtractCustomerQuery(unittest.TestCase):

    def test_extract_email(self):

        result = extract_customer_query("Find john@example.com")

        self.assertEqual(
            result["email"],
            "john@example.com",
        )

        self.assertIsNone(result["name"])
        self.assertIsNone(result["city"])

    def test_extract_name(self):

        result = extract_customer_query("Find John Kamau")

        self.assertEqual(
            result["name"],
            "John Kamau",
        )

    def test_extract_name_from_email_question(self):

        result = extract_customer_query("What's Mary's email?")

        self.assertEqual(
            result["name"],
            "Mary",
        )

    def test_extract_city(self):

        result = extract_customer_query("Which customer lives in Thika?")

        self.assertEqual(
            result["city"],
            "Thika",
        )


class TestExtractCustomerUpdate(unittest.TestCase):

    def test_update_name_based(self):

        result = extract_customer_update("Change Peter's city to Nairobi")

        self.assertEqual(
            result["name"],
            "Peter",
        )

        self.assertIsNone(result["customer_id"])

        self.assertEqual(
            result["field"],
            "city",
        )

        self.assertEqual(
            result["value"],
            "Nairobi",
        )

    def test_update_email(self):

        result = extract_customer_update("Update John's email to john2@example.com")

        self.assertEqual(
            result["name"],
            "John",
        )

        self.assertEqual(
            result["field"],
            "email",
        )

        self.assertEqual(
            result["value"],
            "john2@example.com",
        )

    def test_update_by_customer_id(self):

        result = extract_customer_update("Change customer 5's city to Thika")

        self.assertIsNone(result["name"])

        self.assertEqual(
            result["customer_id"],
            5,
        )

        self.assertEqual(
            result["field"],
            "city",
        )

        self.assertEqual(
            result["value"],
            "Thika",
        )

    def test_update_name_field(self):

        result = extract_customer_update("Change Peter's name to Peter Mwangi")

        self.assertEqual(
            result["name"],
            "Peter",
        )

        self.assertEqual(
            result["field"],
            "name",
        )

        self.assertEqual(
            result["value"],
            "Peter Mwangi",
        )


if __name__ == "__main__":
    unittest.main()
