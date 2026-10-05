from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
import os

from app.env_loader import load_env

# Load environment variables from the .env file (works for both <root>/app/.env
# and <root>/.env container layouts; real env vars win).
load_env()

# Access variables
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL is not set.\n"
        "This app reads configuration from environment variables. .env files are "
        "gitignored and are NOT copied into the Docker image, so a container must "
        "receive DATABASE_URL from its runtime.\n"
        "Fix by setting it on the host, for example:\n"
        "  docker run -e DATABASE_URL='postgresql://user:pass@host:5432/db' ...\n"
        "  docker compose:  environment: / env_file: pointing at a real .env\n"
        "  Kubernetes:      envFrom: secretRef: ...\n"
        "  Render/Fly/Heroku: add DATABASE_URL under the service's Environment "
        "variables.\n"
        "For local development, create app/.env (see .env.example)."
    )

logging.getLogger(__name__).info(
    "DATABASE_URL loaded (host=%s)", DATABASE_URL.split("@")[-1].split("/")[0]
)

SQLALCHEMY_DATABASE_URL = DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()