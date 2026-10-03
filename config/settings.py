import os

from dotenv import load_dotenv

load_dotenv()


# -------------------------------------------------
# Environment
# -------------------------------------------------

APP_ENV = os.getenv("APP_ENV", "development")


# -------------------------------------------------
# Secrets / external services
# -------------------------------------------------

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")


# -------------------------------------------------
# Database
# -------------------------------------------------

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")


# -------------------------------------------------
# Gemini
# -------------------------------------------------

MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.5-flash-lite",
)


# -------------------------------------------------
# Metrics server
# -------------------------------------------------

METRICS_HOST = os.getenv(
    "METRICS_HOST",
    "127.0.0.1",
)

METRICS_PORT = int(
    os.getenv(
        "METRICS_PORT",
        "8000",
    )
)


# -------------------------------------------------
# Logging
# -------------------------------------------------

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO",
)

LOG_PATH = os.getenv(
    "LOG_PATH",
    "logs/atlas.jsonl",
)


# -------------------------------------------------
# Memory storage
# -------------------------------------------------

ATLAS_MEMORY_FILE = os.getenv(
    "ATLAS_MEMORY_FILE",
    "memory/data.json",
)


# -------------------------------------------------
# Tool execution timeouts
# -------------------------------------------------

DEFAULT_TOOL_TIMEOUT_SECONDS = int(
    os.getenv(
        "DEFAULT_TOOL_TIMEOUT_SECONDS",
        "30",
    )
)

TOOL_TIMEOUT_READ_SECONDS = int(
    os.getenv(
        "TOOL_TIMEOUT_READ_SECONDS",
        "10",
    )
)

TOOL_TIMEOUT_EXTERNAL_READ_SECONDS = int(
    os.getenv(
        "TOOL_TIMEOUT_EXTERNAL_READ_SECONDS",
        "30",
    )
)

TOOL_TIMEOUT_MEMORY_READ_SECONDS = int(
    os.getenv(
        "TOOL_TIMEOUT_MEMORY_READ_SECONDS",
        "10",
    )
)

TOOL_TIMEOUT_MEMORY_WRITE_SECONDS = int(
    os.getenv(
        "TOOL_TIMEOUT_MEMORY_WRITE_SECONDS",
        "10",
    )
)

TOOL_TIMEOUT_WRITE_SECONDS = int(
    os.getenv(
        "TOOL_TIMEOUT_WRITE_SECONDS",
        "10",
    )
)

TOOL_TIMEOUT_DESTRUCTIVE_SECONDS = int(
    os.getenv(
        "TOOL_TIMEOUT_DESTRUCTIVE_SECONDS",
        "10",
    )
)


# -------------------------------------------------
# Role rate limits
# -------------------------------------------------

RATE_LIMIT_READ_ONLY_CALLS = int(
    os.getenv(
        "RATE_LIMIT_READ_ONLY_CALLS",
        "30",
    )
)

RATE_LIMIT_READ_ONLY_WINDOW_SECONDS = int(
    os.getenv(
        "RATE_LIMIT_READ_ONLY_WINDOW_SECONDS",
        "60",
    )
)

RATE_LIMIT_STANDARD_CALLS = int(
    os.getenv(
        "RATE_LIMIT_STANDARD_CALLS",
        "20",
    )
)

RATE_LIMIT_STANDARD_WINDOW_SECONDS = int(
    os.getenv(
        "RATE_LIMIT_STANDARD_WINDOW_SECONDS",
        "60",
    )
)

RATE_LIMIT_ADMIN_CALLS = int(
    os.getenv(
        "RATE_LIMIT_ADMIN_CALLS",
        "60",
    )
)

RATE_LIMIT_ADMIN_WINDOW_SECONDS = int(
    os.getenv(
        "RATE_LIMIT_ADMIN_WINDOW_SECONDS",
        "60",
    )
)
