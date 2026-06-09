"""Shared fixtures: deterministic synthetic series and a tiny staged data snapshot. No network."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest


def _ar1_returns(n: int, phi: float, sigma: float, seed: int) -> pd.Series:
    rng = np.random.default_rng(seed)
    eps = rng.normal(0.0, sigma, size=n)
    r = np.zeros(n)
    for t in range(1, n):
        r[t] = phi * r[t - 1] + eps[t]
    index = pd.bdate_range("2005-01-03", periods=n, name="date")
    return pd.Series(r, index=index, name="ret")


@pytest.fixture
def edge_returns() -> pd.Series:
    """AR(1) returns with strong positive autocorrelation: time-series momentum genuinely works."""
    return _ar1_returns(n=4000, phi=0.4, sigma=0.01, seed=42)


@pytest.fixture
def noise_returns() -> pd.Series:
    """i.i.d. returns: no edge. Any apparent Sharpe is sampling noise."""
    return _ar1_returns(n=4000, phi=0.0, sigma=0.01, seed=7)


@pytest.fixture
def staged_data_dir(tmp_path: Path, edge_returns: pd.Series) -> Path:
    """A minimal data/ snapshot: one symbol's OHLCV parquet + a macro panel + MANIFEST.json."""
    data = tmp_path / "data"
    (data / "bars").mkdir(parents=True)
    close = 100.0 * (1.0 + edge_returns).cumprod()
    bars = pd.DataFrame(
        {
            "date": close.index,
            "open": close.to_numpy(),
            "high": close.to_numpy() * 1.001,
            "low": close.to_numpy() * 0.999,
            "close": close.to_numpy(),
            "volume": 1_000_000.0,
        }
    )
    bars.to_parquet(data / "bars" / "SYN.parquet")

    macro = pd.DataFrame({"date": close.index, "DGS10": 3.0, "VIXCLS": 18.0})
    macro.to_parquet(data / "macro.parquet")

    as_of = close.index[-1].date()
    manifest = {
        "as_of": as_of.isoformat(),
        "source": "synthetic",
        "start": close.index[0].date().isoformat(),
        "bars": {"SYN": {"rows": len(bars), "path": "bars/SYN.parquet"}},
        "macro": {"rows": len(macro), "path": "macro.parquet", "series": ["DGS10", "VIXCLS"]},
    }
    (data / "MANIFEST.json").write_text(json.dumps(manifest), encoding="utf-8")
    return data


@pytest.fixture
def snapshot_asof(staged_data_dir: Path) -> dt.date:
    manifest = json.loads((staged_data_dir / "MANIFEST.json").read_text(encoding="utf-8"))
    return dt.date.fromisoformat(manifest["as_of"])
