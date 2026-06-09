"""Convenience loaders that turn a DataSource into the wide frames a backtest consumes,
while enforcing the point-in-time boundary.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd

from qf.datasource import DataSource

DEFAULT_START = dt.date(2005, 1, 1)


def close_prices(
    source: DataSource, symbols: list[str], start: dt.date = DEFAULT_START
) -> pd.DataFrame:
    """Wide DataFrame of close prices (date index, one column per symbol), up to source.asof()."""
    end = source.asof()
    bars = source.bars(symbols, start, end)
    closes = {sym: frame["close"] for sym, frame in bars.items()}
    wide = pd.DataFrame(closes)
    return wide.sort_index()


def daily_returns(
    source: DataSource, symbols: list[str], start: dt.date = DEFAULT_START
) -> pd.DataFrame:
    """Simple daily returns from close prices."""
    return close_prices(source, symbols, start).pct_change().dropna(how="all")


def macro_panel(
    source: DataSource, series: list[str], start: dt.date = DEFAULT_START
) -> pd.DataFrame:
    """Macro panel forward-filled to a daily index up to source.asof()."""
    panel = source.macro(series, start, source.asof())
    return panel.sort_index().ffill()
