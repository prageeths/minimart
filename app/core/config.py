"""Application configuration settings."""

from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = "postgresql://username:password@localhost:5432/minimart_db"
    
    # OpenAI
    openai_api_key: str = ""
    
    # Email
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    
    # Supplier emails
    supplier_emails: List[str] = [
        "prageethsandakalum@gmail.com",
        "prageeths@outlook.com", 
        "malshasf@outlook.com",
        "malshasf603@gmail.com"
    ]
    
    # Security
    secret_key: str = "your-secret-key-here"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Application
    environment: str = "development"
    debug: bool = True
    api_v1_str: str = "/api/v1"
    project_name: str = "MiniMart AI Inventory Management"
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
