# R-01 — Systematic (Rules-Based) Trading

**Status:** SELECTED (Nick, Jul 17 2026) — active workstream at
`workstreams/R-01_systematic_trading/`
**Fit:** best match for the stated scope ("markets with strict trading
guidelines") and for an engineer's temperament: the whole point is
replacing discretion with written, testable rules.

## What it is
Define entry/exit/sizing rules in code, backtest them against
historical data, paper-trade them, and only then run them small with
real money — Nick executing every order himself per Standing Rule 2.
Crypto is the natural first venue only because small accounts aren't
penalized there (fractional sizing, 24/7 data, free APIs) — that's a
practical observation, not a market endorsement.

## Honest math (read this part twice)
With a few hundred to a few thousand dollars deployed, even a genuinely
good year — say 20%, which most professionals don't sustain — is a few
hundred dollars. The near-term value of R-01 is NOT income. It is:
1. a tested, disciplined system that scales if capital grows later, and
2. the skill itself.
Treat the first 3–6 months as R&D with expected net return ≈ $0.

## Effort / capital / risk
- **Effort:** heavy upfront (~20–40 hrs to build a backtest harness +
  data pipeline), low ongoing (fits the 5–10 hr/wk budget after that)
- **Capital:** $0 during R&D (paper only); a few hundred at go-live
- **Main risks:** overfitting (the #1 killer — a backtest that "works"
  on the data it was tuned on), fees/slippage eating small accounts,
  crypto exchange/custody risk, tax record-keeping burden
- **Ceiling:** low in absolute dollars at this capital level; the
  ceiling is the system, not the P&L

## First build if selected
Backtest harness: data fetcher (e.g., exchange OHLCV API), strategy
interface, fee/slippage model, walk-forward validation (train on one
period, test on a later one — the anti-overfitting discipline), and a
results log committed to this repo.
