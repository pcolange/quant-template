"""Wire the staged data through the signal and the qf harness to a pre-registered ALIVE/DEAD
verdict on the out-of-sample tail. The agent keeps this shape; only the signal/config change.
"""

from __future__ import annotations

from dataclasses import dataclass

import structlog

from killtest import config
from killtest import signal
from qf.backtest import backtest
from qf.backtest import split_oos
from qf.costs import CostModel
from qf.data_loader import close_prices
from qf.data_loader import daily_returns
from qf.datasource import DataSource
from qf.stats import deflated_sharpe

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class Verdict:
    alive: bool
    oos_sharpe: float
    oos_tstat: float
    oos_max_drawdown: float
    n_oos: int

    @property
    def label(self) -> str:
        return "ALIVE" if self.alive else "DEAD"


def run(source: DataSource) -> Verdict:
    """Evaluate the pre-registered thesis on the held-out OOS tail. Returns the verdict."""
    prices = close_prices(source, config.SYMBOLS)
    rets = daily_returns(source, config.SYMBOLS)
    pos = signal.positions(prices)

    _, oos_index = split_oos(rets.index, config.OOS_FRACTION)
    costs = CostModel(asset_class=config.ASSET_CLASS)
    result = backtest(pos.reindex(oos_index), rets.reindex(oos_index), costs)

    oos_sharpe = deflated_sharpe(result.sharpe, config.N_TRIALS)
    alive = (
        oos_sharpe >= config.OOS_SHARPE_MIN
        and result.t_stat >= config.OOS_TSTAT_MIN
        and result.max_drawdown >= config.OOS_MAX_DRAWDOWN_FLOOR
    )
    verdict = Verdict(
        alive=alive,
        oos_sharpe=oos_sharpe,
        oos_tstat=result.t_stat,
        oos_max_drawdown=result.max_drawdown,
        n_oos=result.n_obs,
    )
    logger.info(
        "verdict",
        label=verdict.label,
        oos_sharpe=round(oos_sharpe, 3),
        oos_tstat=round(result.t_stat, 3),
        oos_max_drawdown=round(result.max_drawdown, 3),
        n_oos=result.n_obs,
    )
    return verdict
