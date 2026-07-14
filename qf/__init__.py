"""qf — the shared, tested quant-factory backtest harness.

The per-build agent imports this package; it must not modify it. The harness owns the
anti-leakage and anti-overfit guarantees (chronological out-of-sample split, net-of-cost
returns, placebo controls) so each daily build reuses tested rigor instead of re-deriving it.
"""

from qf.backtest import BacktestResult
from qf.backtest import backtest
from qf.backtest import split_oos
from qf.costs import CostModel
from qf.datasource import DataSource
from qf.datasource import LocalParquetSource
from qf.forecast import DMResult
from qf.forecast import diebold_mariano
from qf.forecast import directional_accuracy
from qf.forecast import forecasts_to_positions
from qf.forecast import mae
from qf.forecast import naive_drift
from qf.forecast import naive_last_value
from qf.forecast import naive_rolling_mean
from qf.forecast import naive_zero
from qf.forecast import rmse
from qf.forecast import skill
from qf.stats import max_drawdown
from qf.stats import sharpe
from qf.stats import t_stat

__all__ = [
    "BacktestResult",
    "CostModel",
    "DMResult",
    "DataSource",
    "LocalParquetSource",
    "backtest",
    "diebold_mariano",
    "directional_accuracy",
    "forecasts_to_positions",
    "mae",
    "max_drawdown",
    "naive_drift",
    "naive_last_value",
    "naive_rolling_mean",
    "naive_zero",
    "rmse",
    "sharpe",
    "skill",
    "split_oos",
    "t_stat",
]
