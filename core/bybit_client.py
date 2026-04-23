import hashlib
import hmac
import json
import time
from typing import Any

import requests


class BybitClient:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = "https://api-testnet.bybit.com" if testnet else "https://api.bybit.com"

    def _sign(self, timestamp: str, recv_window: str, payload: str) -> str:
        raw = f"{timestamp}{self.api_key}{recv_window}{payload}"
        return hmac.new(self.api_secret.encode("utf-8"), raw.encode("utf-8"), hashlib.sha256).hexdigest()

    def _request(self, method: str, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        timestamp = str(int(time.time() * 1000))
        recv_window = "10000"

        if method.upper() == "GET":
            body = "&".join([f"{k}={payload[k]}" for k in sorted(payload.keys())])
            url = f"{self.base_url}{path}"
            params = payload
            data = None
        else:
            body = json.dumps(payload, separators=(",", ":"))
            url = f"{self.base_url}{path}"
            params = None
            data = body

        signature = self._sign(timestamp, recv_window, body)
        headers = {
            "X-BAPI-API-KEY": self.api_key,
            "X-BAPI-SIGN": signature,
            "X-BAPI-SIGN-TYPE": "2",
            "X-BAPI-TIMESTAMP": timestamp,
            "X-BAPI-RECV-WINDOW": recv_window,
            "Content-Type": "application/json",
        }
        resp = requests.request(method=method, url=url, headers=headers, params=params, data=data, timeout=15)
        resp.raise_for_status()
        result = resp.json()
        if result.get("retCode") != 0:
            raise ValueError(f"Bybit error: {result.get('retCode')} {result.get('retMsg')}")
        return result

    def place_market_buy_by_quote(self, symbol: str, usdt_amount: float) -> dict[str, Any]:
        payload = {
            "category": "spot",
            "symbol": symbol,
            "side": "Buy",
            "orderType": "Market",
            "qty": f"{usdt_amount:.8f}",
            "marketUnit": "quoteCoin",
        }
        return self._request("POST", "/v5/order/create", payload)

    def place_market_sell_by_base(self, symbol: str, qty: float) -> dict[str, Any]:
        payload = {
            "category": "spot",
            "symbol": symbol,
            "side": "Sell",
            "orderType": "Market",
            "qty": f"{qty:.12f}",
            "marketUnit": "baseCoin",
        }
        return self._request("POST", "/v5/order/create", payload)

    def get_usdt_balance(self) -> float:
        payload = {"accountType": "UNIFIED", "coin": "USDT"}
        result = self._request("GET", "/v5/account/wallet-balance", payload)
        accounts = result.get("result", {}).get("list", [])
        if not accounts:
            return 0.0
        coins = accounts[0].get("coin", [])
        for coin in coins:
            if coin.get("coin") == "USDT":
                return float(coin.get("walletBalance", "0"))
        return 0.0
