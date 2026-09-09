from collections.abc import Mapping, Sequence


REDACTED = "[REDACTED]"


SENSITIVE_KEYS = {
    "password",
    "token",
    "secret",
    "api_key",
    "authorization",
    "email",
    "fact",
}


def is_sensitive_key(key) -> bool:
    """
    Determine whether an argument key contains sensitive data.
    """

    return str(key).lower() in SENSITIVE_KEYS


def redact_sensitive_data(value):
    """
    Recursively redact sensitive values from audit data.

    Dictionaries have their sensitive keys redacted.
    Lists and tuples are recursively processed.
    Other values are returned unchanged.
    """

    if isinstance(value, Mapping):
        return {
            key: (
                REDACTED
                if is_sensitive_key(key)
                else redact_sensitive_data(item)
            )
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            redact_sensitive_data(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return tuple(
            redact_sensitive_data(item)
            for item in value
        )

    if isinstance(value, Sequence) and not isinstance(
        value,
        (str, bytes, bytearray),
    ):
        return type(value)(
            redact_sensitive_data(item)
            for item in value
        )

    return value
