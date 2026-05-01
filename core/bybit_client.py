import hashlib
import hmac
import json
import logging
import time
from typing import Any

import requests

# Настройка логирования ошибок округления
logger = logging.getLogger(__name__)
handler = logging.FileHandler('/root/projects/crypto_signals_auto_trade/bybit_errors.log')
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
logger.setLevel(logging.WARNING)


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
            error_msg = f"Bybit error: {result.get('retCode')} {result.get('retMsg')}"
            # Логируем ошибки округления
            if result.get("retCode") in [170137, 170148]:
                logger.error(f"{error_msg} | Payload: {payload}")
            raise ValueError(error_msg)
        return result

    def get_symbol_precision(self, symbol: str) -> dict[str, Any]:
        """Получить правила округления для символа"""
        url = f"{self.base_url}/v5/market/instruments-info"
        params = {"category": "spot", "symbol": symbol}
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if data.get("retCode") != 0:
            raise Exception(f"Bybit error: {data.get('retCode')} {data.get('retMsg')}")

        items = data.get("result", {}).get("list", [])
        if not items:
            raise Exception(f"Symbol {symbol} not found")

        lot_filter = items[0].get("lotSizeFilter", {})
        return {
            "basePrecision": float(lot_filter.get("basePrecision", "0.01")),
            "quotePrecision": float(lot_filter.get("quotePrecision", "0.01")),
            "minOrderQty": float(lot_filter.get("minOrderQty", "0.01")),
            "maxOrderQty": float(lot_filter.get("maxOrderQty", "1000000")),
        }

    def round_qty(self, symbol: str, qty: float) -> str:
        """Округлить количество по правилам биржи (basePrecision)"""
        precision = self.get_symbol_precision(symbol)
        base_precision = precision["basePrecision"]

        # Округляем до нужного шага
        rounded = round(qty / base_precision) * base_precision

        # Используем максимум 5 знаков для надежности
        if base_precision >= 1:
            decimals = 0
        else:
            decimals = min(5, len(str(base_precision).rstrip('0').split('.')[-1]))

        return f"{rounded:.{decimals}f}"

    def round_quote_amount(self, symbol: str, usdt_amount: float) -> str:
        """Округлить сумму в USDT по правилам биржи (quotePrecision)"""
        precision = self.get_symbol_precision(symbol)
        quote_precision = precision["quotePrecision"]

        # Округляем до нужного шага
        rounded = round(usdt_amount / quote_precision) * quote_precision

        # Используем максимум 5 знаков для надежности
        if quote_precision >= 1:
            decimals = 0
        else:
            decimals = min(5, len(str(quote_precision).rstrip('0').split('.')[-1]))

        return f"{rounded:.{decimals}f}"

    def place_market_buy_by_quote(self, symbol: str, usdt_amount: float) -> dict[str, Any]:
        # Округляем сумму в USDT по правилам биржи
        rounded_amount = self.round_quote_amount(symbol, usdt_amount)

        payload = {
            "category": "spot",
            "symbol": symbol,
            "side": "Buy",
            "orderType": "Market",
            "qty": rounded_amount,
            "marketUnit": "quoteCoin",
        }
        return self._request("POST", "/v5/order/create", payload)

    def place_market_sell_by_base(self, symbol: str, qty: float) -> dict[str, Any]:
        # Округляем количество по правилам биржи
        rounded_qty = self.round_qty(symbol, qty)

        payload = {
            "category": "spot",
            "symbol": symbol,
            "side": "Sell",
            "orderType": "Market",
            "qty": rounded_qty,
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

    def get_coin_balance(self, symbol: str) -> float:
        """Получить реальный баланс монеты на бирже (например, RENDERUSDT -> RENDER)"""
        coin = symbol.replace("USDT", "")
        payload = {"accountType": "UNIFIED"}
        result = self._request("GET", "/v5/account/wallet-balance", payload)
        accounts = result.get("result", {}).get("list", [])
        if not accounts:
            return 0.0
        coins = accounts[0].get("coin", [])
        for c in coins:
            if c.get("coin") == coin:
                balance = c.get("walletBalance", "0")
                return float(balance) if balance else 0.0
        return 0.0
