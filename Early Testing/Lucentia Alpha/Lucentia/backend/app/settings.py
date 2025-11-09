from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    PLAID_CLIENT_ID: str
    PLAID_SECRET: str
    PLAID_ENV: str = "sandbox"  # sandbox | development | production
    DATABASE_URL: str = "postgresql+psycopg://lucentia:lucentia@localhost:5432/lucentia"
    # If using Docker for backend too, point hostname to the compose service name, e.g. db

    class Config:
        env_file = ".env"

@lru_cache
def get_settings():
    return Settings()
