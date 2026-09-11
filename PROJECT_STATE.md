# CGP PROJECT STATE
*Maintained by FAT (Fable Architect — engineering sessions).
Last updated: Sep 11, 2026 — R-06 design approved; P0 paper prototype written.*

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
| R-01 | Trading (two tracks) | **ACTIVE — R&D (paper only)** | `workstreams/R-01_systematic_trading/` — Track 1: discretionary opportunity journal + checklist ruleset (primary, per Nick Jul 18). Track 2: backtest harness as support tooling. No capital deployed; Rule 3 gate not yet passed |
| R-03 | Sellable product | parked | Revisit after R-01 R&D settles into low-maintenance rhythm |
| R-04 | Content channel | candidate | Document gearbox/actuator builds; Bee entirely out of frame. Demand engine for R-03/R-05 |
| R-05 | SCP actuators | candidate | Nick's white whale — TCP polymer muscles + fabrication tooling as product. Sequenced after CEV v0.5 |
| R-06 | *Frontier* — AI race sim game | **ACTIVE — P0 prototype** | `research/R-06_ai_race_game/` — business sim, 2020–2030, one frontier lab. Design approved Sep 11; paper prototype written and waiting to be played. Personal project, explicitly NOT a capital workstream |

## Capital Ledger
| Date | Workstream | In | Out | Net to date | Notes |
|------|-----------|----|-----|-------------|-------|
| — | — | — | — | $0.00 | Opening balance |
| Jul 18, 2026 | R-01 discretionary | $250.00 | — | $250.00 | Working capital allocated by Nick. Limits: 2% risk/trade, 50% max deployment, ≤7-day holds (see R-01 RULESET.md). Nick reports changes per trade |

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
- **Jul 18, 2026** — R-01 restructured to two tracks per Nick:
  **discretionary is primary** (Nick brings opportunities, FAT gives
  pros/cons analysis — never verdicts or buy/sell calls — limits set
  pre-entry, everything journaled), systematic harness becomes support
  tooling for pressure-testing theses. FAT's no-individual-trade-calls
  line reconfirmed as a hard boundary, not a preference. Also agreed:
  any R-03 design sold to others requires intensive testing at a
  HIGHER bar than personal use (full build from published files alone).
- **Jul 18, 2026** — Ruleset approved with Nick's limits; $250 working
  capital allocated (see ledger).
- **Jul 18, 2026** — Two new research candidates filed at Nick's
  interest: R-04 (content channel — gearbox/actuator documentation,
  Bee out of frame, separate from any personal CNS/psychedelic channel)
  and R-05 (supercoiled polymer actuators — Nick's white whale, ChemE
  home turf, tooling-as-product thesis). Neither active; R-05 sequenced
  after CEV v0.5.

- **Sep 11, 2026** — R-06 filed at Nick's request: *Frontier*, a
  business-management simulation of the AI race, 2020–2030. Full design
  plan committed (`research/R-06_ai_race_game.md`); no code by
  instruction. Core mechanic is the three-way compute split
  (train / serve / experiment). Proposed kill gate is a paper prototype
  before anything is built. Open questions for Nick in §16 — including
  whether this is personal-interest only or a live R-03 candidate.

- **Sep 11, 2026** — R-06 design approved by Nick without changes.
  Scope locked: personal project (not an R-03 candidate), single-player
  always, lab-only (no chip-vendor or regulator modes), gritty economic
  sim over broad reach, paper prototype first. Stated target feeling —
  *"staring at benchmarks, pissed you lost on AA by two points; seeing
  how long you can burn cash on inference"* — promoted two systems to
  first-class in `DESIGN.md` §6: the **published benchmark index** (AA,
  with ±2 noise, where the market prices the published number and not
  your true capability) and **the burn** (gross margin and a runway
  clock, with serving below cost as a legitimate play). `PAPER_PROTOTYPE.md`
  written: 12 turns, Q1 2022–Q4 2024, one charter, two rivals, full
  tables, event deck, and a four-part kill gate that includes testing
  the two-point-loss feeling directly. Still no code, by design.

## Next Actions
- [x] Nick: set limits — DONE Jul 18 ($250 capital, 2% risk/trade,
      50% max deployment, ≤7-day holds). RULESET.md APPROVED
- [ ] Nick: bring the first opportunity to the table (or name a
      market/asset for FAT to research first)
- [ ] Nick: thinking on R-03 product directions (parked, no action)
- [ ] FAT: on request — research briefs, thesis pressure-tests via the
      harness, more strategies through walk-forward as ideas arise
- [x] Nick: review R-06 design plan — DONE Sep 11, approved, scope
      locked (see decision log)
- [ ] Nick: play the R-06 P0 paper prototype and keep the playtest log
      (§12). Four kill-gate criteria in §10 decide whether P1 happens
- [ ] Rule 3 gate: RULESET.md approved + journal running before any
      real capital
