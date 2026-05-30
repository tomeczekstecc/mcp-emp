"""Application settings — loaded once from environment / .env file.

All keys are prefixed with MCP_EMP_ (see docs/09-configuration.md).
"""

from __future__ import annotations

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Validated configuration for mcp-emp."""

    model_config = SettingsConfigDict(
        env_prefix="MCP_EMP_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # EMP backend
    api_base_url: str = "http://localhost:480/api"

    # Keycloak
    kc_base_url: str = "https://auth-lsi2021-dev.slaskie.pl/auth"
    kc_realm: str = "eMP"
    kc_client_id: str = "eMP-REST-API"
    kc_client_secret: SecretStr = SecretStr("")
    kc_username: str = ""
    kc_password: SecretStr = SecretStr("")
    kc_unit: str = ""   # fallback when KC token lacks unit claim
    kc_team: str = ""   # fallback when KC token lacks team claim

    # Runtime
    transport: str = "stdio"  # "stdio" | "http"
    sse_host: str = "127.0.0.1"
    sse_port: int = 8765
    log_level: str = "INFO"
    read_only: bool = False

    # Cache TTLs (seconds)
    task_type_ttl: int = 600   # 10 minutes
    tag_ttl: int = 300          # 5 minutes

    # MCP API-key auth (for HTTP transport)
    auth_enabled: bool = False
    auth_db_path: str = "~/.mcp_emp/auth.db"

    # Task templates
    templates_db_path: str = "~/.mcp_emp/templates.db"

    # Direct EMP DB access (for backdate_task tool)
    db_enabled: bool = False   # set True to enable backdate_task
    db_host: str = ""          # e.g. https://emp-db.slaskie.pl (scheme stripped)
    db_port: int = 5432
    db_user: str = ""
    db_pass: SecretStr = SecretStr("")
    db_database: str = ""


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return the process-wide Settings singleton."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def _set_settings(s: Settings | None) -> None:
    """Override the singleton — for testing only."""
    global _settings
    _settings = s
