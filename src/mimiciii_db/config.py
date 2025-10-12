import os

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def db_url(env_var: str = "DATABASE_URL") -> str:
    url = os.getenv(env_var)
    if not url:
        raise RuntimeError(f"{env_var} not set")
    return url
