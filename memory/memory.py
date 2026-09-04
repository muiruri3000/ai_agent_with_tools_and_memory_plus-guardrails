import json
import os
from pathlib import Path

MEMORY_FILE = Path(os.getenv("ATLAS_MEMORY_FILE", "memory/data.json"))


def _load_memory() -> list:
    """
    Load all persistent memories.
    """

    if not MEMORY_FILE.exists():
        return []

    try:
        with open(MEMORY_FILE, "r", encoding="utf-8") as file:
            return json.load(file)

    except (json.JSONDecodeError, OSError):
        return []


def _save_memory(memories: list):
    """
    Save memories to disk.
    """

    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(MEMORY_FILE, "w", encoding="utf-8") as file:

        json.dump(memories, file, indent=2, ensure_ascii=False)


def remember(fact: str) -> str:
    """
    Store a fact in persistent memory.
    """

    memories = _load_memory()

    if fact not in memories:
        memories.append(fact)

        _save_memory(memories)

        return f"Remembered: {fact}"

    return f"I already remember: {fact}"


def recall() -> list:
    """
    Retrieve all stored memories.
    """

    return _load_memory()


def forget(fact: str) -> str:
    """
    Remove a specific fact from memory.
    """

    memories = _load_memory()

    if fact in memories:

        memories.remove(fact)

        _save_memory(memories)

        return f"Forgot: {fact}"

    return f"I don't have that memory."
