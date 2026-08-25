import os
from pydantic_settings import BaseSettings
from pydantic import field_validator, ConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "RecoverAI — Autonomous Revenue Recovery Agent"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"
    LOG_LEVEL: str = "info"
    BACKEND_PORT: int = 8000
    
    # Recovery Engine & Policy Configuration (Configurable Guardrails)
    MAX_RETRY_ATTEMPTS: int = 3
    HIGH_VALUE_THRESHOLD: float = 50000.0
    RETRY_DELAY_HOURS: int = 24

    # Phase 3 LLM Engine Configuration
    DECISION_ENGINE_TYPE: str = "llm"     # "llm" or "rule_based"
    LLM_PROVIDER: str = "mock"            # Default: "mock" (offline testable)
    LLM_API_KEY: str | None = None        # Optional OpenAI API Key
    LLM_MODEL_NAME: str = "gpt-4o-mini"
    LLM_TIMEOUT_SECONDS: float = 5.0
    LLM_TEMPERATURE: float = 0.1
    LLM_MIN_CONFIDENCE: float = 0.60
    LLM_ENABLE_FALLBACK: bool = True
    
    # PostgreSQL Configuration
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres_password_placeholder"
    POSTGRES_DB: str = "recoverai_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str = "postgresql+psycopg://postgres:postgres_password_placeholder@localhost:5432/recoverai_db"
    DATABASE_URL_TEST: str = "postgresql+psycopg://postgres:postgres_password_placeholder@localhost:5432/recoverai_test_db"

    @field_validator("DATABASE_URL", mode="before")
    def assemble_db_connection(cls, v: str | None) -> str:
        if isinstance(v, str):
            if v.startswith("postgresql://"):
                return v.replace("postgresql://", "postgresql+psycopg://", 1)
            return v
        return "postgresql+psycopg://postgres:postgres_password_placeholder@localhost:5432/recoverai_db"

    @field_validator("DATABASE_URL_TEST", mode="before")
    def assemble_test_db_connection(cls, v: str | None) -> str:
        if isinstance(v, str):
            if v.startswith("postgresql://"):
                return v.replace("postgresql://", "postgresql+psycopg://", 1)
            return v
        return "postgresql+psycopg://postgres:postgres_password_placeholder@localhost:5432/recoverai_test_db"

    model_config = ConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
