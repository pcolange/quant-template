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
from qf.stats import max_drawdown
from qf.stats import sharpe
from qf.stats import t_stat

__all__ = [
    "BacktestResult",
    "CostModel",
    "DataSource",
    "LocalParquetSource",
    "backtest",
    "max_drawdown",
    "sharpe",
    "split_oos",
    "t_stat",
]
