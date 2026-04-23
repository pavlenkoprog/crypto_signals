import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backtest_utils import run_grid_search
from strategies import rsi as strategy_rsi

if __name__ == "__main__":
    grid = {
        "period": [8, 10, 14, 21],
        "buy_level": [20, 25, 30, 35],
        "sell_level": [65, 70, 75, 80],
    }

    run_grid_search(
        strategy_name="RSI",
        signal_fn=strategy_rsi.signal,
        param_grid=grid,
        warmup_fn=lambda p: p["period"] + 2,
        interval="5",
        limit=1000,
    )
