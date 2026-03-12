"""
Configuration management using environment variables with validation
"""
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    # API Server
    API_HOST: str = Field(default="0.0.0.0", description="API host")
    API_PORT: int = Field(default=8001, description="API port")
    API_WORKERS: int = Field(default=4, description="Number of workers")
    API_RELOAD: bool = Field(default=False, description="Auto-reload on changes")
    
    # CORS
    CORS_ORIGINS: str = Field(default="http://localhost:3000,https://charming-monstera-eab521.netlify.app", description="Allowed origins")
    
    # Data Paths
    DATA_DIR: str = Field(default="../data", description="Data directory")
    CACHE_DIR: str = Field(default="../data/airport_cache_v2", description="Cache directory")
    BUILDINGS_DIR: str = Field(default="../data/buildings", description="Buildings directory")
    
    # Rate Limiting
    RATE_LIMIT_ENABLED: bool = Field(default=True, description="Enable rate limiting")
    RATE_LIMIT_REQUESTS: int = Field(default=100, description="Requests per window")
    RATE_LIMIT_WINDOW: int = Field(default=60, description="Time window in seconds")
    
    # Logging
    LOG_LEVEL: str = Field(default="INFO", description="Log level")
    LOG_FILE: str = Field(default="../logs/api.log", description="Log file path")
    
    # Performance
    MAX_BUILDINGS_RETURN: int = Field(default=500, description="Max buildings in response")
    CACHE_TTL: int = Field(default=3600, description="Cache TTL in seconds")
    
    # Security
    API_KEY_REQUIRED: bool = Field(default=False, description="Require API key")
    API_KEY: str = Field(default="", description="API key for authentication")
    
    @validator('CORS_ORIGINS')
    def parse_cors_origins(cls, v):
        return [origin.strip() for origin in v.split(',')]
    
    @property
    def data_path(self) -> Path:
        return Path(__file__).parent.parent / self.DATA_DIR
    
    @property
    def cache_path(self) -> Path:
        return Path(__file__).parent.parent / self.CACHE_DIR
    
    @property
    def buildings_path(self) -> Path:
        return Path(__file__).parent.parent / self.BUILDINGS_DIR
    
    @property
    def log_path(self) -> Path:
        return Path(__file__).parent.parent / self.LOG_FILE
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
