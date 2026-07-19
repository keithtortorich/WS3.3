"""Pydantic Settings configuration.

Every field name mirrors the corresponding variable name in the root
``.env.example`` exactly, so ``Settings()`` can be constructed straight from
the process environment (or a ``.env`` file) with zero remapping.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )

    # --- Application ---
    APP_ENV: str = "development"
    APP_DEBUG: bool = True
    APP_SECRET_KEY: str = "change-me-to-a-random-64-char-string"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000
    APP_BASE_URL: str = "http://localhost:8000"
    FRONTEND_BASE_URL: str = "http://localhost:3000"
    LOG_LEVEL: str = "INFO"

    # --- PostgreSQL ---
    POSTGRES_USER: str = "smm_admin"
    POSTGRES_PASSWORD: str = "smm_dev_password"
    POSTGRES_DB: str = "smm_platform"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql+asyncpg://smm_admin:smm_dev_password@postgres:5432/smm_platform"
    DATABASE_URL_SYNC: str = "postgresql+psycopg://smm_admin:smm_dev_password@postgres:5432/smm_platform"

    # --- Redis / Celery ---
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: str = "redis://redis:6379/0"
    CELERY_BROKER_URL: str = "redis://redis:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://redis:6379/2"

    # --- S3 / MinIO ---
    S3_ENDPOINT_URL: Optional[str] = "http://minio:9000"
    S3_ACCESS_KEY_ID: str = "smm_minio_admin"
    S3_SECRET_ACCESS_KEY: str = "smm_minio_password"
    S3_BUCKET_NAME: str = "smm-media"
    S3_REGION: str = "us-east-1"
    S3_USE_SSL: bool = False
    S3_PUBLIC_URL_BASE: str = "http://localhost:9000/smm-media"

    # --- Clerk ---
    CLERK_SECRET_KEY: str = "sk_test_replace_me"
    CLERK_PUBLISHABLE_KEY: str = "pk_test_replace_me"
    CLERK_JWKS_URL: str = "https://your-instance.clerk.accounts.dev/.well-known/jwks.json"
    CLERK_ISSUER: str = "https://your-instance.clerk.accounts.dev"
    CLERK_AUDIENCE: str = ""
    NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY: str = "pk_test_replace_me"
    CLERK_SIGN_IN_URL: str = "/sign-in"
    CLERK_SIGN_UP_URL: str = "/sign-up"

    # --- AI Provider ---
    AI_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://ollama:11434"
    OLLAMA_DEFAULT_MODEL: str = "llama3.1"
    OLLAMA_TIMEOUT_SECONDS: int = 120
    OPENAI_API_KEY: str = ""
    CLAUDE_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GROK_API_KEY: str = ""
    HERMES_API_KEY: str = ""

    # --- LinkedIn (fully implemented) ---
    LINKEDIN_CLIENT_ID: str = "replace_me"
    LINKEDIN_CLIENT_SECRET: str = "replace_me"
    LINKEDIN_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/linkedin/callback"
    LINKEDIN_API_VERSION: str = "202405"

    # --- Social platform stubs ---
    FACEBOOK_APP_ID: str = ""
    FACEBOOK_APP_SECRET: str = ""
    INSTAGRAM_APP_ID: str = ""
    INSTAGRAM_APP_SECRET: str = ""
    X_API_KEY: str = ""
    X_API_SECRET: str = ""
    THREADS_APP_ID: str = ""
    THREADS_APP_SECRET: str = ""
    TIKTOK_CLIENT_KEY: str = ""
    TIKTOK_CLIENT_SECRET: str = ""
    PINTEREST_APP_ID: str = ""
    PINTEREST_APP_SECRET: str = ""
    YOUTUBE_CLIENT_ID: str = ""
    YOUTUBE_CLIENT_SECRET: str = ""
    GOOGLE_BUSINESS_CLIENT_ID: str = ""
    GOOGLE_BUSINESS_CLIENT_SECRET: str = ""

    # --- Celery / Worker tuning ---
    CELERY_TASK_ALWAYS_EAGER: bool = False
    CELERY_WORKER_CONCURRENCY: int = 4
    PUBLISH_RETRY_MAX_ATTEMPTS: int = 5
    PUBLISH_RETRY_BACKOFF_BASE_SECONDS: int = 30

    # --- CORS ---
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000"

    # --- Testing ---
    TEST_DATABASE_URL: str = "sqlite+aiosqlite:///:memory:"

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.CORS_ALLOWED_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached Settings singleton (avoids re-parsing env on every call)."""
    return Settings()
