import re


def route_request(user_input: str):
    """
    Determine whether a request should be handled
    deterministically before sending it to the LLM.

    Returns:
        A route name or None.
    """

    text = user_input.lower().strip()

    # =================================================
    # CUSTOMER LIST
    # =================================================

    customer_list_patterns = [
        r"\blist customers\b",
        r"\blist all customers\b",
        r"\bshow customers\b",
        r"\bshow all customers\b",
        r"\ball customers\b",
        r"\bevery customer\b",
        r"\bget customers\b",
    ]

    for pattern in customer_list_patterns:
        if re.search(pattern, text):
            return "get_customers"

    # =================================================
    # CUSTOMER DELETE
    # =================================================

    customer_delete_patterns = [
        r"\bdelete\s+(?:customer\s+)?",
        r"\bremove\s+(?:customer\s+)?",
        r"\bpermanently\s+delete\s+(?:customer\s+)?",
        r"\bpermanently\s+remove\s+(?:customer\s+)?",
    ]

    for pattern in customer_delete_patterns:
        if re.search(pattern, text):
            return "delete_customer"

    # =================================================
    # CUSTOMER UPDATE
    # =================================================

    update_patterns = [
        r"\bchange\s+",
        r"\bupdate\s+",
        r"\bedit\s+",
        r"\bmodify\s+",
        r"\bset\s+",
    ]

    for pattern in update_patterns:
        if re.search(pattern, text):
            return "update_customer"

    # =================================================
    # CUSTOMER LOOKUP
    # =================================================

    customer_lookup_patterns = [
        r"\bfind\s+",
        r"\bwho is\s+",
        r"\bwho's\s+",
        r"\bwhich customer\b",
        r"\bwhich customers\b",
        r"\bwhat is\s+.*\bemail\b",
        r"\bwhat's\s+.*\bemail\b",
        r"\bwhat is\s+.*\bcity\b",
        r"\bwhat's\s+.*\bcity\b",
        r"\bwhat is\s+.*\bdetails\b",
        r"\bwhat's\s+.*\bdetails\b",
    ]

    for pattern in customer_lookup_patterns:
        if re.search(pattern, text):
            return "find_customer"

    # =================================================
    # CURRENT / EXTERNAL INFORMATION
    # =================================================

    web_patterns = [
        r"\bcurrent\b",
        r"\blatest\b",
        r"\brecent\b",
        r"\btoday\b",
        r"\bnews\b",
        r"\binternet\b",
        r"\bpopulation\b",
        r"\bweather\b",
    ]

    for pattern in web_patterns:
        if re.search(pattern, text):
            return "web_search"

    return None


# =====================================================
# CUSTOMER QUERY EXTRACTION
# =====================================================


