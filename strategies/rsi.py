"""Strategy 1: RSI — покупка при перепроданности, продажа при перекупленности."""
import pandas as pd


def rsi(closes: pd.Series, period: int = 14) -> pd.Series:
    delta = closes.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss.replace(0, float("nan"))
    return 100 - 100 / (1 + rs)


def signal(df: pd.DataFrame, period: int = 14, buy_level: float = 30, sell_level: float = 70) -> str:
    r = rsi(df["close"], period=period).iloc[-1]
    if pd.isna(r):
        return "HOLD"
    if r < buy_level:
        return "BUY"
    if r > sell_level:
        return "SELL"
    return "HOLD"
