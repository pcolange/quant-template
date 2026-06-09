"""LocalParquetSource reads the frozen snapshot correctly and runs the full strategy pipeline
offline end-to-end.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pandas as pd
import pytest

from killtest.pipeline import run
from qf.data_loader import close_prices
from qf.datasource import LocalParquetSource


def test_reads_bars_within_range(staged_data_dir: Path, snapshot_asof: dt.date) -> None:
    source = LocalParquetSource(staged_data_dir)
    frame = source.bars(["SYN"], dt.date(2005, 1, 1), snapshot_asof)["SYN"]
    assert list(frame.columns) == ["open", "high", "low", "close", "volume"]
    assert frame.index.is_monotonic_increasing
    assert bool((frame.index <= pd.Timestamp(snapshot_asof)).all())


def test_macro_panel(staged_data_dir: Path, snapshot_asof: dt.date) -> None:
    source = LocalParquetSource(staged_data_dir)
    panel = source.macro(["DGS10"], dt.date(2005, 1, 1), snapshot_asof)
    assert "DGS10" in panel.columns


def test_close_prices_wide(staged_data_dir: Path) -> None:
    source = LocalParquetSource(staged_data_dir)
    wide = close_prices(source, ["SYN"])
    assert "SYN" in wide.columns
    assert bool(wide["SYN"].notna().any())


def test_pipeline_runs_offline(staged_data_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """The placeholder strategy must produce a verdict from the snapshot with no network."""
    from killtest import config

    monkeypatch.setattr(config, "SYMBOLS", ["SYN"])
    source = LocalParquetSource(staged_data_dir)
    verdict = run(source)
    assert verdict.label in {"ALIVE", "DEAD"}
    assert verdict.n_oos > 0