def extract_customer_name(user_input: str) -> str | None:
    """
    Extract a likely customer name from a simple
    customer lookup request.
    """

    text = user_input.strip()

    patterns = [
        r"\bfind\s+(.+)",
        r"\bwho is\s+(.+)",
        r"\bwho's\s+(.+)",
        r"\bdelete\s+(?:customer\s+)?(.+)",
        r"\bremove\s+(?:customer\s+)?(.+)",
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:

            value = match.group(1).strip()

            value = re.sub(
                r"\bcustomer\b",
                "",
                value,
                flags=re.IGNORECASE,
            ).strip()

            value = value.rstrip("?.!, ")

            if value:
                return value

    return None


def extract_customer_query(user_input: str) -> dict:
    """
    Extract customer search parameters from a
    natural-language request.

    Returns:
        {
            "name": str | None,
            "email": str | None,
            "city": str | None
        }
    """

    text = user_input.strip()

    result = {
        "name": None,
        "email": None,
        "city": None,
    }

    # =================================================
    # EMAIL
    # =================================================

    email_match = re.search(
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
        text,
    )

    if email_match:

        result["email"] = email_match.group(0)

        return result

    # =================================================
    # CITY
    # =================================================

    city_patterns = [
        r"\blives in\s+([A-Za-z ]+)",
        r"\blive in\s+([A-Za-z ]+)",
        r"\bfrom\s+([A-Za-z ]+)",
    ]

    known_cities = [
        "Nairobi",
        "Kiambu",
        "Thika",
        "Nanyuki",
    ]

    for pattern in city_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:

            city = match.group(1).strip()

            city = city.rstrip("?.!, ")

            for known_city in known_cities:

                if city.lower() == known_city.lower():

                    result["city"] = known_city

                    return result

    # =================================================
    # NAME
    # =================================================

    name_patterns = [
        r"\bfind\s+(.+)",
        r"\bwho is\s+(.+)",
        r"\bwho's\s+(.+)",
        r"\bdelete\s+(?:customer\s+)?(.+)",
        r"\bremove\s+(?:customer\s+)?(.+)",
        r"\bwhat is\s+(.+?)['’]s\s+(?:email|city|details)",
        r"\bwhat's\s+(.+?)['’]s\s+(?:email|city|details)",
    ]

    for pattern in name_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:

            name = match.group(1).strip()

            name = name.rstrip("?.!, ")

            if name:

                result["name"] = name.title()

                return result

    return result


# =====================================================
# CUSTOMER UPDATE EXTRACTION
# =====================================================


def extract_customer_update(user_input: str) -> dict:
    """
    Extract customer update information from a
    natural-language request.

    Returns:
        {
            "name": str | None,
            "customer_id": int | None,
            "field": str | None,
            "value": str | None
        }
    """

    text = user_input.strip()

    result = {
        "name": None,
        "customer_id": None,
        "field": None,
        "value": None,
    }

    # =================================================
    # CUSTOMER ID + FIELD + VALUE
    # =================================================

    # Example:
    # Change customer 5's city to Nairobi
    # Update customer 5's email to peter@example.com

    match = re.search(
        r"(?:change|update|edit|modify|set)\s+"
        r"customer\s+(?:id\s*)?(\d+)['’]s\s+"
        r"(name|email|city)\s+"
        r"(?:to|into)\s+"
        r"(.+?)(?:\?|$)",
        text,
        re.IGNORECASE,
    )

    if match:

        result["customer_id"] = int(match.group(1))

        result["field"] = match.group(2).lower()

        result["value"] = match.group(3).strip()

        result["value"] = result["value"].rstrip("?.!, ")

        return result

    # =================================================
    # NAME + FIELD + VALUE
    # =================================================

    # Example:
    # Change Peter's city to Nairobi
    # Update John's email to john2@example.com
    # Set David's name to David Mwangi

    match = re.search(
        r"(?:change|update|edit|modify|set)\s+"
        r"(.+?)['’]s\s+"
        r"(name|email|city)\s+"
        r"(?:to|into)\s+"
        r"(.+?)(?:\?|$)",
        text,
        re.IGNORECASE,
    )

    if match:

        result["name"] = match.group(1).strip()

        result["field"] = match.group(2).lower()

        result["value"] = match.group(3).strip()

        result["value"] = result["value"].rstrip("?.!, ")

        return result

    # =================================================
    # NAME + FIELD WITHOUT POSSESSIVE APOSTROPHE
    # =================================================

    # Example:
    # Change Peter city to Nairobi
    # Update John email to john2@example.com

    match = re.search(
        r"(?:change|update|edit|modify|set)\s+"
        r"(.+?)\s+"
        r"(name|email|city)\s+"
        r"(?:to|into)\s+"
        r"(.+?)(?:\?|$)",
        text,
        re.IGNORECASE,
    )

    if match:

        result["name"] = match.group(1).strip()

        result["field"] = match.group(2).lower()

        result["value"] = match.group(3).strip()

        result["value"] = result["value"].rstrip("?.!, ")

        return result

    return result
