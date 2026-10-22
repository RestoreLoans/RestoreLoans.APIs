import json
import logging
import os
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

_JSON_ENV_VARS = (
    "GOOGLE_CREDENTIALS_JSON",
    "GOOGLE_SERVICE_ACCOUNT_JSON",
    "GCS_CREDENTIALS_JSON",
)
_configured = False


def configure_gcs_credentials() -> bool:
    """Point GOOGLE_APPLICATION_CREDENTIALS at usable credentials.

    Supports hosts that cannot ship a credentials file (e.g. Render) by
    accepting the service-account JSON in an environment variable and writing
    it to a temporary file. Existing, valid configuration is left untouched.
    """
    global _configured
    if _configured:
        return True

    configured_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if configured_path and Path(configured_path).is_file():
        _configured = True
        return True

    raw = next(
        (value for value in (os.getenv(name) for name in _JSON_ENV_VARS) if value),
        None,
    )
    if raw:
        try:
            json.loads(raw)
        except json.JSONDecodeError:
            logger.error(
                "GCS credentials environment variable is not valid JSON; "
                "documents will not be uploaded"
            )
            return False
        target = Path(tempfile.gettempdir()) / "restoreloans-gcs.json"
        target.write_text(raw, encoding="utf-8")
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(target)
        _configured = True
        logger.info("GCS credentials loaded from environment into %s", target)
        return True

    local = Path(__file__).resolve().parent / "google.json"
    if local.is_file():
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(local)
        _configured = True
        return True

    logger.warning(
        "GCS credentials not configured (set GOOGLE_CREDENTIALS_JSON or place "
        "google.json in app/utils); documents will be kept in memory only"
    )
    return False
