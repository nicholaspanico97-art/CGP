# HANDOFF — Frontier (R-06), Sep 12 2026

Written at the end of the session that built safety. If you are a new
session, read `CLAUDE.md` first (it auto-loads), then this, then
`WORLD_MODEL.md`. This file is the *session* record: what was just done, what
is known to be true about it, and what I would do next. `CLAUDE.md` is the
permanent orientation; this one goes stale.

## Where the project actually is

A calibrated, zero-dependency simulation of the AI race 2020–2030 lives in
`sim/`. It is a *world model*, not a game. There is no player, no turn
structure, no UI beyond a read-only viewer. The plan of record
(`DESIGN.md`, `ROADMAP.md`) is that the game is a window onto this
simulation, and the window comes last.

Branch: `claude/ai-race-game-plan-vl6gi3`. No PR has been opened and none
was asked for.

## What this session added

**Safety, incidents and regulation** — `ROADMAP.md` item 3, the largest
missing pillar. `sim/safety.py` is new; `sim/world.py` gained a `_safety(m)`
step, a fourth per-lab RNG stream (`rng_safety`) and regulation effects in
the market and finance steps; `sim/constants.py` gained a tagged safety
block; all eleven strategies in `sim/strategy.py` gained `safety_spend` and
`eval_rate`.

Design, per Nick's brief: three tiers (minor / moderate / severe),
catastrophic deliberately deferred, and the governing principle that *a
glorified chatbot misaligning is not dangerous, while any deviation in
something with real agency is*. So **frequency** is driven by sloppiness and
deployment surface, and **severity** is gated on AGENT capability and on how
much agentic product is actually deployed. Full spec: `WORLD_MODEL.md` §2f.

## What is verified, and what is not

**Verified.**

*The severity gradient is what Nick asked for.* Over 24 seeded runs:

```
  era          minor  moderate  severe   severe share
  2019-2021       83        11       0             0%
  2022-2024      218        33       0             0%
  2025-2027      154        71       5             2%
  2028-2030      110       150      16             6%
```

Nothing severe is possible before agentic capability exists. First severe
incident 2026; median year 2029. The early decade is embarrassment, the late
decade is liability.

*Safety is a real decision, not a tax.* 84 paired lab-runs (12 seeds x 7
labs), careless against diligent, same lab, same world, same seed:

```
             ARR $B  trust   minor   mod   sev   incident $B   safety $B
  careless    121.3    6.3    2698  1436   105        3820.6         0.0
  diligent    148.3   32.7     306   175    17         975.0       244.4

  paired delta in 2030 ARR (diligent - careless), $B
    p10  -50.5    p25  -7.3    median  +19.1    p75  +58.4    p90  +145.9
    mean +27.0    diligence ahead in 51 of 84 pairs
```

Positive on average, positive at the median, **negative at p10 and p25**.
Insurance you resent paying — which is the stated target.

*Calibration survived.* 15/16 checkpoints inside +/-18 months, median offset
-10, mean |offset| 9.4, order 111/120. (Was 16/16 and 113/120 before; the
difference is a different random realisation, not a regression — see the RNG
note below.) Strategy goal attainment is unchanged: all eleven still score in
the same band.

**Not verified, and worth saying plainly.**

Every number in the safety block is a judgment call. There is no reference
class for a severe AI incident, so nothing anchors the cost of one. The
*structure* is defensible and is what produces the behaviour; the magnitudes
were tuned until the posture was a decision rather than a tax. See
`PREMISES.md`, structural issue 2.

The one checkpoint now outside the band is "an enterprise agent market opens"
at -24 months. It was inside before this session. I believe that is the RNG
realisation rather than the regulation gate lift — regulation is still 0 in
2023, so it cannot be touching that milestone — but I did not prove it, and
it is the first thing to check if the next session sees agentic markets
opening too early.

## Where the bodies are buried

Things that cost real time this session and that will cost it again:

- **Changing an RNG draw changes the world.** `eval_rate` originally
  short-circuited on `always_eval`, so the safety-first strategy consumed
  one fewer random number per ship and every subsequent decision in the run
  diverged. Any A/B on safety posture was measuring that divergence, not
  safety. The draw is now always consumed. If you add a decision, consume
  its randomness unconditionally.
- **A/B across *all* labs measures nothing.** Making every lab careless and
  comparing run outcomes is a null experiment by construction — the relative
  standings are unchanged. The right test is paired: flip *one* lab's
  posture in an otherwise identical world, same seed, and compare that lab
  to itself. `scratchpad/ab.py` does this; it is not committed because it is
  a one-off, but the shape is worth keeping.
- **Runs are slow.** 132 monthly ticks × 7 labs. A paired A/B over 12 seeds
  is 168 runs and takes ~20 minutes. Budget for it; do not iterate
  interactively on a full sweep.

## What I would do next, in order

1. **`ROADMAP.md` item 2, the decision seam.** Policy is still baked into
   `doctrine` dicts read inline all over `world.py`. Nothing *decides*
   anything. Until `observe → decide → apply` exists there is nowhere for a
   player to plug in, and every session that adds a mechanic adds another
   inline `doctrine.get(...)` to unpick later. This is the last
   architectural change that is cheap now and expensive later.
2. **Events** (item 4) — a JSON deck, conditional on world state. Cheapest
   large gain in run-to-run variety.
3. **Demand as a labour market, not a spend ceiling** (`PREMISES.md`
   structural issue 2). The late game is where the interesting decisions
   are and it is the weakest part of the model.

## Standing instructions from Nick, for the record

- Develop on `claude/ai-race-game-plan-vl6gi3`; never push elsewhere
  without asking. No PR unless explicitly requested.
- This is a personal project. Fidelity first: *"model this world really
  really well, the game is the player's window into the simulation."*
- Real units everywhere. Abstract "compute units" were rejected explicitly.
- Calibration does not need to be exact — *"this is an alternate universe,
  kind of"* — but it must stay inside an order of magnitude, and timing is
  the instrument, not magnitude.
- Target feeling: *"staring at benchmarks pissed they lost on AA by 2
  points, seeing how long they can burn cash on inference."*
