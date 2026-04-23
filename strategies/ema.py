"""Strategy 4: EMA Cross — пересечение быстрой и медленной EMA."""
import pandas as pd


def signal(df: pd.DataFrame, fast: int = 9, slow: int = 21) -> str:
    close = df["close"]
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()
    prev = ema_fast.iloc[-2] - ema_slow.iloc[-2]
    curr = ema_fast.iloc[-1] - ema_slow.iloc[-1]
    if pd.isna(prev) or pd.isna(curr):
        return "HOLD"
    if prev < 0 and curr > 0:
        return "BUY"
    if prev > 0 and curr < 0:
        return "SELL"
    return "HOLD"
