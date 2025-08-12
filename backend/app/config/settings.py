from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from enum import Enum
import os
from functools import lru_cache

# Need this to know if I'm running locally vs on the server
class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings(BaseSettings):
    # This tells pydantic to load from .env files automatically
    model_config = SettingsConfigDict(
        env_file=[
            ".env",
            f".{os.getenv('ENVIRONMENT', 'development')}.env"
        ],
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Basic app stuff - helps with debugging and API docs
    environment: Environment = Environment.DEVELOPMENT
    app_name: str = "WhenWorks"
    debug: bool = False
    
    # Database connection - PostgreSQL for real deployment, SQLite for local testing
    database_url: str  # type: ignore  # Loaded from .env automatically
    
    # JWT auth settings - needed for login/logout functionality
    secret_key: str  # type: ignore  # Loaded from .env automatically
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Security stuff for the API - controls who can access from where
    allowed_hosts: list[str] = []
    cors_origins: list[str] = []
    
    # Logging config - helps debug issues when things go wrong
    log_level: str = "INFO"
    log_format: str = "json"  # "json" or "text"
    log_file: str = "app.log"
    log_max_size: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5
    log_retention_days: int = 30
    
    # External services I might need later - Redis for caching, email for notifications
    redis_url: str = "redis://localhost:6379/0"
    smtp_server: str = "smtp.example.com"
    smtp_port: int = 587
    
    # Make sure critical settings are actually secure
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v):
        if not v:
            raise ValueError('Secret key cannot be empty')
        
        # Relax validation for development
        import os
        env = os.getenv('ENVIRONMENT', 'development')
        
        if env == 'production' and len(v) < 32:
            raise ValueError('Secret key must be at least 32 characters long in production')
        elif env != 'production' and len(v) < 8:
            raise ValueError('Secret key must be at least 8 characters long in development')
            
        if v in ['your-secret-key', 'secret', 'password', 'changeme']:
            raise ValueError('Secret key cannot be a common/default value')
        return v
    
    # Check database URL is properly formatted
    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v):
        if not v:
            raise ValueError('Database URL cannot be empty')
        
        allowed_schemes = ['postgresql://', 'postgres://', 'postgresql+psycopg2://', 'sqlite:///', 'mysql://']
        if not any(v.startswith(scheme) for scheme in allowed_schemes):
            raise ValueError(f'Database URL must start with one of: {", ".join(allowed_schemes)}')
        
        return v

@lru_cache()
def get_settings():
    return Settings()