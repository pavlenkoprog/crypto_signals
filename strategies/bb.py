"""Strategy 3: Bollinger Bands — прорыв за пределы полос."""
import pandas as pd


def signal(df: pd.DataFrame, period: int = 20, std_dev: float = 2.0) -> str:
    close = df["close"]
    mid = close.rolling(period).mean()
    std = close.rolling(period).std()
    upper = mid + std_dev * std
    lower = mid - std_dev * std
    price = close.iloc[-1]
    if pd.isna(lower.iloc[-1]):
        return "HOLD"
    if price < lower.iloc[-1]:
        return "BUY"
    if price > upper.iloc[-1]:
        return "SELL"
    return "HOLD"
