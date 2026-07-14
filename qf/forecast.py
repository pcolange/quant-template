"""Forecast-evaluation harness: causal naive baselines, forecast-error metrics, a
Diebold-Mariano significance test against a baseline, and the bridge from forecasts to
backtestable positions.

Convention: a forecast series is indexed by the date it predicts (the target date); the
prediction for date t may use information through t - horizon only. Baselines built here
respect that by construction; the agent's model must too.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd
from scipy import stats as _scipy_stats

Loss = Literal["squared", "absolute"]

_MIN_OBS = 3


@dataclass(frozen=True)
class DMResult:
    """Diebold-Mariano test outcome. p_value is one-sided: small means the model's loss is
    significantly below the baseline's.
    """

    dm_stat: float
    p_value: float
    mean_loss_model: float
    mean_loss_baseline: float
    n: int


def naive_last_value(y: pd.Series, horizon: int = 1) -> pd.Series:
    """Predict y_t with y_{t-horizon} (the random walk in the modeled quantity)."""
    return y.shift(horizon)


def naive_zero(index: pd.Index) -> pd.Series:
    """Predict zero everywhere — the random walk in prices when y is returns."""
    return pd.Series(0.0, index=index)


def naive_drift(y: pd.Series, horizon: int = 1) -> pd.Series:
    """Predict y_t with the expanding mean of observations through t - horizon."""
    return y.expanding().mean().shift(horizon)


def naive_rolling_mean(y: pd.Series, window: int, horizon: int = 1) -> pd.Series:
    """Predict y_t with the rolling mean of the `window` observations through t - horizon."""
    return y.rolling(window).mean().shift(horizon)


def _joined(actual: pd.Series, predicted: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    frame = pd.concat({"actual": actual, "predicted": predicted}, axis=1, join="inner").dropna()
    return frame["actual"].to_numpy(), frame["predicted"].to_numpy()


def rmse(actual: pd.Series, predicted: pd.Series) -> float:
    """Root mean squared error over the inner-joined, NaN-free overlap. 0.0 if empty."""
    a, p = _joined(actual, predicted)
    if len(a) == 0:
        return 0.0
    return float(np.sqrt(np.mean((a - p) ** 2)))


def mae(actual: pd.Series, predicted: pd.Series) -> float:
    """Mean absolute error over the inner-joined, NaN-free overlap. 0.0 if empty."""
    a, p = _joined(actual, predicted)
    if len(a) == 0:
        return 0.0
    return float(np.mean(np.abs(a - p)))


def directional_accuracy(actual: pd.Series, predicted: pd.Series) -> float:
    """Fraction of observations where sign(actual) == sign(predicted). 0.0 if empty."""
    a, p = _joined(actual, predicted)
    if len(a) == 0:
        return 0.0
    return float(np.mean(np.sign(a) == np.sign(p)))


def _loss(errors: np.ndarray, loss: Loss) -> np.ndarray:
    return errors**2 if loss == "squared" else np.abs(errors)


def diebold_mariano(
    actual: pd.Series,
    pred_model: pd.Series,
    pred_baseline: pd.Series,
    *,
    loss: Loss = "squared",
    horizon: int = 1,
) -> DMResult:
    """Diebold-Mariano test of equal forecast accuracy, one-sided against the model.

    Uses a Bartlett-kernel HAC variance of the loss differential (truncation at
    horizon - 1, the MA order induced by an h-step forecast) and the
    Harvey-Leybourne-Newbold small-sample correction with t(n-1) critical values.
    Degenerate inputs (too few observations, zero-variance differential) return a
    conservative p_value of 1.0 unless the model's loss is strictly lower.
    """
    frame = pd.concat(
        {"actual": actual, "model": pred_model, "baseline": pred_baseline}, axis=1, join="inner"
    ).dropna()
    loss_model = _loss(frame["actual"].to_numpy() - frame["model"].to_numpy(), loss)
    loss_baseline = _loss(frame["actual"].to_numpy() - frame["baseline"].to_numpy(), loss)
    d = loss_model - loss_baseline
    n = len(d)
    mean_model = float(loss_model.mean()) if n else 0.0
    mean_baseline = float(loss_baseline.mean()) if n else 0.0
    if n < _MIN_OBS:
        return DMResult(0.0, 1.0, mean_model, mean_baseline, n)

    d_bar = float(d.mean())
    centered = d - d_bar
    # Bartlett-kernel long-run variance of d; h-step-ahead errors are MA(h-1).
    variance = float(centered @ centered) / n
    for k in range(1, min(horizon, n)):
        weight = 1.0 - k / horizon
        variance += 2.0 * weight * float(centered[k:] @ centered[:-k]) / n
    if variance <= 0.0:
        p_value = 0.0 if d_bar < 0.0 else 1.0
        return DMResult(0.0, p_value, mean_model, mean_baseline, n)

    dm = d_bar / np.sqrt(variance / n)
    h = horizon
    hln = np.sqrt((n + 1 - 2 * h + h * (h - 1) / n) / n)
    dm_stat = float(dm * hln)
    p_value = float(_scipy_stats.t.cdf(dm_stat, df=n - 1))
    return DMResult(dm_stat, p_value, mean_model, mean_baseline, n)


def skill(
    actual: pd.Series,
    pred_model: pd.Series,
    pred_baseline: pd.Series,
    *,
    loss: Loss = "squared",
) -> float:
    """Skill score 1 - loss_model / loss_baseline: positive means the model beats the
    baseline. 0.0 when the baseline loss is degenerate (zero or empty overlap).
    """
    frame = pd.concat(
        {"actual": actual, "model": pred_model, "baseline": pred_baseline}, axis=1, join="inner"
    ).dropna()
    if frame.empty:
        return 0.0
    loss_model = _loss(frame["actual"].to_numpy() - frame["model"].to_numpy(), loss).mean()
    loss_baseline = _loss(frame["actual"].to_numpy() - frame["baseline"].to_numpy(), loss).mean()
    if loss_baseline == 0.0:
        return 0.0
    return float(1.0 - loss_model / loss_baseline)


def forecasts_to_positions(
    pred_returns: pd.Series,
    *,
    mode: Literal["sign", "scaled"] = "sign",
    scale_window: int = 63,
    clip: float = 1.0,
) -> pd.Series:
    """Turn one-bar return forecasts into target weights for `qf.backtest`.

    `pred_returns` is indexed by the target date t and must be built from information
    through t - horizon (horizon >= 1). The forecast targeting t is re-labeled to t's
    preceding bar, so after `backtest`'s one-bar execution shift it earns exactly the
    return it predicts — causal because its information set predates that bar.
    "sign" takes the forecast's sign; "scaled" normalizes by the rolling forecast
    dispersion over `scale_window` targets and clips to [-clip, clip].
    """
    if mode == "sign":
        weights = pd.Series(np.sign(pred_returns.to_numpy()), index=pred_returns.index)
    else:
        dispersion = pred_returns.rolling(scale_window).std()
        weights = (pred_returns / dispersion.replace(0.0, np.nan)).clip(-clip, clip)
    return weights.shift(-1).fillna(0.0)
