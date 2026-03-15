from __future__ import annotations

import json
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "dvdrental"

    # App
    PROJECT_NAME: str = "DVDRental GraphQL API"
    DEBUG: bool = False
    ALLOWED_ORIGINS: list[str] = ["*"]
    GRAPHQL_PATH: str = "/graphql"

    # Keycloak
    KEYCLOAK_ISSUER: str = "http://localhost:8090/realms/dvd-rental"
    KEYCLOAK_JWKS_URL: str = (
        "http://localhost:8090/realms/dvd-rental/protocol/openid-connect/certs"
    )
    KEYCLOAK_CLIENT_ID: str = "dvd-rental-api"

    @property
    def async_database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return json.loads(v)
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
