"""Forecast harness checks: baselines are causal, metrics are exact, the Diebold-Mariano
test has power on a real signal and correct size on noise, and the forecast-to-position
bridge feeds the backtest causally. If these fail, no forecast verdict can be trusted.
"""

from __future__ import annotations

from collections.abc import Callable

import numpy as np
import pandas as pd
import pytest

from qf.backtest import backtest
from qf.backtest import split_oos
from qf.costs import CostModel
from qf.forecast import diebold_mariano
from qf.forecast import directional_accuracy
from qf.forecast import forecasts_to_positions
from qf.forecast import mae
from qf.forecast import naive_drift
from qf.forecast import naive_last_value
from qf.forecast import naive_rolling_mean
from qf.forecast import naive_zero
from qf.forecast import rmse
from qf.forecast import skill


def _ar1_forecast(y: pd.Series, oos_fraction: float = 0.3) -> pd.Series:
    """Fit AR(1) by OLS on the in-sample head only; predict every date from its lag."""
    train_idx, _ = split_oos(y.index, oos_fraction)
    train = y.reindex(train_idx)
    lagged, current = train.shift(1).dropna(), train.iloc[1:]
    phi = float((lagged * current).sum() / (lagged * lagged).sum())
    return y.shift(1) * phi


@pytest.mark.parametrize("horizon", [1, 5])
@pytest.mark.parametrize("baseline", ["last_value", "drift", "rolling_mean"])
def test_baselines_are_causal(edge_returns: pd.Series, baseline: str, horizon: int) -> None:
    builders: dict[str, Callable[[pd.Series], pd.Series]] = {
        "last_value": lambda y: naive_last_value(y, horizon),
        "drift": lambda y: naive_drift(y, horizon),
        "rolling_mean": lambda y: naive_rolling_mean(y, 20, horizon),
    }
    build = builders[baseline]
    cut = len(edge_returns) // 2
    perturbed = edge_returns.copy()
    perturbed.iloc[cut:] += 1.0
    original = build(edge_returns)
    after = build(perturbed)
    # Perturbing data from date t on may not change any prediction targeting < t + horizon.
    unaffected = original.index[: cut + horizon]
    pd.testing.assert_series_equal(original.reindex(unaffected), after.reindex(unaffected))


def test_metrics_hand_computed() -> None:
    index = pd.RangeIndex(5)
    actual = pd.Series([1.0, -1.0, 2.0, 0.5, -0.5], index=index)
    predicted = pd.Series([0.0, -2.0, 1.0, 1.5, 0.5], index=index)
    errors = np.array([1.0, 1.0, 1.0, -1.0, -1.0])
    assert rmse(actual, predicted) == pytest.approx(np.sqrt(np.mean(errors**2)))
    assert mae(actual, predicted) == pytest.approx(1.0)
    # Signs match on the middle three observations; sign(0.0) != sign(1.0) on the first.
    assert directional_accuracy(actual, predicted) == pytest.approx(0.6)


def test_zero_baseline_and_empty_overlap() -> None:
    index = pd.RangeIndex(3)
    assert naive_zero(index).eq(0.0).all()
    disjoint = pd.Series([1.0], index=[99])
    assert rmse(pd.Series([1.0], index=[0]), disjoint) == 0.0
    assert directional_accuracy(pd.Series([1.0], index=[0]), disjoint) == 0.0


def test_dm_power_on_real_signal(edge_returns: pd.Series) -> None:
    _, oos = split_oos(edge_returns.index, 0.3)
    actual = edge_returns.reindex(oos)
    model = _ar1_forecast(edge_returns).reindex(oos)
    baseline = naive_zero(oos)
    result = diebold_mariano(actual, model, baseline)
    assert result.p_value < 0.05
    assert result.mean_loss_model < result.mean_loss_baseline
    assert skill(actual, model, baseline) > 0.0


def test_dm_size_on_noise(noise_returns: pd.Series) -> None:
    _, oos = split_oos(noise_returns.index, 0.3)
    actual = noise_returns.reindex(oos)
    model = _ar1_forecast(noise_returns).reindex(oos)
    result = diebold_mariano(actual, model, naive_zero(oos))
    # No signal: the AR fit is spurious, so the model must not significantly beat the
    # random walk. This guards the test's size, not its power.
    assert result.p_value > 0.05


def test_dm_symmetry_and_bookkeeping(edge_returns: pd.Series) -> None:
    _, oos = split_oos(edge_returns.index, 0.3)
    actual = edge_returns.reindex(oos)
    model = _ar1_forecast(edge_returns).reindex(oos)
    baseline = naive_zero(oos)
    forward = diebold_mariano(actual, model, baseline)
    reverse = diebold_mariano(actual, baseline, model)
    assert forward.dm_stat == pytest.approx(-reverse.dm_stat)
    assert forward.n == reverse.n == len(oos)


def test_dm_degenerate_inputs() -> None:
    index = pd.RangeIndex(2)
    tiny = pd.Series([0.01, -0.02], index=index)
    result = diebold_mariano(tiny, naive_zero(index), naive_zero(index))
    assert result.p_value == 1.0
    assert result.dm_stat == 0.0


def test_positions_sign_mode_is_ternary(edge_returns: pd.Series) -> None:
    pred = _ar1_forecast(edge_returns)
    positions = forecasts_to_positions(pred, mode="sign")
    assert set(np.unique(positions.to_numpy())) <= {-1.0, 0.0, 1.0}


def test_positions_scaled_mode_is_clipped(edge_returns: pd.Series) -> None:
    pred = _ar1_forecast(edge_returns)
    positions = forecasts_to_positions(pred, mode="scaled", scale_window=63, clip=0.5)
    assert positions.abs().max() <= 0.5


def test_bridge_earns_the_predicted_bar(edge_returns: pd.Series) -> None:
    # Perfect foresight of each bar's return must monetize exactly that bar through the
    # backtest's execution shift; shuffled forecasts of the same bars must not.
    _, oos = split_oos(edge_returns.index, 0.3)
    actual = edge_returns.reindex(oos)
    costs = CostModel(asset_class="etf")

    foresight = backtest(forecasts_to_positions(actual), actual, costs)
    assert foresight.sharpe > 5.0
    assert foresight.t_stat > 10.0

    rng = np.random.default_rng(0)
    shuffled = pd.Series(rng.permutation(actual.to_numpy()), index=actual.index)
    placebo = backtest(forecasts_to_positions(shuffled), actual, costs)
    assert placebo.t_stat < foresight.t_stat
    assert abs(placebo.t_stat) < 2.0
