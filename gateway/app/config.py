"""Application configuration from environment variables."""

from __future__ import annotations

from functools import lru_cache

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

    # Bearer token Bankr / agents use to call this gateway
    rh_wallet_api_key: str = Field(default="", alias="RH_WALLET_API_KEY")

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


@lru_cache
def get_settings() -> Settings:
    return Settings()
