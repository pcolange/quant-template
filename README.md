# quant-strategy (scaffold)

PLACEHOLDER per-build scaffold for **quant-factory**. Each daily run, the agent fills in the
`killtest` package with its thesis, updates the project `name`/`description`, and embeds the run's
`SUMMARY.md` here.

## What's fixed vs. what the agent writes

- **`qf/` — do not modify.** The shared, tested backtest harness: `DataSource`/`LocalParquetSource`
  (offline data access), `backtest` + `split_oos` (chronological OOS), `CostModel` (net-of-cost,
  futures roll), `stats` (Sharpe/t-stat/drawdown/deflated-Sharpe/bootstrap), `controls` (placebos),
  `forecast` (naive baselines, error metrics, Diebold-Mariano, forecast→position bridge).
- **`killtest/` — the agent rewrites** (the package name stays `killtest`). `config.py`
  (pre-registered universe + OOS thresholds), `signal.py` (prices → positions), `pipeline.py`
  (snapshot → ALIVE/DEAD verdict), `__main__.py`.
- **`data/` — staged at run time** by the controller's `fetch_data` step (frozen Parquet snapshot
  + `MANIFEST.json` with the `as_of` point-in-time boundary). The agent reads it; never fetches.

## Run

```bash
./install.sh                            # uv sync --dev + pre-commit install
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run pyright                          # strict (unknown-type family relaxed)
python -m killtest                      # logs ALIVE/DEAD from the staged snapshot
```

Tests pass offline against synthetic fixtures. The known-edge series must read ALIVE and pure
noise must read DEAD — if not, the harness is broken.

> Research artifact, not investment advice. No live trading. Backtested results are hypothetical.
