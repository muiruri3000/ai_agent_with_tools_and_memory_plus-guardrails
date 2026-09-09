import re


MAX_NAME_LENGTH = 150
MAX_EMAIL_LENGTH = 254
MAX_CITY_LENGTH = 100
MAX_FACT_LENGTH = 2000
MAX_QUERY_LENGTH = 500


EMAIL_PATTERN = re.compile(
    r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
)


def validate_positive_integer(
    value,
    field_name: str,
) -> None:
    if value <= 0:
        raise ValueError(
            f"{field_name} must be greater than 0."
        )


def validate_non_empty_string(
    value,
    field_name: str,
    max_length: int,
) -> None:
    if not value.strip():
        raise ValueError(
            f"{field_name} must not be empty."
        )

    if len(value.strip()) > max_length:
        raise ValueError(
            f"{field_name} exceeds the maximum "
            f"length of {max_length} characters."
        )


def validate_name(value: str) -> None:
    validate_non_empty_string(
        value,
        "name",
        MAX_NAME_LENGTH,
    )


def validate_email(value: str) -> None:
    validate_non_empty_string(
        value,
        "email",
        MAX_EMAIL_LENGTH,
    )

    if not EMAIL_PATTERN.match(value.strip()):
        raise ValueError(
            "email must be a valid email address."
        )


def validate_city(value: str) -> None:
    validate_non_empty_string(
        value,
        "city",
        MAX_CITY_LENGTH,
    )


def validate_fact(value: str) -> None:
    validate_non_empty_string(
        value,
        "fact",
        MAX_FACT_LENGTH,
    )


def validate_query(value: str) -> None:
    validate_non_empty_string(
        value,
        "query",
        MAX_QUERY_LENGTH,
    )


def validate_tool_values(
    function_name: str,
    arguments: dict,
) -> None:
    """
    Validate semantic constraints on tool arguments.

    Type and signature validation should happen before
    this function is called.
    """

    if "customer_id" in arguments:
        validate_positive_integer(
            arguments["customer_id"],
            "customer_id",
        )

    if "name" in arguments:
        validate_name(
            arguments["name"]
        )

    if "email" in arguments:
        validate_email(
            arguments["email"]
        )

    if "city" in arguments:
        validate_city(
            arguments["city"]
        )

    if "fact" in arguments:
        validate_fact(
            arguments["fact"]
        )

    if "query" in arguments:
        validate_query(
            arguments["query"]
        )
