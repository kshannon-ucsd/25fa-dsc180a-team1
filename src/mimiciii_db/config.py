import os


def db_url(env_var: str = "DATABASE_URL") -> str:
    url = os.getenv(env_var)
    if not url:
        raise RuntimeError(f"{env_var} not set")
    return url
