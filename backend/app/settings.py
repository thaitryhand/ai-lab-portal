from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, PostgresDsn, RedisDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Explicit path to backend/.env (not CWD-dependent, works from any working directory)
_BACKEND_DIR = Path(__file__).resolve().parent.parent
_ENV_FILE = _BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Application settings parsed from environment variables.

    FastAPI app code reads typed settings from this boundary instead of reading
    raw environment variables directly. Pattern follows pydantic-settings
    BaseSettings with SettingsConfigDict env prefix:
    https://docs.pydantic.dev/latest/concepts/pydantic_settings/
    """

    model_config = SettingsConfigDict(
        env_prefix="AI_LAB_",
        # Local dev loads backend/.env by explicit path. Containers and production
        # deploys should rely on process environment variables only.
        env_file=_ENV_FILE if _ENV_FILE.is_file() else None,
        env_ignore_empty=True,
        extra="ignore",
    )

    app_name: str = Field(default="AI Lab Portal API", min_length=1)
    service_name: str = Field(default="ai-lab-portal-api", min_length=1)
    environment: Literal["development", "test", "staging", "production"] = "test"
    database_url: PostgresDsn = Field(
        default="postgresql+psycopg://ai_lab:ai_lab_dev_password@localhost:5432/ai_lab_portal"
    )
    redis_url: RedisDsn = Field(default="redis://localhost:6379/0")
    admin_boundary_secret: SecretStr = Field(
        default="development-admin-boundary-secret-at-least-32-chars",
        min_length=32,
    )
    llm_openai_api_key: SecretStr = Field(default="")
    llm_model: str = Field(default="gpt-4o")
    firecrawl_api_key: SecretStr = Field(default="")


@lru_cache
def get_settings() -> Settings:
    return Settings()
