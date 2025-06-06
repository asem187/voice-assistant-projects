"""
Configuration management for the Realtime Voice Assistant.
Handles environment variables, settings, and configuration validation.
"""

import os
import logging
from typing import List, Optional
from pathlib import Path
from pydantic import BaseSettings, Field, validator
from pydantic_settings import SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""
    url: str = Field(default="postgresql://user:pass@localhost:5432/voice_assistant")
    pool_size: int = Field(default=10, ge=1, le=50)
    max_overflow: int = Field(default=20, ge=0, le=100)
    echo: bool = Field(default=False)
    
    @validator('url')
    def validate_database_url(cls, v):
        if not v.startswith(('postgresql://', 'sqlite://')):
            raise ValueError('Database URL must start with postgresql:// or sqlite://')
        return v


class RedisSettings(BaseSettings):
    """Redis configuration settings."""
    url: str = Field(default="redis://localhost:6379/0")
    password: Optional[str] = Field(default=None)
    db: int = Field(default=0, ge=0, le=15)
    max_connections: int = Field(default=10, ge=1, le=100)


class OpenAISettings(BaseSettings):
    """OpenAI API configuration settings."""
    api_key: str = Field(..., min_length=1)
    realtime_api_url: str = Field(default="wss://api.openai.com/v1/realtime")
    model: str = Field(default="gpt-4o-realtime-preview-2024-10-01")
    timeout: int = Field(default=30, ge=1, le=300)
    max_retries: int = Field(default=3, ge=0, le=10)
    
    @validator('api_key')
    def validate_api_key(cls, v):
        if not v.startswith('sk-'):
            raise ValueError('OpenAI API key must start with sk-')
        return v


class AudioSettings(BaseSettings):
    """Audio processing configuration settings."""
    sample_rate: int = Field(default=24000, ge=8000, le=48000)
    chunk_size: int = Field(default=1024, ge=128, le=8192)
    channels: int = Field(default=1, ge=1, le=2)
    format: str = Field(default="int16")
    temp_dir: Path = Field(default=Path("./temp_audio"))
    
    # Voice Activity Detection
    vad_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    min_speech_duration: float = Field(default=0.5, ge=0.1, le=5.0)
    min_silence_duration: float = Field(default=1.0, ge=0.1, le=10.0)


class SecuritySettings(BaseSettings):
    """Security configuration settings."""
    secret_key: str = Field(..., min_length=32)
    jwt_secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiration_hours: int = Field(default=24, ge=1, le=168)
    
    @validator('secret_key', 'jwt_secret_key')
    def validate_keys(cls, v):
        if len(v) < 32:
            raise ValueError('Secret keys must be at least 32 characters long')
        return v


class APISettings(BaseSettings):
    """API server configuration settings."""
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000, ge=1024, le=65535)
    workers: int = Field(default=1, ge=1, le=8)
    reload: bool = Field(default=False)
    
    # Rate limiting
    rate_limit_requests: int = Field(default=100, ge=1, le=10000)
    rate_limit_window: int = Field(default=60, ge=1, le=3600)
    
    # File upload
    max_file_size: int = Field(default=10485760, ge=1024, le=104857600)  # 10MB max
    allowed_file_types: List[str] = Field(default=["txt", "md", "py", "js", "json", "yaml", "yml"])


class WebSocketSettings(BaseSettings):
    """WebSocket configuration settings."""
    heartbeat_interval: int = Field(default=30, ge=5, le=300)
    reconnect_attempts: int = Field(default=5, ge=1, le=20)
    reconnect_delay: int = Field(default=5, ge=1, le=60)
    max_message_size: int = Field(default=1048576, ge=1024, le=10485760)  # 1MB max


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""
    level: str = Field(default="INFO")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    date_format: str = Field(default="%Y-%m-%d %H:%M:%S")
    
    @validator('level')
    def validate_log_level(cls, v):
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f'Log level must be one of: {valid_levels}')
        return v.upper()


class Settings(BaseSettings):
    """Main application settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application metadata
    app_name: str = Field(default="Realtime Voice Assistant")
    app_version: str = Field(default="1.0.0")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    
    # Component settings
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    openai: OpenAISettings = Field(default_factory=lambda: OpenAISettings(api_key=os.getenv("OPENAI_API_KEY", "")))
    audio: AudioSettings = Field(default_factory=AudioSettings)
    security: SecuritySettings = Field(default_factory=lambda: SecuritySettings(
        secret_key=os.getenv("SECRET_KEY", "your-secret-key-here-32-chars-min"),
        jwt_secret_key=os.getenv("JWT_SECRET_KEY", "your-jwt-secret-here-32-chars-min")
    ))
    api: APISettings = Field(default_factory=APISettings)
    websocket: WebSocketSettings = Field(default_factory=WebSocketSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    
    # Monitoring
    metrics_port: int = Field(default=9090, ge=1024, le=65535)
    health_check_interval: int = Field(default=30, ge=5, le=300)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.validate_settings()
    
    def validate_settings(self):
        """Validate settings and create necessary directories."""
        # Create temp audio directory
        self.audio.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Validate environment
        if self.environment not in ["development", "production", "testing"]:
            raise ValueError("Environment must be one of: development, production, testing")
    
    @property
    def log_level(self) -> str:
        """Get the logging level."""
        return self.logging.level
    
    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"


# Global settings instance
settings = Settings()
logging_config = settings.logging


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


def reload_settings() -> Settings:
    """Reload settings from environment."""
    global settings
    settings = Settings()
    return settings
