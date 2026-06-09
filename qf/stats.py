"""Performance and significance statistics. Kept small and dependency-light; statsmodels/scipy
are available for richer inference when a thesis needs it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def sharpe(returns: pd.Series, periods_per_year: int = TRADING_DAYS) -> float:
    """Annualized Sharpe ratio. Returns 0.0 for a degenerate (zero-variance) series."""
    r = returns.dropna()
    if len(r) < 2 or r.std(ddof=1) == 0:
        return 0.0
    return float(r.mean() / r.std(ddof=1) * np.sqrt(periods_per_year))


def t_stat(returns: pd.Series) -> float:
    """t-statistic of the mean return against zero (i.i.d. assumption)."""
    r = returns.dropna()
    n = len(r)
    if n < 2 or r.std(ddof=1) == 0:
        return 0.0
    return float(r.mean() / (r.std(ddof=1) / np.sqrt(n)))


def max_drawdown(returns: pd.Series) -> float:
    """Worst peak-to-trough decline of the cumulative equity curve, as a negative fraction."""
    r = returns.dropna()
    if r.empty:
        return 0.0
    equity = (1.0 + r).cumprod()
    drawdown = equity / equity.cummax() - 1.0
    return float(drawdown.min())


def deflated_sharpe(observed: float, n_trials: int, periods_per_year: int = TRADING_DAYS) -> float:
    """Haircut a Sharpe for multiple testing: subtract the Sharpe a best-of-N random search
    would produce by chance. A crude but honest guard against spec-mining.
    """
    if n_trials <= 1:
        return observed
    # Expected max of N standard normals, divided by sqrt(periods_per_year) to annualize.
    expected_max_z = np.sqrt(2.0 * np.log(n_trials))
    return float(observed - expected_max_z / np.sqrt(periods_per_year))


def block_bootstrap_pvalue(
    returns: pd.Series, block: int = 20, n_boot: int = 1000, seed: int = 0
) -> float:
    """One-sided p-value that mean return > 0, resampling contiguous blocks to preserve
    autocorrelation. Lower is stronger evidence of a real positive edge.
    """
    r = returns.dropna().to_numpy()
    n = len(r)
    if n < block + 1:
        return 1.0
    rng = np.random.default_rng(seed)
    observed = float(r.mean())
    centered = r - observed
    n_blocks = int(np.ceil(n / block))
    starts_pool = n - block
    hits = 0
    for _ in range(n_boot):
        starts = rng.integers(0, starts_pool, size=n_blocks)
        sample = np.concatenate([centered[s : s + block] for s in starts])[:n]
        if sample.mean() >= observed:
            hits += 1
    return float(hits / n_boot)
