"""
trade_bot.py — автоторговля на Bybit по консенсус-сигналам.
Запуск: python trade_bot.py [--once]
"""
import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from core.bybit_client import BybitClient
from core.config import INTERVAL, LIMIT, SYMBOLS
from core.data import fetch_ohlcv
from core.signal_logger import log_signal
from core.trade_logger import log_trade
from runner import STRATEGIES, consensus, load_optimized_params

CYCLE_SECONDS = 60 * 5
PROCESS_STARTED_AT = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
POSITIONS_FILE = Path(__file__).resolve().parent / "open_positions.json"
TARGET_ORDER_USDT = 20.0
MIN_ORDER_USDT = 5.0


def load_dotenv():
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


def load_positions() -> dict:
    if not POSITIONS_FILE.exists():
        return {}
    try:
        return json.loads(POSITIONS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_positions(positions: dict):
    POSITIONS_FILE.write_text(json.dumps(positions, ensure_ascii=False, indent=2), encoding="utf-8")


def get_order_amount(client: BybitClient) -> float:
    balance = client.get_usdt_balance()
    if balance >= TARGET_ORDER_USDT:
        return TARGET_ORDER_USDT
    if balance >= MIN_ORDER_USDT:
        return balance
    return 0.0


def run_once(client: BybitClient):
    optimized_params = load_optimized_params()
    positions = load_positions()

    for symbol in SYMBOLS:
        try:
            df = fetch_ohlcv(symbol, INTERVAL, LIMIT)
            price = float(df["close"].iloc[-1])
            sigs = {}
            for name, fn in STRATEGIES.items():
                kwargs = optimized_params.get(name, {}).get(symbol, {})
                sigs[name] = fn(df, **kwargs)
            result = consensus(sigs)
            log_signal(symbol, price, sigs, result, PROCESS_STARTED_AT)

            position = positions.get(symbol)
            if result == "BUY" and position is None:
                # Проверяем баланс перед каждой покупкой
                usdt_amount = get_order_amount(client)
                if usdt_amount < MIN_ORDER_USDT:
                    log_trade(
                        symbol=symbol,
                        action="BUY",
                        usdt_amount=0.0,
                        qty=0.0,
                        price=price,
                        signal=result,
                        result="SKIP",
                        note="Not enough USDT balance (<5)",
                    )
                    print(f"SKIP {symbol:12s} not enough USDT balance")
                    continue

                # Пытаемся купить с обработкой ошибок
                try:
                    qty = usdt_amount / price
                    client.place_market_buy_by_quote(symbol, usdt_amount)
                    positions[symbol] = {
                        "entry_price": price,
                        "qty": qty,
                        "usdt_amount": usdt_amount,
                        "opened_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    save_positions(positions)
                    log_trade(
                        symbol=symbol,
                        action="BUY",
                        usdt_amount=usdt_amount,
                        qty=qty,
                        price=price,
                        signal=result,
                        result="OK",
                        note="Opened position",
                    )
                    print(f"BUY  {symbol:12s} qty={qty:.8f} usdt={usdt_amount:.2f} price={price:.8f}")
                except Exception as buy_error:
                    # Если ошибка при покупке - логируем как SKIP
                    log_trade(
                        symbol=symbol,
                        action="BUY",
                        usdt_amount=usdt_amount,
                        qty=0.0,
                        price=price,
                        signal=result,
                        result="SKIP",
                        note=f"Buy failed: {str(buy_error)}",
                    )
                    print(f"SKIP {symbol:12s} buy error: {buy_error}")

            elif result == "SELL" and position is not None:
                # Получаем реальный баланс с биржи (учитывает комиссии)
                real_qty = client.get_coin_balance(symbol)
                if real_qty == 0:
                    print(f"SKIP {symbol:12s} no balance on exchange")
                    continue

                entry_price = float(position["entry_price"])
                invested = float(position["usdt_amount"])

                # Пытаемся продать реальное количество
                try:
                    client.place_market_sell_by_base(symbol, real_qty)
                    proceeds = real_qty * price
                    pnl_usdt = proceeds - invested
                    pnl_pct = (pnl_usdt / invested * 100) if invested > 0 else 0.0
                    positions.pop(symbol, None)
                    save_positions(positions)
                except Exception as sell_error:
                    # Если ошибка при продаже - логируем и продолжаем держать
                    log_trade(
                        symbol=symbol,
                        action="SELL",
                        usdt_amount=0.0,
                        qty=real_qty,
                        price=price,
                        signal=result,
                        result="SKIP",
                        note=f"Sell failed: {str(sell_error)}",
                    )
                    print(f"SKIP {symbol:12s} sell error: {sell_error}")
                    continue
                log_trade(
                    symbol=symbol,
                    action="SELL",
                    usdt_amount=proceeds,
                    qty=real_qty,
                    price=price,
                    signal=result,
                    result="OK",
                    pnl_usdt=pnl_usdt,
                    pnl_pct=pnl_pct,
                    note=f"Entry={entry_price:.8f}",
                )
                print(f"SELL {symbol:12s} qty={real_qty:.8f} pnl={pnl_usdt:.4f} ({pnl_pct:.2f}%)")
            else:
                print(f"HOLD {symbol:12s} signal={result} position={'yes' if position else 'no'}")

        except Exception as exc:
            # Общие ошибки (получение данных, стратегия и т.д.)
            print(f"ERROR {symbol}: {exc}")
            # Не логируем в trades.csv, т.к. это не торговая операция


def main():
    load_dotenv()
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="выполнить один цикл и выйти")
    args = parser.parse_args()

    api_key = os.getenv("BYBIT_API_KEY", "").strip()
    api_secret = os.getenv("BYBIT_API_SECRET", "").strip()
    if not api_key or not api_secret:
        raise ValueError("Set BYBIT_API_KEY and BYBIT_API_SECRET in .env")

    client = BybitClient(api_key=api_key, api_secret=api_secret, testnet=False)

    if args.once:
        run_once(client)
        return

    print(f"Trade bot started: every {CYCLE_SECONDS // 60} min, order=20 USDT (min 5 if balance low)")
    while True:
        run_once(client)
        time.sleep(CYCLE_SECONDS)


if __name__ == "__main__":
    main()
