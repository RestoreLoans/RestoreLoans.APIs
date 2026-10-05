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
    raise ValueError(
        "DATABASE_URL is not set. Provide it as an environment variable or add "
        "it to .env at the project root (or app/.env)."
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