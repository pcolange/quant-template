"""A genuine edge must beat its placebo. Shuffling positions in time destroys the timing, so the
shuffled control must collapse toward zero Sharpe even on the edge series.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from qf.backtest import backtest
from qf.backtest import split_oos
from qf.controls import shuffle_positions
from qf.controls import sign_flip
from qf.costs import CostModel


def _momentum(returns: pd.Series) -> pd.Series:
    return pd.Series(np.sign(returns.to_numpy()), index=returns.index, name="pos")


def test_shuffled_placebo_collapses(edge_returns: pd.Series) -> None:
    pos = _momentum(edge_returns)
    _, oos = split_oos(edge_returns.index, 0.3)
    costs = CostModel(asset_class="etf")

    real = backtest(pos.reindex(oos), edge_returns.reindex(oos), costs)
    placebo = backtest(
        shuffle_positions(pos.reindex(oos), seed=1), edge_returns.reindex(oos), costs
    )
    assert real.sharpe > 1.0
    assert placebo.sharpe < real.sharpe - 1.0


def test_sign_flip_inverts_edge(edge_returns: pd.Series) -> None:
    pos = _momentum(edge_returns)
    _, oos = split_oos(edge_returns.index, 0.3)
    costs = CostModel(asset_class="etf")

    real = backtest(pos.reindex(oos), edge_returns.reindex(oos), costs)
    flipped = backtest(sign_flip(pos).reindex(oos), edge_returns.reindex(oos), costs)
    assert real.sharpe > 0.0 > flipped.sharpe
