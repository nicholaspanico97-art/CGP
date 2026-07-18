# R-01 — Trading Workstream (two tracks)

**Status:** ACTIVE (selected Jul 17, 2026; restructured to two tracks
Jul 18 per Nick). No real capital until Standing Rule 3 is satisfied
(written ruleset + record committed here).

## Track 1 — Discretionary (primary)

Ad hoc opportunity-hunting: Nick brings ideas (or asks for research),
FAT supplies pros/cons analysis and data checks — never a verdict or a
buy/sell call — limits are set before entry, and every outcome is
recorded. Lives in `discretionary/`:
- `RULESET.md` — the pre-entry checklist and position limits (DRAFT
  until Nick redlines the bracketed limits)
- `JOURNAL.md` — the opportunity journal; the non-negotiable discipline

## Track 2 — Systematic (support tooling)

The backtest harness. Used to pressure-test discretionary theses
against history ("does buying X after Y actually work?") and to develop
rules-based strategies if any idea graduates to full automation.

## What's here

```
discretionary/    track 1: ruleset + opportunity journal
harness/          track 2: backtest harness (pure Python + requests, no other deps)
  data.py         OHLCV fetcher (Coinbase Exchange public API) + local CSV cache
  strategy.py     Strategy interface + reference strategies (SMA cross, buy & hold)
  backtest.py     event-loop backtester: next-bar fills, fees, slippage, metrics
  walkforward.py  walk-forward validation (train on one window, test on the next)
  run.py          CLI entry point
data_cache/       cached candles (gitignored)
results/          committed run logs — the Rule-3 paper record lives here
```

## Design rules (anti-self-deception)

1. **No lookahead.** Signals are computed on bar N's close; fills happen
   at bar N+1's open. The engine enforces this — a strategy physically
   cannot see the bar it trades into.
2. **Fees and slippage always on.** Default 25 bps fee + 10 bps slippage
   per side (Coinbase taker-tier ballpark for small accounts). A strategy
   that only works at 0 bps doesn't work.
3. **Walk-forward is the score that counts.** In-sample results are for
   debugging only. Parameters are chosen on a training window and scored
   on the following unseen window, rolled forward across history. The
   aggregate out-of-sample equity curve is the honest number.
4. **Benchmark or it didn't happen.** Every run reports buy-and-hold on
   the same data next to the strategy.

## Usage

```
# fetch/refresh data and run a single backtest (in-sample, debugging only)
python harness/run.py backtest --product BTC-USD --granularity 86400 --strategy sma_cross --params fast=20,slow=100

# the honest test: walk-forward validation
python harness/run.py walkforward --product BTC-USD --granularity 86400 --strategy sma_cross --train-bars 365 --test-bars 90

# results are written to results/ as markdown, and printed to stdout
```

## What "good" looks like

Not "beats buy-and-hold in a bull market." Good is: positive
out-of-sample walk-forward return after fees, drawdown meaningfully
below buy-and-hold's, stable across parameter neighborhoods (a strategy
that dies when fast=20 becomes fast=22 is an overfit artifact). Expect
most ideas to fail this bar. That's the harness doing its job.
