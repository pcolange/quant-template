"""Data access. The agent only ever uses LocalParquetSource, which reads the frozen snapshot
staged into data/ by the credentialed fetch step. It has no network path, so the agent's tests
run fully offline and the agent never holds a data API key.
"""

from __future__ import annotations

import datetime as dt
import json
from abc import ABC
from abc import abstractmethod
from pathlib import Path
from typing import Literal

import pandas as pd

Freq = Literal["1d"]
OHLCV_COLUMNS = ["open", "high", "low", "close", "volume"]


class DataSource(ABC):
    """Read-only market-data interface. Implementations promise point-in-time correctness:
    no bar dated after asof() may ever be returned.
    """

    @abstractmethod
    def bars(
        self, symbols: list[str], start: dt.date, end: dt.date, freq: Freq = "1d"
    ) -> dict[str, pd.DataFrame]:
        """OHLCV frame per symbol, indexed by a tz-naive DatetimeIndex named 'date'."""

    @abstractmethod
    def macro(self, series: list[str], start: dt.date, end: dt.date) -> pd.DataFrame:
        """Macro panel: one column per series, indexed by date."""

    @abstractmethod
    def asof(self) -> dt.date:
        """The point-in-time boundary. No data after this date exists in the snapshot."""


class LocalParquetSource(DataSource):
    """Offline DataSource backed by data/MANIFEST.json + data/bars/*.parquet + macro.parquet."""

    def __init__(self, data_dir: Path | str) -> None:
        self._dir = Path(data_dir)
        manifest_path = self._dir / "MANIFEST.json"
        if not manifest_path.exists():
            raise FileNotFoundError(f"no data snapshot at {manifest_path}")
        with manifest_path.open(encoding="utf-8") as fh:
            self._manifest: dict[str, object] = json.load(fh)
        self._asof = dt.date.fromisoformat(str(self._manifest["as_of"]))

    def asof(self) -> dt.date:
        return self._asof

    def _check_end(self, end: dt.date) -> None:
        if end > self._asof:
            raise ValueError(
                f"end {end} is past the snapshot as_of {self._asof}; look-ahead forbidden"
            )

    def bars(
        self, symbols: list[str], start: dt.date, end: dt.date, freq: Freq = "1d"
    ) -> dict[str, pd.DataFrame]:
        if freq != "1d":
            raise ValueError(f"only daily bars are staged; got freq={freq!r}")
        self._check_end(end)
        bars_meta = self._manifest.get("bars", {})
        if not isinstance(bars_meta, dict):
            raise TypeError("manifest 'bars' must be a mapping")
        out: dict[str, pd.DataFrame] = {}
        for sym in symbols:
            if sym not in bars_meta:
                raise KeyError(
                    f"symbol {sym!r} not in staged universe; this thesis is DEAD on data"
                )
            frame = pd.read_parquet(self._dir / "bars" / f"{sym}.parquet")
            frame = _index_by_date(frame)
            out[sym] = _slice(frame, start, end)
        return out

    def macro(self, series: list[str], start: dt.date, end: dt.date) -> pd.DataFrame:
        self._check_end(end)
        path = self._dir / "macro.parquet"
        if not path.exists():
            raise KeyError("no macro panel staged")
        panel = _index_by_date(pd.read_parquet(path))
        missing = [s for s in series if s not in panel.columns]
        if missing:
            raise KeyError(f"macro series not staged: {missing}")
        return _slice(pd.DataFrame(panel[series]), start, end)


def _index_by_date(frame: pd.DataFrame) -> pd.DataFrame:
    if "date" in frame.columns:
        frame = frame.set_index("date")
    frame.index = pd.to_datetime(frame.index)
    frame.index.name = "date"
    return frame.sort_index()


def _slice(frame: pd.DataFrame, start: dt.date, end: dt.date) -> pd.DataFrame:
    mask = (frame.index >= pd.Timestamp(start)) & (frame.index <= pd.Timestamp(end))
    return frame.loc[mask]
