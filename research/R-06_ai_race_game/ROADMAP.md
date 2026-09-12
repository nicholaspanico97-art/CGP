# What the sim still needs to be a base for the game

Written Sep 12 2026, after v0.9 (AA index). The world model is in decent
shape as a *model*. This is an honest list of what is missing before a game
can be built on top of it, ordered by what gets more expensive the longer it
is left.

## Where it stands

Built and calibrated: hardware, fleets, power and the interconnect queue ·
capital including narrative valuation, infrastructure debt and corporate
parents · a data market with exclusives, auctions and a telemetry flywheel ·
eight capability domains bought with compute *and* data · benchmarks as task
difficulty distributions, with retirement, elicitation, chasing and the AA
index · talent as a scarce global stock with a people-to-compute shift ·
eleven strategies with their own objectives · release variance with a
no-regression ratchet · diffusion via openness and distillation · the
self-improvement loop · nine gated market segments.

Calibration 1.62x across four anchor families. ~90 lead changes a run,
5.7 of 7 labs viable at 2030.

---

## 1. The observability seam — **DONE, v1.0.** See `WORLD_MODEL.md` §2e.

Original entry kept below for the record.

### The observability seam — *was: architectural, do it first*

The simulation has perfect internal information. Anything can read
`lab.model.caps`, `lab.cash`, `lab.internal`. A game cannot.

There needs to be a hard boundary between **world state** and **what a
given lab can observe**, with the observable side built from things that
are actually public or inferable:

| Public | Inferable, with effort | Private |
|---|---|---|
| Published benchmark scores, AA | Cluster size from power siting and filings | True difficulty frontier |
| Prices per Mtok | Headcount from hiring | Unreleased models |
| Announced products and segments | Data deals from press | Cash position, runway |
| Funding rounds, valuations | Serving volume from outages | Training mixture, research pipeline |

This matters beyond UI plumbing. **It is what makes half the mechanics
mean anything.** Benchmark-chasing is only interesting because rivals
cannot see your true frontier. Hoarding only works because nobody knows
what you have. Right now those mechanics are modelled but not *hidden*, so
the AI opponents are implicitly cheating.

It also wants an **intel** action: spend to narrow your estimate of a
rival — hire from them, buy their API in volume, read their papers.

Doing this later means rewriting every consumer of lab state. Doing it now
costs a day.

## 2. The decision seam — **next**

Policy is currently baked into `doctrine` dicts read inline all over
`world.py`. A lab does not *decide* anything; the loop reaches in and reads
its parameters.

A game needs:

```
observation = world.observe(lab)          # what this lab can see
actions     = policy.decide(observation)  # strategy AI, or a human
world.apply(lab, actions)                 # validated, logged
```

with the eleven strategies becoming implementations of `policy`, and the
player being one more. That also gets, for free: an action log (so a game
can be saved, resumed and replayed), validation (so an illegal action is
caught rather than silently absorbed), and the ability to run a strategy
against a recorded game to see if it would have done better.

## 3. Safety, incidents and regulation — **DONE, v1.3.** See
`WORLD_MODEL.md` §2f and `sim/safety.py`.

Original entry kept below for the record.

### Safety, incidents and regulation — *was: the biggest missing pillar*

`safety_debt` accumulates and does **nothing**. No incident ever fires.
There is no regulator. This is a whole designed pillar (`DESIGN.md` §6)
that does not exist, and it is the one that makes speed a real decision
rather than a free one.

Needs: an incident hazard driven by deployment surface, capability jump
since last evaluation and safety investment; four severity tiers; a
regulator that responds to sector incident history with compute thresholds,
licensing and liability; and evaluation as a real cost in time and compute
that a lab can choose to skip.

Without it, "ship without evaluating" is strictly free and every strategy
should do it.

## 4. Events — **cheap, high drama**

`DESIGN.md` specifies a twelve-card deck; none of it is implemented. Chip
allocation cuts, open-weight releases, talent raids, data lawsuits, power
constraints, viral quarters. These are what make two runs of the same
strategy feel like different stories rather than the same story with
different dice.

Should be data-driven (a JSON deck), conditional on world state rather than
on the date, and visible in the viewer as a timeline.

## 5. Government as an actor

`supply_share` is a static per-strategy number standing in for the entire
geopolitics of compute. Export controls, compute thresholds, procurement,
national champions and energy permitting should be a modelled actor that
responds to the sector, not a constant.

## 6. The player's own charter and the Legacy Report

The eleven AI strategies have objectives; a player has none. The player
needs a charter with the same structure — its own goals, scored the same
way — and an end-of-decade report across the four axes in `DESIGN.md` §11.

## 7. Named people

Stars are a float. For a game they should be individuals with names who
visibly move between labs, because "three of their top researchers just
left for a rival" is a story and "stars: 7.3 → 6.1" is not.

## 8. Fab supply should respond to demand

`FAB_OUTPUT_PER_MONTH` is a fixed table by year. In reality capacity
expanded *because* labs bought. It should respond to sector capex with a
2-3 year lag, which also makes a compute-hoarding strategy raise everyone's
costs.

---

## Recommended order

1. **Observability seam** (1) — architectural, cheap now, expensive later,
   and it retroactively makes the benchmark and hoarding mechanics honest.
2. **Decision seam** (2) — same argument, and it is what the player plugs
   into.
3. ~~**Safety and regulation** (3)~~ — **done in v1.3.**
4. **Events** (4) — cheap, and the biggest gain in run-to-run variety.

5-8 are content and can follow in any order.

The honest summary as of v1.3: the **economy, the capability race, the
information structure and the consequence structure are all modelled. What
is not modelled is the game** — nothing in `sim/` decides anything; policy
is still read inline out of `doctrine` dicts. That is item 2, and it is now
the only architectural item left.
