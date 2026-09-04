def request_confirmation(
    action: str,
    description: str,
) -> bool:
    """
    Ask the user to confirm an action.
    """

    print()
    print("⚠️  CONFIRMATION REQUIRED")
    print(f"Action: {action}")
    print(f"Details: {description}")
    print()

    answer = input("Do you want Atlas to proceed? [y/N]: ")

    return answer.strip().lower() in {
        "y",
        "yes",
    }
