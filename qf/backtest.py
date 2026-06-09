"""The thin, vectorized backtest harness. Positions are applied to the NEXT period's return
(decided at close t, earn return t+1) so a signal can never peek at the bar it trades on. The
out-of-sample split is strictly chronological and the test slice is meant to be evaluated once.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from qf.costs import CostModel
from qf.stats import max_drawdown
from qf.stats import sharpe
from qf.stats import t_stat


@dataclass(frozen=True)
class BacktestResult:
    net_returns: pd.Series
    gross_returns: pd.Series
    turnover: pd.Series
    n_obs: int
    sharpe: float
    t_stat: float
    max_drawdown: float

    @property
    def equity(self) -> pd.Series:
        return (1.0 + self.net_returns).cumprod()


def _as_frame(x: pd.Series | pd.DataFrame) -> pd.DataFrame:
    return x.to_frame() if isinstance(x, pd.Series) else x


def backtest(
    positions: pd.Series | pd.DataFrame,
    asset_returns: pd.Series | pd.DataFrame,
    costs: CostModel | None = None,
    periods_per_year: int = 252,
) -> BacktestResult:
    """Run a net-of-cost backtest. `positions` are target weights per asset; `asset_returns`
    are the matching per-asset simple returns. Single-asset Series are accepted directly.
    """
    costs = costs or CostModel()
    pos = _as_frame(positions).sort_index()
    rets = _as_frame(asset_returns).sort_index()
    if isinstance(positions, pd.Series) and isinstance(asset_returns, pd.Series):
        pos.columns = ["asset"]
        rets.columns = ["asset"]
    pos, rets = pos.align(rets, join="inner", axis=0)
    pos = pos.reindex(columns=rets.columns).fillna(0.0)

    executed = pos.shift(1).fillna(0.0)
    gross = (executed * rets).sum(axis=1)
    turnover = executed.diff().abs().sum(axis=1)
    turnover.iloc[0] = executed.iloc[0].abs().sum()
    gross_exposure = executed.abs().sum(axis=1)

    net = gross - costs.turnover_cost(turnover) - costs.roll_cost(gross_exposure)
    net = net.dropna()
    return BacktestResult(
        net_returns=net,
        gross_returns=gross.reindex(net.index),
        turnover=turnover.reindex(net.index),
        n_obs=len(net),
        sharpe=sharpe(net, periods_per_year),
        t_stat=t_stat(net),
        max_drawdown=max_drawdown(net),
    )


def split_oos(index: pd.Index, oos_fraction: float = 0.3) -> tuple[pd.Index, pd.Index]:
    """Chronological train/test split. The first (1 - oos_fraction) of the timeline is the
    in-sample head; the trailing oos_fraction is the held-out tail evaluated once.
    """
    if not 0.0 < oos_fraction < 1.0:
        raise ValueError(f"oos_fraction must be in (0, 1); got {oos_fraction}")
    ordered = index.sort_values()
    cut = int(len(ordered) * (1.0 - oos_fraction))
    return ordered[:cut], ordered[cut:]
