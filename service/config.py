"""Runtime configuration loaded from environment variables.

All settings are env-driven with sensible defaults. The technical brief
specifies localhost:8765 as the default bind; everything else is local.
"""

from __future__ import annotations

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Service-wide runtime configuration."""

    model_config = SettingsConfigDict(
        env_prefix="SKYBRAIN_QVAC_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    host: str = Field(default="127.0.0.1", description="Bind address. Default: loopback only.")
    port: int = Field(default=8765, ge=1, gt=0, description="HTTP port.")

    audit_dir: Path = Field(
        default=Path("./audit"),
        description="Directory where audit JSON Lines logs are written.",
    )

    model_store_dir: Path = Field(
        default=Path("./bci_models"),
        description="Where trained BCI models are stored (deferred to Phase 1 week 5-6).",
    )

    default_analysis_profile: str = Field(
        default="skybrain_4ch",
        description="SkyBrain SDK analysis profile when the request doesn't specify one.",
    )

    require_sdk: bool = Field(
        default=True,
        description=(
            "When True, raise on startup if skybrain_sdk is not importable. "
            "Set False for docs-only deployments (CI, doc build)."
        ),
    )


def get_settings() -> Settings:
    """Cached settings accessor for FastAPI dependency injection."""
    return Settings()
