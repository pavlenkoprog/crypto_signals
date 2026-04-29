import csv
import os
from datetime import datetime, timezone


LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "signals.csv")
COLUMNS = ["timestamp", "run_started_at", "symbol", "price", "rsi", "macd", "bb", "ema", "vwap", "consensus"]


def _ensure_header():
    if not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0:
        with open(LOG_FILE, "w", newline="") as f:
            csv.writer(f).writerow(COLUMNS)
        return

    # If columns were changed, rewrite file with the current schema.
    with open(LOG_FILE, "r", newline="") as f:
        reader = csv.reader(f)
        existing_header = next(reader, [])

    if existing_header == COLUMNS:
        return

    with open(LOG_FILE, "r", newline="") as f:
        old_rows = list(csv.DictReader(f))

    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for row in old_rows:
            writer.writerow({col: row.get(col, "") for col in COLUMNS})


def log_signal(symbol: str, price: float, signals: dict, consensus: str, run_started_at: str):
    _ensure_header()
    row = [
        datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        run_started_at,
        symbol,
        round(price, 8),
        signals.get("rsi", "HOLD"),
        signals.get("macd", "HOLD"),
        signals.get("bb", "HOLD"),
        signals.get("ema", "HOLD"),
        signals.get("vwap", "HOLD"),
        consensus,
    ]
    with open(LOG_FILE, "a", newline="") as f:
        csv.writer(f).writerow(row)


def read_signals(limit: int = 200) -> list[dict]:
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r", newline="") as f:
        rows = list(csv.DictReader(f))
    return rows[-limit:][::-1]
