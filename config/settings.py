import os
from typing import Optional
from pydantic_settings import BaseSettings
from urllib.parse import urlparse


class Settings(BaseSettings):
    # Database settings
    neon_database_url: str = os.getenv("NEON_DATABASE_URL", "")
    
    # AI settings
    google_api_key: Optional[str] = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
    
    # File processing settings
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", 10485760))  # 10MB default
    chunk_size: int = int(os.getenv("CHUNK_SIZE", 1000))
    chunk_overlap: int = int(os.getenv("CHUNK_OVERLAP", 200))
    
    # Upload settings
    upload_dir: str = "/app/uploads"
    
    # API settings
    cors_origins: list = ["*"]
    cors_credentials: bool = True
    cors_methods: list = ["*"]
    cors_headers: list = ["*"]
    
    # Logging settings
    log_level: str = "INFO"
    
    # Redis settings for caching
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = int(os.getenv("REDIS_DB", 0))
    redis_password: Optional[str] = os.getenv("REDIS_PASSWORD")
    
    # Performance settings
    cache_ttl_response: int = int(os.getenv("CACHE_TTL_RESPONSE", 600))  # 10 minutes
    cache_ttl_search: int = int(os.getenv("CACHE_TTL_SEARCH", 300))     # 5 minutes
    max_context_tokens: int = int(os.getenv("MAX_CONTEXT_TOKENS", 4000))
    
    # Database pool settings
    db_min_connections: int = int(os.getenv("DB_MIN_CONNECTIONS", 5))
    db_max_connections: int = int(os.getenv("DB_MAX_CONNECTIONS", 20))
    db_command_timeout: int = int(os.getenv("DB_COMMAND_TIMEOUT", 60))
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Parse Redis URL to get host and port
        try:
            parsed_url = urlparse(self.redis_url)
            self.redis_host = parsed_url.hostname or "localhost"
            self.redis_port = parsed_url.port or 6379
            if parsed_url.password:
                self.redis_password = parsed_url.password
        except Exception:
            # Fallback to default values
            pass
    
    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings() 