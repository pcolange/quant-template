"""Guards against the two ways a backtest leaks the future: reading bars past the as_of boundary,
and an OOS split that isn't strictly chronological.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import pytest

from qf.backtest import split_oos
from qf.datasource import LocalParquetSource


def test_source_refuses_post_asof(staged_data_dir: Path, snapshot_asof: dt.date) -> None:
    source = LocalParquetSource(staged_data_dir)
    with pytest.raises(ValueError, match="look-ahead"):
        source.bars(["SYN"], dt.date(2005, 1, 1), snapshot_asof + dt.timedelta(days=1))


def test_unstaged_symbol_is_dead(staged_data_dir: Path, snapshot_asof: dt.date) -> None:
    source = LocalParquetSource(staged_data_dir)
    with pytest.raises(KeyError):
        source.bars(["NOT_STAGED"], dt.date(2005, 1, 1), snapshot_asof)


def test_oos_split_is_chronological() -> None:
    index = pd.bdate_range("2010-01-01", periods=1000, name="date")
    train, test = split_oos(index, 0.3)
    assert len(train) + len(test) == len(index)
    assert len(train.intersection(test)) == 0
    assert train.append(test).is_monotonic_increasing
