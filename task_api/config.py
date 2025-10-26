"""Configuration management for the Task API."""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Configuration
    api_title: str = "Task API - MCP PyCon Demo"
    api_version: str = "0.1.0"
    api_description: str = "A demo API showcasing MCP integration for secure LLM-to-API communication"

    # Security
    task_api_key: str = "demo-secret-key-change-in-production"

    # AWS Configuration
    aws_region: str = "us-east-2"
    aws_s3_bucket: str = "mcp-pycon-demo-bucket"
    aws_endpoint_url: str | None = None  # For LocalStack testing

    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
