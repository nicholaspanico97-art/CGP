# CGP PROJECT STATE
*Maintained by FAT (Fable Architect — engineering sessions).
Last updated: July 18, 2026 — R-01 selected, backtest harness built.*

This repo is deliberately self-contained: a session opened here should
need nothing from any other project. Keep it that way.

## Purpose
Fund Nick's personal projects — CEV first — i.e. "personal
industrialization." Secondary benefit: financial buffer against job
automation / general security. No fixed dollar target: Nick is
financially stable with a job that meets his needs; the more that can
be *ethically* generated, the better.

## Constraints
- **Time:** 5–10 hrs/week
- **Capital:** a few hundred deployable now; up to a few thousand for
  approaches that have proven reliable
- Surplus money, not needed money — but Standing Rule 1 still applies

## Scope
- **IN (early):** financial & crypto markets under strict written
  trading guidelines
- **MAYBE (later):** a tech thing / product worth selling (leverages
  printer + CAD + engineering skillset)
- **OUT:** freelancing — deliberate work-life-balance decision; Nick
  would just freelance his regulatory skillset if he wanted that

## Standing Rules (approved as written by Nick, Jul 17 2026)
1. Never deploy money that isn't affordable to lose entirely.
   Per-position risk caps are defined in a workstream's ruleset BEFORE
   any capital moves.
2. **Nick executes all trades and transfers personally.** FAT builds
   research, tooling, backtests, and monitoring — but never touches an
   account, never executes a transaction, and doesn't make individual
   buy/sell calls. (This is also a hard assistant-side boundary, not
   just preference.)
3. No strategy goes live with real money until it has a written
   ruleset plus a backtest or paper-trade record committed to this repo.
4. The capital ledger is updated in any session where money moved.

## Workstreams
| ID | Name | Status | Notes |
|----|------|--------|-------|
| R-01 | Systematic trading | **ACTIVE — R&D (paper only)** | `workstreams/R-01_systematic_trading/` — harness built Jul 18, walk-forward validated on BTC-USD daily. No capital deployed; Rule 3 gate not yet passed |
| R-03 | Sellable product | parked | Revisit after R-01 R&D settles into low-maintenance rhythm |

## Capital Ledger
| Date | Workstream | In | Out | Net to date | Notes |
|------|-----------|----|-----|-------------|-------|
| — | — | — | — | $0.00 | Opening balance |

## Decision Log
- **Jul 17, 2026** — Project created as its own repo, outside the
  workshop, partly so it can sit open on screen without cross-project
  material visible. Scaffold committed.
- **Jul 17, 2026** — Scope set (see Purpose/Constraints/Scope above).
  Freelance ruled out. Markets-first, product-maybe.
- **Jul 17, 2026** — GitHub remote created by Nick:
  `nicholaspanico97-art/CGP`.
- **Jul 17, 2026** — R-02 (low-variance yield) rejected: Nick is
  already well invested in personal-finance terms; no need to
  duplicate it here. Remaining candidates: R-01, R-03.
- **Jul 17, 2026** — Nick picked **R-01 (systematic trading)** as the
  first workstream; R-03 parked. Standing Rules approved as written.
- **Jul 18, 2026** — Backtest harness built and validated
  (`workstreams/R-01_systematic_trading/`): Coinbase public OHLCV
  fetcher + cache, next-bar-fill engine with fees/slippage, walk-forward
  optimizer, CLI. First honest result committed to `results/`: SMA cross
  on BTC-USD daily returns +18.4% OOS vs +114.2% buy & hold over the
  same span, with unstable chosen params — i.e., no edge, correctly
  detected. The harness's job is to say no; it says no.

## Next Actions
- [ ] FAT: candidate strategy pipeline — implement 2-3 strategies with
      a real hypothesis (e.g., volatility-filtered trend, donchian
      breakout, cross-sectional momentum across a few majors) and put
      them through the same walk-forward bar
- [ ] FAT: add a paper-trade mode (daily signal emitter Nick can
      sanity-check live) once any strategy clears walk-forward
- [ ] Nick: none blocking — review `results/` reports at leisure
- [ ] Rule 3 gate: written ruleset + paper record before any capital
