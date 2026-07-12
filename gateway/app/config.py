"""Application configuration from environment variables."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Support repo-root .env (docker-compose) and gateway/.env (local dev)
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Robinhood Crypto Trading API credentials (never expose to Bankr)
    rh_api_key: str = Field(default="", alias="RH_API_KEY")
    rh_private_key_base64: str = Field(default="", alias="RH_PRIVATE_KEY_BASE64")
    rh_base_url: str = Field(
        default="https://trading.robinhood.com", alias="RH_BASE_URL"
    )

    # Legacy single-tenant Bearer token (optional)
    rh_wallet_api_key: str = Field(default="", alias="RH_WALLET_API_KEY")

    # Optional shared secret for public stateless gateway (users set RH_GATEWAY_SECRET in Bankr)
    gateway_shared_secret: str = Field(default="", alias="GATEWAY_SHARED_SECRET")

    # Experimental: store user RH keys in DB via /connect (disabled by default)
    enable_connect_storage: bool = Field(default=False, alias="ENABLE_CONNECT_STORAGE")

    # Multi-tenant vault (only used when ENABLE_CONNECT_STORAGE=true)
    master_encryption_key: str = Field(default="", alias="MASTER_ENCRYPTION_KEY")
    database_url: str = Field(default="", alias="DATABASE_URL")
    public_base_url: str = Field(default="", alias="PUBLIC_BASE_URL")

    # Robinhood Agentic OAuth (stocks/options MCP proxy)
    # Pre-register a client with Robinhood, or leave blank to attempt dynamic registration.
    agentic_client_id: str = Field(default="", alias="AGENTIC_CLIENT_ID")
    agentic_client_secret: str = Field(default="", alias="AGENTIC_CLIENT_SECRET")
    # HMAC key for signing OAuth state parameter (stateless PKCE)
    agentic_state_secret: str = Field(default="", alias="AGENTIC_STATE_SECRET")
    # Service token for validating agentic tickers in public catalog (get_equity_quotes)
    agentic_catalog_token: str = Field(default="", alias="AGENTIC_CATALOG_TOKEN")

    # Safety
    max_order_usd: float = Field(default=50.0, alias="MAX_ORDER_USD")
    require_confirmation: bool = Field(default=True, alias="REQUIRE_CONFIRMATION")

    # Server
    port: int = Field(default=8080, alias="PORT")
    log_level: str = Field(default="info", alias="LOG_LEVEL")

    def has_rh_credentials(self) -> bool:
        return bool(self.rh_api_key and self.rh_private_key_base64)

    def has_gateway_auth(self) -> bool:
        return bool(self.rh_wallet_api_key)

    def has_gateway_shared_secret(self) -> bool:
        return bool(self.gateway_shared_secret)

    def has_master_key(self) -> bool:
        return bool(self.master_encryption_key)

    def is_multi_tenant(self) -> bool:
        return self.enable_connect_storage and self.has_master_key()

    def effective_public_url(self, request_base_url: str = "") -> str:
        if self.public_base_url:
            return self.public_base_url.rstrip("/")
        return request_base_url.rstrip("/")


def get_settings() -> Settings:
    return Settings()
