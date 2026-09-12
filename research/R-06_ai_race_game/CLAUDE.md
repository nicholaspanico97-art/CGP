# R-06 *Frontier* — orientation for a new session

A calibrated simulation of the AI race, 2020–2030, intended as the world a
business-management game will be built on. Zero dependencies, pure stdlib
Python. Read this first, then `WORLD_MODEL.md`.

## Read these, in this order

| File | What it is |
|---|---|
| `WORLD_MODEL.md` | The model: units, every subsystem, the calibration table |
| `PREMISES.md` | **Read before changing anything.** What is defensible, what is a guess, what is structurally wrong |
| `ROADMAP.md` | What is still missing before a game sits on this |
| `DESIGN.md` | The original game design. Still the target |
| `BENCHMARKS_PROPOSAL.md` | Why benchmarks work the way they do, with outcome notes |

`PAPER_PROTOTYPE.md` is superseded; kept for its kill-gate discipline only.

## Run it

```
python3 -m sim.checkpoints   # PRIMARY calibration: timing, in months
python3 -m sim.score         # secondary: magnitude sanity check only
python3 -m sim.balance 24    # strategy goal attainment, lead changes
python3 -m sim.fit_report    # benchmark curve fit
python3 -m sim.export run.json && \
  python3 -c "d=open('run.json').read(); open('viewer/rundata.js','w').write('window.RUN='+d+';')"
```

Viewer: `viewer/scope.html` beside `rundata.js`. No libraries, no network.

## How to judge a change — this matters

**Calibrate on TIMING, not magnitude.** `sim/checkpoints.py` asks when the
sim reached each milestone versus when the world did, in months. The old
magnitude metric (`sim/score.py`) punishes being six months early on a curve
rising an order of magnitude a year, which for an alternate-universe sim is
not an error. It is kept only to catch order-of-magnitude breakage.

Targets, in priority order:
1. **Order** — milestones fire in the right sequence (currently 113/120 pairs)
2. **Timing** — inside ±18 months (currently 15/16)
3. **Magnitude** — within an order of magnitude (yes, on every family)
4. **Shape** — the decade has an opening, a middle and a takeoff

**Always average over seeds.** A single run varies enough that a change can
look like a large improvement purely from where the dice landed. This was a
real mistake made in this project; several parameters were tuned on noise
before it was caught.

**Check which constraint binds before trusting a fit.** The largest error
found so far was a hard run-size ceiling deciding outcomes in 73% of
lab-months while the model claimed compute was the constraint — invisible to
the fit, because the ceiling had been tuned to reproduce history. A fitted
parameter doing a mechanism's job is the failure mode to watch for.

## The module map

```
constants.py   physical and economic constants, confidence-tagged
anchors.py     the 2020-2026 record as public estimates
capability.py  scaling, efficiency, reasoning multiplier, domain capability
tasks.py       benchmarks as task-difficulty distributions, the AA index
domains.py     8 domains, the TRANSFER matrix, 10 data sources, 9 segments
economics.py   accelerators, fleets, power, serving cost, demand
talent.py      researchers, stars, the people-to-compute shift, the RSI loop
intel.py       what a lab can see; beliefs with error bars; threat
release.py     run outcomes, the ship decision, x.5 releases
strategy.py    11 strategies with variation, drawn per game
objectives.py  what each strategy is trying to do; how success is scored
world.py       the monthly tick: everything above, wired together
scenarios.py   rosters. historical_2020() is FIXED for calibration
checkpoints.py timing calibration  <- the primary instrument
score.py       magnitude calibration (secondary)
balance.py     is it a race? did each strategy meet its own goals?
export.py      dump a run to JSON for the viewer
```

## Non-obvious invariants

- **`historical_2020()` must stay fixed.** It is the calibration roster.
  Randomised games use `randomized_2020(seed)`.
- **Four separate RNG streams per lab** (`rng`, `rng_eval`, `rng_intel`).
  Adding a draw to one must not reshuffle the others, or calibration stops
  being comparable across changes.
- **Nothing downstream of `World._observe` may read a rival's true state.**
  Decisions run on `lab.beliefs`. Breaking this makes the AI cheat and
  silently voids benchmark-chasing and hoarding.
- **A lab's own goals are scored on what it BUILT**, including unreleased
  models. The market only ever sees what shipped.
- **Two dials trade realism for play**: `COMPETITIVENESS` (1.8) and `SPIRAL`
  (1.0). Both are documented values choices, not fits. `0` on either gives
  the historical-realism setting.

## Current state

Timing 15/16 inside ±18 months, median offset −9. Order 113/120. Eleven
strategies score 60–95% on their own goals. ~90 lead changes per run, top
lab ~40% of revenue, ~6 of 7 labs viable at 2030.

## What is deliberately not modelled yet

Safety incidents and regulation (`safety_debt` accumulates and does nothing,
so shipping without evaluating is currently free), events, government as an
actor, labs dying, the player. See `ROADMAP.md`.
