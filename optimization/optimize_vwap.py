import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backtest_utils import run_grid_search
from strategies import vwap as strategy_vwap

if __name__ == "__main__":
    grid = {
        "threshold": [0.002, 0.003, 0.004, 0.005, 0.006, 0.008],
    }

    run_grid_search(
        strategy_name="VWAP",
        signal_fn=strategy_vwap.signal,
        param_grid=grid,
        warmup_fn=lambda p: 2,
        interval="5",
        limit=1000,
    )
