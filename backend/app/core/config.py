from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(ENV_PATH)


class Settings(BaseSettings):
    APP_NAME: str = "Brand Reputation Intelligence Platform"
    PROJECT_NAME: str = "Brand Reputation Intelligence Platform API"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    WORKERS: int = 4
    RELOAD: bool = True
    
    DATABASE_URL: str = "postgresql+asyncpg://postgres:@localhost:5432/brand_reputation"
    SYNC_DATABASE_URL: str = "postgresql+psycopg://postgres:@localhost:5432/brand_reputation"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_ECHO: bool = False
    
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    OPENAI_API_KEY: Optional[str] = None
    REDDIT_CLIENT_ID: Optional[str] = None
    REDDIT_CLIENT_SECRET: Optional[str] = None
    REDDIT_USER_AGENT: str = "BrandReputation/1.0"
    TWITTER_BEARER_TOKEN: Optional[str] = None
    
    SENTIMENT_MODEL: str = "distilbert-base-uncased-finetuned-sst-2-english"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    
    SPIKE_THRESHOLD_MULTIPLIER: float = 3.0
    COLLECTION_INTERVAL_MINUTES: int = 15
    
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000", 
        "http://127.0.0.1:3000"
    ]
    
    CORS_ALLOW_METHODS: list[str] = [
        "GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"
    ]
    
    CORS_ALLOW_HEADERS: list[str] = [
        "Authorization", "Content-Type", "Accept", "Origin",
        "X-Requested-With", "X-CSRF-Token", "X-API-Key", "X-Request-ID"
    ]
    
    CORS_EXPOSE_HEADERS: list[str] = [
        "Content-Range", "X-Content-Range", "X-Total-Count", "X-Request-ID"
    ]
    
    CORS_MAX_AGE: int = 600
    
    SECRET_KEY: str = "your-super-secret-key-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    API_V1_STR: str = "/api/v1"
    
    RATE_LIMIT_PER_MINUTE: int = 1000
    RATE_LIMIT_PER_HOUR: int = 10000
    
    LOG_LEVEL: str = "INFO"
    
    HEALTH_CHECK_TIMEOUT: int = 30
    HEALTH_CHECK_INTERVAL: int = 60

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def cors_origins(self) -> list[str]:
        return self.CORS_ORIGINS
    
    @property
    def reload_enabled(self) -> bool:
        return self.is_development
    
    @property
    def log_config(self) -> dict[str, object]:
        return {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                }
            },
            "handlers": {
                "default": {
                    "level": self.LOG_LEVEL,
                    "formatter": "standard",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {
                "": {
                    "handlers": ["default"],
                    "level": self.LOG_LEVEL,
                    "propagate": False
                }
            }
        }

    class Config:
        env_file = str(ENV_PATH)
        case_sensitive = True
        extra = "ignore"


settings = Settings()