"""The thesis's signal: prices in, target positions out. PLACEHOLDER — a trivial time-series
momentum rule the agent replaces with its actual edge. It must use only information available at
the close of each bar (no look-ahead); the harness shifts positions forward by one period.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def positions(prices: pd.DataFrame, lookback: int = 20) -> pd.DataFrame:
    """Long when the trailing `lookback`-day return is positive, short otherwise (±1 per asset)."""
    momentum = prices.pct_change(lookback)
    return pd.DataFrame(
        np.sign(momentum.to_numpy()), index=prices.index, columns=prices.columns
    ).fillna(0.0)
