from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    APP_NAME: str = "THERMALIFT"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"
    
    DATABASE_URL: str = "sqlite:///./thermalift.db"
    
    SYNTHETIC_DATA_SEED: int = 42
    DEMO_MODE: bool = True
    
    # CORS_ORIGINS can be set via env var as comma-separated string
    # e.g., CORS_ORIGINS="https://frontend.netlify.app,http://localhost:5173"
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS from env var if set, otherwise use default list."""
        env_origins = os.getenv("CORS_ORIGINS")
        if env_origins:
            return [origin.strip() for origin in env_origins.split(",")]
        return self.CORS_ORIGINS


settings = Settings()