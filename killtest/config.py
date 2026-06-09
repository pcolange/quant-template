"""Pre-registered specification. The agent fills these in THESIS.md FIRST and mirrors the exact
numbers here BEFORE any out-of-sample metric is computed. The kill criterion is fixed in advance;
changing it after seeing OOS results is the cardinal sin this framework exists to prevent.
"""

from __future__ import annotations

from typing import Literal

# Which staged universe this thesis trades. Drives the cost model.
ASSET_CLASS: Literal["equity", "etf", "future"] = "etf"

# Symbols the strategy needs. All must be present in data/MANIFEST.json or the run is DEAD.
SYMBOLS: list[str] = ["SPY"]

# Fraction of the timeline held out as the (once-evaluated) out-of-sample tail.
OOS_FRACTION: float = 0.3

# Pre-registered pass thresholds on the OOS tail. ALL must hold for an ALIVE verdict.
OOS_SHARPE_MIN: float = 0.5
OOS_TSTAT_MIN: float = 2.0
OOS_MAX_DRAWDOWN_FLOOR: float = -0.25  # net OOS max drawdown must be >= this (less severe)

# Number of distinct specifications tried this run (for the multiple-testing haircut). Be honest.
N_TRIALS: int = 1
