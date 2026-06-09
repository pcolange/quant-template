# CLAUDE.md — quant-strategy scaffold

Per-build scaffold for quant-factory. You (the agent) build ONE trading-strategy kill test here.

## Layout

- `qf/` — **shared harness; do not modify.** Import it. It owns the anti-leakage/anti-overfit
  guarantees: offline `LocalParquetSource`, chronological `split_oos`, net-of-cost `backtest`,
  `CostModel` (incl. futures roll), `stats`, placebo `controls`.
- `killtest/` — **your code** (keep the package name; don't rename). `config.py` (pre-registered
  spec), `signal.py` (prices→positions), `pipeline.py` (snapshot→verdict), `__main__.py` (entry
  point that logs the ALIVE/DEAD verdict).
- `data/` — frozen snapshot staged before you run: `bars/<sym>.parquet`, `macro.parquet`,
  `MANIFEST.json`. `MANIFEST.json["as_of"]` is the point-in-time boundary — never use data after it.

## Hard rules

- Pre-register the kill criterion in `THESIS.md` and mirror the exact numbers in `killtest/config.py`
  **before** computing any out-of-sample metric. The OOS tail is evaluated once.
- Net-of-cost results only. Include a placebo/negative control. Be honest about `N_TRIALS`.
- Tests pass offline; mark live-network/LLM tests `@pytest.mark.network`/`@pytest.mark.llm`.
- Only staged symbols exist. A thesis needing unstaged data is DEAD at the data-existence gate.
- Research artifact, not investment advice. No live trading.

## Gates

```bash
uv sync --dev
uv run pytest
uv run ruff check . && uv run ruff format --check .
uv run pyright            # strict (unknown-type family relaxed)
```
