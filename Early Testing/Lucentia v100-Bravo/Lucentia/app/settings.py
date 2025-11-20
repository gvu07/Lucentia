from pydantic_settings import BaseSettings
from typing import List, Optional
import os

class Settings(BaseSettings):
    # Application
    app_name: str = "Lucentia"
    debug: bool = True
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    
    # Security
    secret_key: str = "your_super_secret_key_here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Database
    database_url: str = "postgresql://lucentia:lucentia123@localhost:5432/lucentia_db"
    
    # Plaid API
    plaid_client_id: str
    plaid_secret: str
    plaid_env: str = "development"
    plaid_products: str = "transactions,auth,identity,balance"
    plaid_country_codes: str = "US,CA,GB"
    plaid_redirect_uri: Optional[str] = None
    
    # Redis
    redis_url: str = "redis://localhost:6379"

    # Demo data seeding
    demo_seed_enabled: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
