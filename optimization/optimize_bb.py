import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backtest_utils import run_grid_search
from strategies import bb as strategy_bb

if __name__ == "__main__":
    grid = {
        "period": [14, 20, 26, 34],
        "std_dev": [1.6, 2.0, 2.4, 2.8],
    }

    run_grid_search(
        strategy_name="Bollinger Bands",
        signal_fn=strategy_bb.signal,
        param_grid=grid,
        warmup_fn=lambda p: p["period"] + 2,
        interval="5",
        limit=1000,
    )
