import os
from typing import Optional
from pydantic import BaseSettings


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
    
    class Config:
        env_file = ".env"


# Global settings instance
settings = Settings() 