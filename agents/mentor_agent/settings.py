"""
Configuration management for mentor agent using existing environment variables.
Leverages existing BLACKBOX_API_KEY and DATABASE_URL from main system.
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator, ConfigDict
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class MentorSettings(BaseSettings):
    """Mentor agent settings leveraging existing environment configuration."""
    
    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # LLM Configuration (Using existing BlackboxAI setup)
    llm_provider: str = Field(default="blackboxai", description="LLM provider")
    llm_api_key: str = Field(..., env="BLACKBOX_API_KEY", description="BlackboxAI API key")
    llm_model: str = Field(default="anthropic/claude-sonnet-4", description="Model name")
    
    # Database Configuration (Using existing PostgreSQL)
    database_url: str = Field(..., env="DATABASE_URL", description="PostgreSQL connection string")
    
    # ChromaDB Configuration (Using existing vector store)
    chroma_path: str = Field(default="./chroma_memory", description="ChromaDB storage path")
    embedding_model: str = Field(default="sentence-transformers/all-MiniLM-L6-v2", description="Embedding model")
    
    # Mentor-Specific Configuration
    max_memory_results: int = Field(default=3, description="Max past interactions to retrieve")
    hint_escalation_levels: int = Field(default=4, description="Number of hint levels")
    similarity_threshold: float = Field(default=0.7, description="Memory similarity threshold")
    recent_repeat_days: int = Field(default=7, description="Days to consider recent repeat")
    pattern_recognition_days: int = Field(default=30, description="Days for pattern recognition")
    
    # Application Configuration
    app_env: str = Field(default="development", description="Environment")
    log_level: str = Field(default="INFO", description="Logging level")
    debug: bool = Field(default=False, description="Debug mode")
    max_retries: int = Field(default=3, description="Max retry attempts")
    timeout_seconds: int = Field(default=30, description="Default timeout")
    
    @field_validator("llm_api_key")
    @classmethod
    def validate_llm_key(cls, v):
        """Ensure BlackboxAI API key is not empty."""
        if not v or v.strip() == "":
            raise ValueError("BLACKBOX_API_KEY cannot be empty")
        return v
    
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v):
        """Ensure database URL is properly formatted."""
        if not v or not v.startswith(("postgresql://", "postgres://", "sqlite://")):
            raise ValueError("DATABASE_URL must be a valid PostgreSQL or SQLite connection string")
        return v


def load_mentor_settings() -> MentorSettings:
    """Load mentor settings with proper error handling."""
    try:
        return MentorSettings()
    except Exception as e:
        error_msg = f"Failed to load mentor settings: {e}"
        if "BLACKBOX_API_KEY" in str(e):
            error_msg += "\nMake sure BLACKBOX_API_KEY is set in your .env file"
        elif "DATABASE_URL" in str(e):
            error_msg += "\nMake sure DATABASE_URL is set in your .env file"
        raise ValueError(error_msg) from e


# Global settings instance
mentor_settings = load_mentor_settings()