import logging
import os
from pathlib import Path

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

_ENV_LOADED = False


def load_env() -> None:
    """Load .env from every location that exists.

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
    found = False
    for candidate in candidates:
        if candidate.is_file():
            load_dotenv(dotenv_path=str(candidate), override=False)
            found = True
            logger.info("Loaded environment from %s", candidate)

    # Last resort: python-dotenv auto-discovery (walks up from the cwd).
    load_dotenv(override=False)

    if not found:
        logger.warning(
            "No .env file found (searched: %s). The application will rely on "
            "environment variables supplied by the host/runtime.",
            ", ".join(str(c) for c in candidates),
        )
