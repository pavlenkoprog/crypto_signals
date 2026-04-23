"""Strategy 5: VWAP — цена выше/ниже взвешенной средней по объёму."""
import pandas as pd


def signal(df: pd.DataFrame, threshold: float = 0.005) -> str:
    typical = (df["high"] + df["low"] + df["close"]) / 3
    vwap = (typical * df["volume"]).cumsum() / df["volume"].cumsum()
    price = df["close"].iloc[-1]
    v = vwap.iloc[-1]
    if pd.isna(v):
        return "HOLD"
    if price > v * (1 + threshold):
        return "BUY"
    if price < v * (1 - threshold):
        return "SELL"
    return "HOLD"
