import csv
import os
from datetime import UTC, datetime


TRADES_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "trades.csv")
TRADE_COLUMNS = [
    "timestamp",
    "symbol",
    "action",
    "usdt_amount",
    "qty",
    "price",
    "signal",
    "result",
    "pnl_usdt",
    "pnl_pct",
    "note",
]


def _ensure_header():
    if not os.path.exists(TRADES_FILE) or os.path.getsize(TRADES_FILE) == 0:
        with open(TRADES_FILE, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(TRADE_COLUMNS)


def log_trade(
    symbol: str,
    action: str,
    usdt_amount: float,
    qty: float,
    price: float,
    signal: str,
    result: str,
    pnl_usdt: float = 0.0,
    pnl_pct: float = 0.0,
    note: str = "",
):
    _ensure_header()
    row = [
        datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S"),
        symbol,
        action,
        round(usdt_amount, 8),
        round(qty, 12),
        round(price, 10),
        signal,
        result,
        round(pnl_usdt, 8),
        round(pnl_pct, 6),
        note,
    ]
    with open(TRADES_FILE, "a", newline="", encoding="utf-8") as f:
        csv.writer(f).writerow(row)


def read_trades(limit: int = 200) -> list[dict]:
    if not os.path.exists(TRADES_FILE):
        return []
    with open(TRADES_FILE, "r", newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[-limit:][::-1]
