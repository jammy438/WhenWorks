from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from enum import Enum

# Need this to know if I'm running locally vs on the server
class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

class Settings(BaseSettings):
    # This tells pydantic to load from .env files automatically
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Basic app stuff - helps with debugging and API docs
    environment: Environment = Environment.DEVELOPMENT
    app_name: str = "Calendar API"
    debug: bool = False  # Turn off in production for security
    
    # Database connection - PostgreSQL for real deployment, SQLite for local testing
    database_url: str  # No default - must be set in environment
    
    # JWT auth settings - needed for login/logout functionality
    secret_key: str  # Must be secure - no default to force proper setup
    algorithm: str = "HS256"  # Standard JWT algorithm
    access_token_expire_minutes: int = 30  # How long users stay logged in
    
    # Security stuff for the API - controls who can access from where
    allowed_hosts: list[str] = []  # Specific domains in production
    cors_origins: list[str] = []  # Frontend URLs that can call the API
    
    # Logging config - helps debug issues when things go wrong
    log_level: str = "INFO"  # Can change to DEBUG when troubleshooting
    
    # External services I might need later - Redis for caching, email for notifications
    redis_url: str = "redis://localhost:6379/0"  # Cache/session storage
    smtp_server: str = "smtp.example.com"  # Email notifications
    smtp_port: int = 587  # Standard email port
    
    # Make sure critical settings are actually secure
    @field_validator('secret_key')
    @classmethod
    def validate_secret_key(cls, v):
        if not v:
            raise ValueError('Secret key cannot be empty')
        if len(v) < 32:
            raise ValueError('Secret key must be at least 32 characters long')
        if v in ['your-secret-key', 'secret', 'password', 'changeme']:
            raise ValueError('Secret key cannot be a common/default value')
        return v
    
    # Check database URL is properly formatted
    @field_validator('database_url')
    @classmethod
    def validate_database_url(cls, v):
        if not v:
            raise ValueError('Database URL cannot be empty')
        
        allowed_schemes = ['postgresql://', 'postgres://', 'sqlite:///', 'mysql://']
        if not any(v.startswith(scheme) for scheme in allowed_schemes):
            raise ValueError(f'Database URL must start with one of: {", ".join(allowed_schemes)}')
        
        return v