"""
runner.py — запускает цикл: загрузка → стратегии → логирование.
Запуск: python runner.py [--once]
"""
import time
import argparse
from collections import Counter
from datetime import datetime, UTC

from core.config import INTERVAL, LIMIT, SYMBOLS
from core.data import fetch_ohlcv
from core.signal_logger import log_signal
from strategies import bb as strategy_bb
from strategies import ema as strategy_ema
from strategies import macd as strategy_macd
from strategies import rsi as strategy_rsi
from strategies import vwap as strategy_vwap

STRATEGIES = {
    "rsi":  strategy_rsi.signal,
    "macd": strategy_macd.signal,
    "bb":   strategy_bb.signal,
    "ema":  strategy_ema.signal,
    "vwap": strategy_vwap.signal,
}

CYCLE_SECONDS = 60 * 5  # каждые 5 минут
PROCESS_STARTED_AT = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")


def consensus(signals: dict) -> str:
    counts = Counter(signals.values())
    top, count = counts.most_common(1)[0]
    return top if count >= 3 else "HOLD"


def run_once():
    for symbol in SYMBOLS:
        try:
            df = fetch_ohlcv(symbol, INTERVAL, LIMIT)
            price = df["close"].iloc[-1]
            sigs = {name: fn(df) for name, fn in STRATEGIES.items()}
            result = consensus(sigs)
            log_signal(symbol, price, sigs, result, PROCESS_STARTED_AT)
            print(f"{symbol:15s}  price={price:<14.6f}  {sigs}  -> {result}")
        except Exception as exc:
            print(f"ERROR {symbol}: {exc}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="выполнить один цикл и выйти")
    args = parser.parse_args()

    if args.once:
        run_once()
        return

    print(f"Запуск цикла каждые {CYCLE_SECONDS // 60} мин. Ctrl+C для остановки.")
    while True:
        run_once()
        time.sleep(CYCLE_SECONDS)


if __name__ == "__main__":
    main()
