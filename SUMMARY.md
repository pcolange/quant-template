# SUMMARY — PLACEHOLDER

The agent overwrites this LAST (this is what gets emailed). It must include:

- **Verdict: ALIVE or DEAD** (and why) — a clean DEAD with its killing fact is a successful run.
- **Calibrated confidence (0–100%)** — load-bearing `[ASSUMPTION]`s and conceded red-team points
  pull it down; cap at 50% if two or more load-bearing facts are unverified.
- Test counts (passed / failed / skipped); ruff + pyright status.
- One-paragraph recap of the thesis and what the OOS backtest showed.
- A machine-readable verdict block for the ledger:

```
asset_class: <equity|etf|future>
oos_metric: <e.g. sharpe>
threshold: <pre-registered pass value>
observed: <OOS value>
verdict: <ALIVE|DEAD>
```

- **FACTS TO VERIFY** checklist.

> Research artifact, not investment advice. No live trading. Backtested results are hypothetical.
