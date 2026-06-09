"""Placebo / negative controls. A real edge must beat these; if a control also "passes," the
pipeline is leaking and the run is DEAD by construction.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def shuffle_positions(
    positions: pd.Series | pd.DataFrame, seed: int = 0
) -> pd.Series | pd.DataFrame:
    """Randomly permute positions in time, destroying any genuine timing while preserving the
    position distribution. A strategy whose edge survives this was never timing anything.
    """
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(positions))
    shuffled = positions.to_numpy()[order]
    if isinstance(positions, pd.DataFrame):
        return pd.DataFrame(shuffled, index=positions.index, columns=positions.columns)
    return pd.Series(shuffled, index=positions.index, name=positions.name)


def sign_flip(positions: pd.Series | pd.DataFrame) -> pd.Series | pd.DataFrame:
    """Invert the signal. If the flipped strategy is also profitable, the result is symmetric
    noise, not a directional edge.
    """
    return -positions


def random_positions(like: pd.Series | pd.DataFrame, seed: int = 0) -> pd.Series | pd.DataFrame:
    """Random ±1 positions with the same shape — a pure-noise benchmark that must read DEAD."""
    rng = np.random.default_rng(seed)
    values = rng.choice([-1.0, 1.0], size=like.shape)
    if isinstance(like, pd.DataFrame):
        return pd.DataFrame(values, index=like.index, columns=like.columns)
    return pd.Series(values, index=like.index, name=like.name)
