import os
from pathlib import Path

from dotenv import load_dotenv

_ENV_LOADED = False


def load_env() -> None:
    """Load .env from the first location that exists.

    Supports both layouts: <root>/app/.env (local development) and <root>/.env
    (container/deploy, e.g. /app/.env). Real environment variables always take
    precedence so platform-injected configuration is never overridden.
    """
    global _ENV_LOADED
    if _ENV_LOADED:
        return
    _ENV_LOADED = True

    here = Path(__file__).resolve().parent
    candidates = [
        here / ".env",            # .../app/.env
        here.parent / ".env",     # <root>/.env (container: /app/.env)
        Path.cwd() / ".env",
        Path("/app/.env"),
    ]
    for candidate in candidates:
        if candidate.is_file():
            load_dotenv(dotenv_path=str(candidate), override=False)

    # Last resort: python-dotenv auto-discovery (walks up from the cwd).
    load_dotenv(override=False)
