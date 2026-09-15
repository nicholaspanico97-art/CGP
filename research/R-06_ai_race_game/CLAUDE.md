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
| `HANDOFF.md` | The last session's record: what was just built and why |
| `BENCHMARKS_PROPOSAL.md` | Why benchmarks work the way they do, with outcome notes |
| `WORLD_STATE.md` | The world outside the labs: blocs, supply, capital, mood — initial parameters and the anchors they must reproduce before acting |
| `HARDWARE.md` | The supply chain: foundries, memory, chip designers with their own books; rules, anchors, first measurement |
| `ECONOMY.md` | Four blocs and demand as a labour market; parameters, anchors, first reading (observed; the switch waits on finding 12) |

`PAPER_PROTOTYPE.md` is superseded; kept for its kill-gate discipline only.

## Run it

```
python3 -m sim.checkpoints   # PRIMARY calibration: timing, in months
python3 -m sim.replay        # the seam check: record, replay, must match bit for bit
python3 -m sim.hardware_checkpoints 7   # the supply chain vs the record (observed tier)
python3 -m sim.serve --seed 7 --lab 2  # PLAY IT in a browser: open http://localhost:8765
python3 -m sim.play --seed 7 --lab 2   # or in the terminal
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
strategy.py    11 strategies with variation, drawn per game (what they WANT)
policy.py      the decision seam: Observation, Actions, Policy; DoctrinePolicy
               is the strategies' behaviour; ReplayPolicy replays a log
replay.py      record -> save -> replay; must be bit-identical
game.py        the player's seat: PlayerPolicy, Game (turns, board letter, preview)
explain.py     why a model is what it is: the capability chain, itemised
geo.py         the world outside the labs (v1.9: observed, not yet acting)
hardware.py    foundries, memory, chip designers (v1.10: observed, not yet acting)
hardware_checkpoints.py  the supply chain's instrument
econ.py        four blocs, demand as a labour market (v1.11: observed, not yet acting)
play.py        terminal front end for game.py; `--auto N` watches autopilot
serve.py       local web dashboard (viewer/play.html) on top of game.py; stdlib only
objectives.py  what each strategy is trying to do; how success is scored
safety.py      incident hazard, three severity tiers, sector regulation
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
- **Five separate RNG streams per lab** (`rng`, `rng_eval`, `rng_intel`,
  `rng_safety`, `rng_policy`). Adding a draw to one must not reshuffle the
  others, or calibration stops being comparable across changes. **A
  conditional draw must still be consumed unconditionally** — an
  `always_eval` short-circuit once made the safety-first strategy skip one
  `random()` per ship, which desynchronised every later decision in the run
  and silently contaminated every A/B run against it.
- **A policy draws only from `rng_policy`; the world never does.** So the
  world's realisation cannot depend on how a policy decided, and a replay
  (which draws nothing) reproduces the run.
- **`world.py` reads `lab.doctrine` only for identity, never for a
  choice.** Anything a lab chooses goes through `lab.actions`, set by its
  `Policy` in `World._decide` (standing) or `World.ask_release` (the
  interrupt when a run lands). `python3 -m sim.replay` is the check: a
  `ReplayPolicy` has no doctrine and no observation, so a mechanic that
  reaches around the seam shows up as a divergence. Run it after any change
  to `world.py`.
- **Immediate purchases go through `World.buy_now`** and are logged as
  `{"now": ...}`; `sim.replay` applies them before the month's tick. Any
  new kind of instant order must go through it, or the seam leaks.
- **There is no cooldown timer.** The gap between runs is `decide_run`
  returning "not this month" for reasons (launch prep, post-training in
  the base, a cluster landing, not enough effective growth). Do not add a
  timer back; if cadence is off, the reasons' constants are the knobs.
- **`behind` is a belief.** `maybe_ship` measures a finished run against
  `lab.believed_frontier` (the central estimate; the paranoid band drives
  spending, not dice). `BEHIND_RISK_APPETITE` was refit for that input;
  do not "fix" it back to the world's max.
- **A run's recipe is fixed when it is planned.** `World.ask_run` stores
  the `RunPlan` in `lab.run_plan`; `maybe_ship` reads tokens/param,
  sparsity, test-time and mixture from there, never from `lab.actions`.
  `sim/explain.py` is the one place the capability chain is itemised; the
  planner preview and `model.why` both call it.
- **A/B a mechanic by flipping ONE lab, not all of them.** Making every lab
  careless and comparing outcomes is a null experiment: the relative
  standings are unchanged by construction. Pair the same lab against itself
  in the same world on the same seed.
- **Nothing downstream of `World._observe` may read a rival's true state.**
  Decisions run on `lab.beliefs`. Breaking this makes the AI cheat and
  silently voids benchmark-chasing and hoarding.
- **A lab's own goals are scored on what it BUILT**, including unreleased
  models. The market only ever sees what shipped.
- **Two dials trade realism for play**: `COMPETITIVENESS` (1.8) and `SPIRAL`
  (1.0). Both are documented values choices, not fits. `0` on either gives
  the historical-realism setting.

## Current state

Timing 15/16 inside ±18 months, median offset −10, mean |offset| 9.4.
Order 113/120. Eleven strategies score 54–89% on their own goals. ~86 lead
changes per run, top lab ~39% of revenue, ~6 of 7 labs viable at 2030.
Safety incidents fire with the intended severity gradient: nothing severe is
possible before agentic capability exists, and by 2028–30 severe is ~6% of
incidents. Every decision goes through the seam; replay is bit-identical.

## What is deliberately not modelled yet

Events, government as an actor, labs dying, and the player. See
`ROADMAP.md`. **It is playable** (v1.5): `sim/serve.py` in a browser or
`sim/play.py` in a terminal. **The plan of record is `ROADMAP.md` "v2
direction"**: fix what playing finds, then give the world state of its own
(blocs, regulators, energy, fab supply), then close the loop so the world
reacts to AI (demand as a labour market → public mood → politics), then the
organisation (charters as factions, named people, products), then the map.
Every new world subsystem gets an instrument before it gets content.
