"""Pydantic request/response models for the gateway API."""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, model_validator


class PlaceOrderRequest(BaseModel):
    side: Literal["buy", "sell"]
    symbol: str = Field(..., description="Trading pair, e.g. BTC-USD")
    type: Literal["market"] = "market"
    quote_amount: Optional[str] = Field(
        default=None,
        description="USD amount (preferred for buys). Mutually exclusive with asset_quantity.",
    )
    asset_quantity: Optional[str] = Field(
        default=None,
        description="Asset quantity (preferred for sells). Mutually exclusive with quote_amount.",
    )
    confirm: bool = Field(
        default=False,
        description="Must be true when REQUIRE_CONFIRMATION is enabled.",
    )
    client_order_id: Optional[str] = Field(
        default=None,
        description="Optional idempotency UUID; generated if omitted.",
    )

    @model_validator(mode="after")
    def exactly_one_size(self) -> PlaceOrderRequest:
        has_quote = self.quote_amount is not None and self.quote_amount != ""
        has_asset = self.asset_quantity is not None and self.asset_quantity != ""
        if has_quote == has_asset:
            raise ValueError(
                "Provide exactly one of quote_amount or asset_quantity."
            )
        self.symbol = self.symbol.upper()
        return self


class OrderSummary(BaseModel):
    id: Optional[str] = None
    account_number: Optional[str] = None
    symbol: Optional[str] = None
    client_order_id: Optional[str] = None
    side: Optional[str] = None
    type: Optional[str] = None
    state: Optional[str] = None
    average_price: Optional[Any] = None
    filled_asset_quantity: Optional[Any] = None
    fee_charged: Optional[Any] = None
    estimated_fee_remaining: Optional[Any] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    raw: Optional[dict[str, Any]] = None


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[Any] = None
    status_code: Optional[int] = None
