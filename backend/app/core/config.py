from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ─── Application ─────────────────────────────────────────────────────────
    app_env: str = Field(default="development")
    app_host: str = Field(default="0.0.0.0")
    app_port: int = Field(default=8000)
    log_level: str = Field(default="INFO")

    # ─── PostgreSQL ───────────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql+asyncpg://aegisgov:change-me-in-development@localhost:5432/aegisgov"
    )

    # ─── OPA ─────────────────────────────────────────────────────────────────
    opa_url: str = Field(default="http://localhost:8181")
    opa_policy_path: str = Field(default="v1/data/aegis")

    # ─── Keycloak ─────────────────────────────────────────────────────────────
    keycloak_url: str = Field(default="http://localhost:8080")
    keycloak_realm: str = Field(default="aegisgov")
    keycloak_client_id: str = Field(default="aegisgov-backend")
    keycloak_client_secret: str = Field(default="dev-backend-secret")

    # ─── Agent Identity ──────────────────────────────────────────────────────
    agent_jwt_secret: str = Field(default="dev-agent-secret-change-in-production")
    agent_jwt_algorithm: str = Field(default="HS256")

    # ─── LLM (Phase 2+) ──────────────────────────────────────────────────────
    openai_api_key: str = Field(default="")
    llm_model: str = Field(default="gpt-4o")
    llm_temperature: float = Field(default=0.0)

    # ─── Langfuse Observability (Phase 4+) ───────────────────────────────────
    langfuse_public_key: str = Field(default="")
    langfuse_secret_key: str = Field(default="")
    langfuse_host: str = Field(default="https://cloud.langfuse.com")
    langfuse_enabled: bool = Field(default=False)

    # ─── Runtime Governance Limits (CLAUDE.md §7) ────────────────────────────
    max_tool_calls: int = Field(default=8)
    max_execution_time_seconds: int = Field(default=60)
    max_agent_handoffs: int = Field(default=4)
    max_identical_tool_calls: int = Field(default=3)

    @property
    def keycloak_jwks_url(self) -> str:
        return (
            f"{self.keycloak_url}/realms/{self.keycloak_realm}"
            "/protocol/openid-connect/certs"
        )

    @property
    def opa_decision_url(self) -> str:
        return f"{self.opa_url}/{self.opa_policy_path}"


settings = Settings()
