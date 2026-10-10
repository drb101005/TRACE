"""Application configuration using Pydantic settings."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "sqlite:///./trace_audit.db"
    
    # Security
    secret_key: str = "dev-secret-key-change-in-production-minimum-32-characters-required"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    
    # LLM Configuration
    gemini_api_key: Optional[str] = None
    gemini_model: str = "gemini-pro"
    llm_enabled: bool = False
    
    # File Upload
    max_upload_size_mb: int = 100
    
    # MCP Server
    mcp_server_port: int = 3000
    
    # Environment
    environment: str = "development"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @property
    def max_upload_size_bytes(self) -> int:
        """Convert MB to bytes."""
        return self.max_upload_size_mb * 1024 * 1024


settings = Settings()
