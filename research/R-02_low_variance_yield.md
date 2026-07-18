# R-02 — Low-Variance Yield / Market-Neutral Approaches

**Status:** candidate — not active
**Fit:** the "boring baseline" — low effort, low variance, and the
honest benchmark every other workstream has to beat.

## What it is
Approaches whose return doesn't depend on predicting price direction:
interest-bearing cash equivalents, staking yield, and (further out the
risk curve) things like exchange funding-rate arbitrage. Mostly
set-and-monitor rather than build-and-trade.

## Honest math
Single-digit to low-teens percent annually is the realistic band, and
on a few thousand dollars that is tens to low hundreds of dollars per
year. This will never fund CEV by itself. Its role is (a) making idle
CGP capital non-idle and (b) forcing honesty: any trading strategy
that can't beat this after fees isn't worth running.

## Effort / capital / risk
- **Effort:** very low — a few hours to research and set up, then
  near-zero maintenance
- **Capital:** whatever is parked; scales linearly and boringly
- **Main risk:** NOT market risk — it's platform/custody/counterparty
  risk. The graveyard of "safe yield" products (Celsius, BlockFi, etc.)
  is exactly this failure mode. Venue selection matters far more than
  the advertised rate. Rule of thumb: if the yield is well above the
  risk-free rate, the difference is compensation for a risk someone
  isn't naming.
- **Ceiling:** hard-capped by capital; no skill or effort multiplier

## First build if selected
A one-page comparison in this folder of venue options with rate,
custody model, and failure modes — Nick picks and executes any actual
placement himself (Standing Rule 2).
