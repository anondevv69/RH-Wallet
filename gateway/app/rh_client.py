"""Robinhood Crypto Trading API v2 client with Ed25519 signing."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlencode

from dataclasses import dataclass

import httpx

from app.signing import authorization_headers, serialize_body

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RHCredentials:
    api_key: str
    private_key_base64: str
    base_url: str = "https://trading.robinhood.com"


class RobinhoodAPIError(Exception):
    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        payload: Any = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class RobinhoodClient:
    """Thin signed proxy to https://trading.robinhood.com (API v2)."""

    def __init__(self, credentials: RHCredentials, timeout: float = 15.0) -> None:
        if not credentials.api_key or not credentials.private_key_base64:
            raise ValueError(
                "Robinhood credentials missing. Set RH_API_KEY and RH_PRIVATE_KEY_BASE64."
            )
        self.credentials = credentials
        self.base_url = credentials.base_url.rstrip("/")
        self._timeout = timeout
        self._account_number: Optional[str] = None
        self._client = httpx.Client(timeout=timeout)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> RobinhoodClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Low-level HTTP
    # ------------------------------------------------------------------

    def request(
        self,
        method: str,
        path: str,
        body: Optional[dict[str, Any]] = None,
        *,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Signed request. ``path`` must include the leading ``/api/...`` and any query string."""
        if params:
            qs = self._build_query(params)
            path = f"{path}{qs}" if "?" not in path else f"{path}&{qs.lstrip('?')}"

        body_str = serialize_body(body) if body else ""
        timestamp = int(datetime.now(tz=timezone.utc).timestamp())
        headers = authorization_headers(
            self.credentials.api_key,
            self.credentials.private_key_base64,
            timestamp,
            path,
            method.upper(),
            body_str,
        )
        headers["Content-Type"] = "application/json; charset=utf-8"
        headers["Accept"] = "application/json"

        url = f"{self.base_url}{path}"
        try:
            if method.upper() == "GET":
                response = self._client.get(url, headers=headers)
            elif method.upper() == "POST":
                # Send the exact JSON string we signed (json.dumps default).
                response = self._client.post(
                    url,
                    headers=headers,
                    content=body_str.encode("utf-8") if body_str else None,
                )
            else:
                raise ValueError(f"Unsupported method: {method}")
        except httpx.RequestError as exc:
            logger.error("Robinhood request failed: %s", type(exc).__name__)
            raise RobinhoodAPIError(f"Request failed: {exc}") from exc

        return self._parse_response(response)

    @staticmethod
    def _build_query(params: dict[str, Any]) -> str:
        pairs: list[tuple[str, str]] = []
        for key, value in params.items():
            if value is None:
                continue
            if isinstance(value, (list, tuple)):
                for item in value:
                    pairs.append((key, str(item)))
            else:
                pairs.append((key, str(value)))
        if not pairs:
            return ""
        return "?" + urlencode(pairs)

    @staticmethod
    def _parse_response(response: httpx.Response) -> Any:
        try:
            payload = response.json()
        except ValueError:
            payload = {"error": response.text or response.reason_phrase}

        if response.status_code >= 400:
            raise RobinhoodAPIError(
                f"HTTP {response.status_code}",
                status_code=response.status_code,
                payload=payload,
            )
        return payload

    def paginate(
        self,
        method: str,
        path: str,
        *,
        params: Optional[dict[str, Any]] = None,
        max_pages: int = 20,
    ) -> list[Any]:
        """Follow ``next`` cursors and return concatenated ``results``."""
        all_results: list[Any] = []
        response = self.request(method, path, params=params)
        pages = 0
        while response and pages < max_pages:
            results = response.get("results") if isinstance(response, dict) else None
            if isinstance(results, list):
                all_results.extend(results)
            next_url = response.get("next") if isinstance(response, dict) else None
            if not next_url:
                break
            next_path = next_url.replace(self.base_url, "")
            response = self.request("GET", next_path)
            pages += 1
        return all_results

    # ------------------------------------------------------------------
    # Account helpers
    # ------------------------------------------------------------------

    def get_accounts(self) -> Any:
        return self.request("GET", "/api/v2/crypto/trading/accounts/")

    def get_primary_account_number(self, *, force_refresh: bool = False) -> str:
        if self._account_number and not force_refresh:
            return self._account_number
        data = self.get_accounts()
        results = data.get("results") if isinstance(data, dict) else None
        if not results:
            # Some responses may be a bare account object
            if isinstance(data, dict) and data.get("account_number"):
                self._account_number = str(data["account_number"])
                return self._account_number
            raise RobinhoodAPIError("No crypto trading accounts found.")
        account_number = results[0].get("account_number")
        if not account_number:
            raise RobinhoodAPIError("Account response missing account_number.")
        self._account_number = str(account_number)
        return self._account_number

    def get_account_summary(self) -> dict[str, Any]:
        data = self.get_accounts()
        results = data.get("results") if isinstance(data, dict) else None
        if results:
            primary = results[0]
            self._account_number = str(primary.get("account_number", "")) or None
            return {
                "account_number": primary.get("account_number"),
                "status": primary.get("status"),
                "buying_power": primary.get("buying_power"),
                "buying_power_currency": primary.get("buying_power_currency"),
                "fee_tier": primary.get("fee_tier"),
                "accounts": results,
            }
        if isinstance(data, dict) and data.get("account_number"):
            self._account_number = str(data["account_number"])
            return data
        return {"raw": data}

    def get_holdings(
        self,
        *asset_codes: str,
        account_number: Optional[str] = None,
    ) -> Any:
        account = account_number or self.get_primary_account_number()
        params: dict[str, Any] = {"account_number": account}
        if asset_codes:
            params["asset_code"] = [c.upper() for c in asset_codes]
        return self.request(
            "GET", "/api/v2/crypto/trading/holdings/", params=params
        )

    # ------------------------------------------------------------------
    # Market data
    # ------------------------------------------------------------------

    def get_trading_pairs(self, *symbols: str) -> list[Any]:
        params: dict[str, Any] = {}
        if symbols:
            params["symbol"] = [s.upper() for s in symbols]
        return self.paginate(
            "GET", "/api/v2/crypto/trading/trading_pairs/", params=params or None
        )

    def get_best_bid_ask(self, *symbols: str) -> Any:
        params: dict[str, Any] = {}
        if symbols:
            params["symbol"] = [s.upper() for s in symbols]
        return self.request(
            "GET",
            "/api/v2/crypto/marketdata/best_bid_ask/",
            params=params or None,
        )

    def get_estimated_price(
        self, symbol: str, side: str, quantity: str
    ) -> Any:
        params = {
            "symbol": symbol.upper(),
            "side": side.lower(),
            "quantity": quantity,
        }
        return self.request(
            "GET",
            "/api/v2/crypto/trading/estimated_price/",
            params=params,
        )

    # ------------------------------------------------------------------
    # Orders
    # ------------------------------------------------------------------

    def get_orders(
        self,
        account_number: Optional[str] = None,
        *,
        created_at_start: Optional[str] = None,
        symbol: Optional[str] = None,
        side: Optional[str] = None,
        state: Optional[str] = None,
        order_type: Optional[str] = None,
    ) -> Any:
        account = account_number or self.get_primary_account_number()
        params: dict[str, Any] = {
            "account_number": account,
            "created_at_start": created_at_start or "2020-01-01T00:00:00Z",
        }
        if symbol:
            params["symbol"] = symbol.upper()
        if side:
            params["side"] = side.lower()
        if state:
            params["state"] = state.lower()
        if order_type:
            params["type"] = order_type.lower()
        return self.request(
            "GET", "/api/v2/crypto/trading/orders/", params=params
        )

    def get_order(
        self, order_id: str, account_number: Optional[str] = None
    ) -> Any:
        account = account_number or self.get_primary_account_number()
        path = f"/api/v2/crypto/trading/orders/{order_id}/"
        return self.request(
            "GET", path, params={"account_number": account}
        )

    def place_market_order(
        self,
        *,
        side: str,
        symbol: str,
        quote_amount: Optional[str] = None,
        asset_quantity: Optional[str] = None,
        client_order_id: Optional[str] = None,
        account_number: Optional[str] = None,
    ) -> Any:
        account = account_number or self.get_primary_account_number()
        order_config: dict[str, str] = {}
        if asset_quantity:
            order_config["asset_quantity"] = str(asset_quantity)
        elif quote_amount:
            # Robinhood API requires asset_quantity; derive it from current ask price
            prices = self.get_best_bid_ask(symbol.upper())
            results = prices.get("results", []) if isinstance(prices, dict) else []
            ask = next(
                (r.get("ask") or r.get("ask_inclusive_of_buy_spread") for r in results if r),
                None,
            )
            if not ask:
                raise ValueError(
                    f"Could not determine ask price for {symbol} to convert quote_amount."
                )
            qty = float(quote_amount) / float(ask)
            order_config["asset_quantity"] = f"{qty:.8f}"
        else:
            raise ValueError("Provide quote_amount or asset_quantity.")

        body = {
            "client_order_id": client_order_id or str(uuid.uuid4()),
            "side": side.lower(),
            "type": "market",
            "symbol": symbol.upper(),
            "market_order_config": order_config,
        }
        return self.request(
            "POST",
            "/api/v2/crypto/trading/orders/",
            body,
            params={"account_number": account},
        )

    def cancel_order(self, order_id: str) -> Any:
        path = f"/api/v2/crypto/trading/orders/{order_id}/cancel/"
        return self.request("POST", path)

    @staticmethod
    def normalize_order(raw: Any) -> dict[str, Any]:
        if not isinstance(raw, dict):
            return {"raw": raw}
        return {
            "id": raw.get("id"),
            "account_number": raw.get("account_number"),
            "symbol": raw.get("symbol"),
            "client_order_id": raw.get("client_order_id"),
            "side": raw.get("side"),
            "type": raw.get("type"),
            "state": raw.get("state"),
            "average_price": raw.get("average_price"),
            "filled_asset_quantity": raw.get("filled_asset_quantity"),
            "fee_charged": raw.get("fee_charged"),
            "estimated_fee_remaining": raw.get("estimated_fee_remaining"),
            "created_at": raw.get("created_at"),
            "updated_at": raw.get("updated_at"),
            "raw": raw,
        }

