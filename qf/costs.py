"""Transaction-cost, slippage, and futures roll-cost models. Backtests are net-of-cost only;
a gross-only result is never a valid kill-test outcome.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import pandas as pd

AssetClass = Literal["equity", "etf", "future"]

# Round-trip-agnostic per-unit-turnover costs in basis points, by asset class. Deliberately
# conservative for free EOD data; tighten only with evidence from a real execution model.
_DEFAULT_COST_BPS: dict[AssetClass, float] = {"equity": 5.0, "etf": 2.0, "future": 3.0}
# Annualized number of contract rolls for a front-month futures strategy (~monthly).
_DEFAULT_ROLLS_PER_YEAR = 12.0


@dataclass(frozen=True)
class CostModel:
    """Charges costs proportional to traded notional. `cost_bps` is applied to per-period
    turnover (sum of absolute position changes); `roll_bps` is an extra per-roll charge for
    futures, amortized across the period to penalize phantom roll yield.
    """

    asset_class: AssetClass = "etf"
    cost_bps: float | None = None
    roll_bps: float = 1.0
    rolls_per_year: float = _DEFAULT_ROLLS_PER_YEAR
    periods_per_year: int = 252

    def _bps(self) -> float:
        return self.cost_bps if self.cost_bps is not None else _DEFAULT_COST_BPS[self.asset_class]

    def turnover(self, positions: pd.Series) -> pd.Series:
        """Per-period absolute change in position (the quantity that incurs trading cost)."""
        return positions.diff().abs().fillna(positions.abs())

    def turnover_cost(self, turnover: pd.Series) -> pd.Series:
        """Trading cost charged on per-period turnover (works for a single asset or a portfolio)."""
        return turnover * (self._bps() / 1e4)

    def roll_cost(self, gross_exposure: pd.Series) -> pd.Series:
        """Per-period futures roll charge proportional to held exposure; zero for cash assets."""
        if self.asset_class != "future":
            return pd.Series(0.0, index=gross_exposure.index)
        per_period_roll = (self.roll_bps / 1e4) * (self.rolls_per_year / self.periods_per_year)
        return gross_exposure.abs() * per_period_roll

    def apply(self, gross_returns: pd.Series, positions: pd.Series) -> pd.Series:
        """Subtract trading + roll costs from a single-asset gross return series."""
        net = gross_returns - self.turnover_cost(self.turnover(positions))
        return net - self.roll_cost(positions)
