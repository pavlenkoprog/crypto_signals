import itertools
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.config import SYMBOLS
from core.data import fetch_ohlcv


def backtest_signals(
    df: pd.DataFrame,
    signal_fn: Callable,
    signal_kwargs: dict,
    warmup: int,
    initial_cash: float = 1.0,
) -> tuple[float, int]:
    cash = initial_cash
    position = 0.0
    trades = 0

    for i in range(max(2, warmup), len(df)):
        window = df.iloc[: i + 1]
        price = float(window["close"].iloc[-1])
        sig = signal_fn(window, **signal_kwargs)

        if sig == "BUY" and cash > 0:
            position = cash / price
            cash = 0.0
            trades += 1
        elif sig == "SELL" and position > 0:
            cash = position * price
            position = 0.0
            trades += 1

    final_equity = cash + position * float(df["close"].iloc[-1])
    profit_pct = (final_equity / initial_cash - 1) * 100
    return profit_pct, trades


def run_grid_search(
    strategy_name: str,
    signal_fn: Callable,
    param_grid: dict,
    warmup_fn: Callable[[dict], int],
    interval: str = "5",
    limit: int = 1000,
) -> dict:
    keys = list(param_grid.keys())
    combos = [dict(zip(keys, values)) for values in itertools.product(*(param_grid[k] for k in keys))]
    print(
        f"=== {strategy_name} | interval={interval} | symbols={len(SYMBOLS)} | "
        f"combos={len(combos)} | mode=per-symbol ==="
    )

    data_by_symbol = {}
    for symbol in SYMBOLS:
        data_by_symbol[symbol] = fetch_ohlcv(symbol, interval=interval, limit=limit)

    best_by_symbol = {}
    for symbol in SYMBOLS:
        symbol_results = []
        df = data_by_symbol[symbol]
        for params in combos:
            warmup = warmup_fn(params)
            profit_pct, trades = backtest_signals(df, signal_fn, params, warmup=warmup)
            symbol_results.append(
                {
                    "params": params,
                    "profit_pct": profit_pct,
                    "trades": trades,
                }
            )

        best = sorted(symbol_results, key=lambda x: (x["profit_pct"], -x["trades"]), reverse=True)[0]
        best_by_symbol[symbol] = best
        print(
            f"{symbol:12s} | best_params={best['params']} | "
            f"profit={best['profit_pct']:.2f}% | trades={best['trades']}"
        )

    payload = {
        "strategy": strategy_name,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
        "interval": interval,
        "limit": limit,
        "symbols_count": len(SYMBOLS),
        "combos_count": len(combos),
        "best_by_symbol": best_by_symbol,
    }

    safe_name = strategy_name.lower().replace(" ", "_")
    output_file = Path(__file__).resolve().parent / "results" / f"{safe_name}_best_params.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"\nSaved: {output_file}")
    return payload
