from __future__ import annotations

from pathlib import Path
from typing import Optional

from pydantic import Field, HttpUrl, computed_field
from pydantic_settings import BaseSettings


class PostgresSettings(BaseSettings):
    enabled: bool = Field(True, description="Toggle for Postgres connectivity checks")
    dsn: Optional[str] = Field(
        default=None,
        alias="POSTGRES_DSN",
        description="PostgreSQL connection string",
    )
    connect_timeout_seconds: float = Field(2.0, ge=0.1)

    model_config = {
        "env_prefix": "OCTOBATCH_",
        "extra": "ignore",
    }


class RedisSettings(BaseSettings):
    enabled: bool = Field(True, description="Toggle for Redis connectivity checks")
    url: Optional[str] = Field(
        default=None,
        alias="REDIS_URL",
        description="Redis connection URL",
    )
    ping_timeout_seconds: float = Field(2.0, ge=0.1)

    model_config = {
        "env_prefix": "OCTOBATCH_",
        "extra": "ignore",
    }


class BlobstoreSettings(BaseSettings):
    enabled: bool = Field(True, description="Toggle for S3-compatible connectivity checks")
    endpoint_url: Optional[str] = Field(
        default=None,
        alias="BLOBSTORE_ENDPOINT",
        description="Endpoint for the S3-compatible service",
    )
    bucket: Optional[str] = Field(
        default=None,
        alias="BLOBSTORE_BUCKET",
        description="Bucket used for Octobatch artifacts",
    )
    region_name: str = Field("us-east-1")
    access_key_id: Optional[str] = Field(default=None, alias="BLOBSTORE_ACCESS_KEY_ID")
    secret_access_key: Optional[str] = Field(
        default=None, alias="BLOBSTORE_SECRET_ACCESS_KEY"
    )
    session_token: Optional[str] = Field(default=None, alias="BLOBSTORE_SESSION_TOKEN")
    healthcheck_object_key: str = Field(
        ".octobatch-healthcheck",
        description="Object key used for head_bucket or simple get operations",
    )

    model_config = {
        "env_prefix": "OCTOBATCH_",
        "extra": "ignore",
    }


class GitHubAppSettings(BaseSettings):
    api_base_url: HttpUrl = Field(
        "https://api.github.com", alias="GITHUB_API_BASE_URL"
    )
    app_id: Optional[int] = Field(default=None, alias="GITHUB_APP_ID")
    webhook_secret: Optional[str] = Field(default=None, alias="GITHUB_WEBHOOK_SECRET")
    private_key: Optional[str] = Field(default=None, alias="GITHUB_APP_PRIVATE_KEY")
    private_key_path: Optional[Path] = Field(
        default=None, alias="GITHUB_APP_PRIVATE_KEY_PATH"
    )
    token_skew_seconds: int = Field(
        60,
        ge=0,
        description="Seconds to subtract from token expiry when caching installation tokens",
    )

    model_config = {
        "env_prefix": "OCTOBATCH_",
        "extra": "ignore",
    }

    @computed_field
    def audience(self) -> str:
        return str(self.api_base_url).rstrip("/")

    def load_private_key_pem(self) -> str:
        if self.private_key:
            return self.private_key
        if self.private_key_path:
            return self.private_key_path.read_text()
        raise ValueError("GitHub App private key not configured")


class ServiceSettings(BaseSettings):
    service_name: str = Field("octobatch-service", alias="SERVICE_NAME")
    environment: str = Field("dev", alias="ENVIRONMENT")
    postgres: PostgresSettings = Field(default_factory=PostgresSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    blobstore: BlobstoreSettings = Field(default_factory=BlobstoreSettings)
    github: GitHubAppSettings = Field(default_factory=GitHubAppSettings)
    healthcheck_timeout_seconds: float = Field(5.0, ge=1.0)

    model_config = {
        "env_prefix": "OCTOBATCH_",
        "extra": "ignore",
    }
