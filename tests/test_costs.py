"""Cost model sanity: costs are non-negative, monotonic in turnover, and never make net > gross."""

from __future__ import annotations

import pandas as pd

from qf.costs import CostModel


def test_turnover_cost_monotonic() -> None:
    costs = CostModel(asset_class="equity")
    low = pd.Series([0.1, 0.1, 0.1])
    high = pd.Series([1.0, 1.0, 1.0])
    assert costs.turnover_cost(high).sum() > costs.turnover_cost(low).sum()


def test_net_never_exceeds_gross() -> None:
    costs = CostModel(asset_class="future")
    gross = pd.Series([0.01, -0.02, 0.0, 0.005])
    positions = pd.Series([1.0, -1.0, 1.0, 0.0])
    net = costs.apply(gross, positions)
    assert (net <= gross + 1e-12).all()


def test_zero_turnover_zero_trading_cost() -> None:
    costs = CostModel(asset_class="etf")
    flat = pd.Series([0.0, 0.0, 0.0])
    assert (
        costs.turnover_cost(costs.turnover(pd.Series([1.0, 1.0, 1.0])).fillna(0.0)).iloc[1:].sum()
        == 0.0
    )
    assert costs.roll_cost(flat).sum() == 0.0
