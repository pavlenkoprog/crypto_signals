import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backtest_utils import run_grid_search
from strategies import macd as strategy_macd

if __name__ == "__main__":
    grid = {
        "fast": [8, 12, 16],
        "slow": [20, 26, 34],
        "signal_period": [6, 9, 12],
    }

    run_grid_search(
        strategy_name="MACD",
        signal_fn=strategy_macd.signal,
        param_grid=grid,
        warmup_fn=lambda p: max(p["slow"], p["signal_period"]) + 2,
        interval="5",
        limit=1000,
    )
