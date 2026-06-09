"""Pipeline check: the harness must read ALIVE on a known edge and DEAD on pure noise. If this
fails, the harness itself is broken and no daily verdict can be trusted.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from qf.backtest import backtest
from qf.backtest import split_oos
from qf.costs import CostModel


def _momentum(returns: pd.Series) -> pd.Series:
    """Decide today's position from today's return sign; the harness shifts it forward one day."""
    return pd.Series(np.sign(returns.to_numpy()), index=returns.index, name="pos")


def test_known_edge_reads_alive(edge_returns: pd.Series) -> None:
    pos = _momentum(edge_returns)
    _, oos = split_oos(edge_returns.index, 0.3)
    result = backtest(pos.reindex(oos), edge_returns.reindex(oos), CostModel(asset_class="etf"))
    assert result.sharpe > 1.0
    assert result.t_stat > 2.0


def test_pure_noise_reads_dead(noise_returns: pd.Series) -> None:
    pos = _momentum(noise_returns)
    _, oos = split_oos(noise_returns.index, 0.3)
    result = backtest(pos.reindex(oos), noise_returns.reindex(oos), CostModel(asset_class="etf"))
    # No edge: the mean OOS return is statistically indistinguishable from zero, so the
    # pre-registered significance gate (t-stat >= 2.0) rejects it. Raw Sharpe on a finite OOS
    # sample is itself noisy and is not the kill signal.
    assert abs(result.t_stat) < 2.0
