import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backtest_utils import run_grid_search
from strategies import ema as strategy_ema

if __name__ == "__main__":
    grid = {
        "fast": [5, 9, 12, 18],
        "slow": [20, 26, 34, 50],
    }

    run_grid_search(
        strategy_name="EMA Cross",
        signal_fn=strategy_ema.signal,
        param_grid=grid,
        warmup_fn=lambda p: p["slow"] + 2,
        interval="5",
        limit=1000,
    )
