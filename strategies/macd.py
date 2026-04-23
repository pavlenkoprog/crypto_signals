"""Strategy 2: MACD — пересечение линий сигнала."""
import pandas as pd


def ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def signal(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal_period: int = 9) -> str:
    close = df["close"]
    if fast >= slow:
        return "HOLD"
    macd_line = ema(close, fast) - ema(close, slow)
    signal_line = ema(macd_line, signal_period)
    prev_diff = (macd_line - signal_line).iloc[-2]
    curr_diff = (macd_line - signal_line).iloc[-1]
    if pd.isna(prev_diff) or pd.isna(curr_diff):
        return "HOLD"
    if prev_diff < 0 and curr_diff > 0:
        return "BUY"
    if prev_diff > 0 and curr_diff < 0:
        return "SELL"
    return "HOLD"
