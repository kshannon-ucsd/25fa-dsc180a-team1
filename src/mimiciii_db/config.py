import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
# Look for .env file in the src directory
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(env_path)


def db_url(env_var: str = "DATABASE_URL") -> str:
    url = os.getenv(env_var)
    if not url:
        raise RuntimeError(f"{env_var} not set")
    return url
