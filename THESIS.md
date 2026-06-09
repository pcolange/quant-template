# THESIS — PLACEHOLDER

The agent overwrites this FIRST, before any code, with the pre-registered spec:

- Gate 0–7 findings (market inefficiency, signal availability, lead/lag, crowding, falsifiable
  hypothesis, OOS kill-test design, tradability, regulatory posture).
- One-sentence falsifiable hypothesis.
- **Pre-registered kill criterion** with exact numeric OOS thresholds (Sharpe / t-stat / max-DD)
  fixed BEFORE any OOS metric is computed — mirrored in `killtest/config.py`.
- Staged data used (symbols, range, `as_of`) and observation count / power.
- Tests to build, including the placebo control.
- **FACTS TO VERIFY** — every `[VERIFIED]` / `[ASSUMPTION]` claim with the exact check to re-run.
