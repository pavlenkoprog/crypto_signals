import pandas as pd
import requests


BYBIT_URL = "https://api.bybit.com/v5/market/kline"


def fetch_ohlcv(symbol: str, interval: str, limit: int) -> pd.DataFrame:
    params = {
        "category": "spot",
        "symbol": symbol,
        "interval": interval,
        "limit": limit,
    }
    resp = requests.get(BYBIT_URL, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    if data.get("retCode") != 0:
        raise ValueError(f"Bybit error for {symbol}: {data.get('retMsg')}")

    rows = data["result"]["list"]
    df = pd.DataFrame(rows, columns=["timestamp", "open", "high", "low", "close", "volume", "turnover"])
    df = df.astype(
        {
            "timestamp": "int64",
            "open": "float64",
            "high": "float64",
            "low": "float64",
            "close": "float64",
            "volume": "float64",
        }
    )
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df
