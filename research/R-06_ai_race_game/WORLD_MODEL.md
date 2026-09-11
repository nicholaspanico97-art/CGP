# Frontier — World Model v0.1

**What changed:** the paper prototype (`PAPER_PROTOTYPE.md`) is superseded.
Nick's direction, Sep 11 2026: *model the world really well, run the sims,
and make the game a window into that simulation.* Abstract "compute units"
are gone. Everything below is in real units and is calibrated against the
2020–2026 record.

**Status:** running. `sim/` is a zero-dependency Python model, 2020→2030,
monthly ticks. `python3 -m sim.score` prints the calibration error;
`python3 -m sim.fit_report` prints the capability fit.

---

## 1. Units

| Quantity | Unit | Why it matters |
|---|---|---|
| Training compute | **FLOP** | GPT-3 was 3.1e23; a 2030 run in this model is ~1e29. Six orders of magnitude — no abstraction survives that span |
| Fleet capacity | **FLOP/s**, accelerators by generation | Determines how long a run takes, which is the real scheduling constraint |
| Power | **watts / MW / GWh** | Binding from ~2026. The model has 104 GW of AI load in 2030 |
| Money | **nominal USD** | Capex, opex, revenue, valuations, debt |
| Data | **tokens** | Chinchilla ratios are a strategic choice, not a constant |
| Serving | **$/Mtok**, tokens/s | The margin line the whole late game runs on |
| Time | **months** internally, quarters surfaced to the player | Runs finish and hardware lands between turns |

## 2. The chain

Each link is a place to spend money and get something different back:

```
pretraining FLOP              bought with accelerators x time
  x algorithmic efficiency      sector-wide progress + a bounded private edge
  x reasoning multiplier        post-training RL, and FLOP per query at serve time
= effective compute
-> capability C = log10(effective FLOP)
-> benchmark scores, one saturating curve per suite
```

C is literally the base-10 log of a FLOP count. C = 26.8 means 6.3e26
effective FLOP, and the gap between 26.8 and 27.8 is exactly one order of
magnitude. Nothing is on an invented scale.

### Calibrated sub-models

- **Scaling.** `C = 6ND` with `D = r·N`. Given a compute budget and a
  token-per-parameter ratio, the model's shape falls out. At 3.1e23 FLOP
  and r=1.7 the model returns 174B parameters on 296B tokens — GPT-3 was
  175B on 300B. At 3.8e25 and r=37 it returns 414B on 15.3T — Llama 3.1
  405B was 405B on 15T. Neither number was typed in.
- **Recipes are dated knowledge.** A lab in 2020 cannot pick a Chinchilla
  ratio, because nobody had worked it out; it cannot serve a sparse
  mixture, because nobody could train one at scale. `RECIPE_ERA_*` gates
  these, and a lab whose research runs ahead of the field reaches each
  recipe early. This was one of three things that made the first honest
  run of the simulation wrong.
- **Runs are engineering, not just money.** The largest run a lab can land
  grows ~1.5x per shipped model (calibrated), never 100x, because the
  failure modes at each new scale have to be learned. Combined with a
  post-ship cooldown for post-training, evals and launch, this reproduces
  a 12–18 month frontier cadence.
- **Serving cost from first principles.** ~2.1 FLOP per active parameter
  per token, divided into an accelerator's realized serving throughput,
  against its all-in monthly cost. An H100 costs $678/month all-in
  ($0.93/hr) and serves a 70B-active model at ~1,680 tok/s for $0.34/Mtok.
  A 2023-era 280B-active model on A100s costs $2.48/Mtok — against a $37.50
  list price, which is why that era's margins were what they were.
- **Price is cost-plus, competed away.** Markup is `1.25 + 11/(1+2.2n)`
  where n is the number of rivals within half an OOM of your capability.
  One lab with the only frontier model charges accordingly; a dozen
  near-substitutes collapse the markup toward the cost of the iron.
- **Capital is modeled, not assumed.** Story valuations before revenue,
  revenue multiples expanding from 20x to 65x, corporate parents funding
  from operating cash flow, and — from mid-2024 — infrastructure debt
  against contracted revenue. That last one is what actually unlocked the
  gigawatt era; without it the simulation cannot build 2025.
- **Power has two doors.** Greenfield at 20 months (34 after the
  interconnect queue arrives in 2025) and $9.5M/MW, or leased colocation
  at 9 months and $105k/MW/month forever. Most of the 2023–25 buildout was
  leased, because a 34-month queue cannot produce a 2024 cluster.
- **Demand is bounded by budgets, not capability.** An unbounded demand
  curve sent 2026 revenue to $491B against an observed $62B. Sector spend
  now saturates against an addressable-budget ceiling.

## 3. Calibration

Scored as mean `|log10(model/actual)|` across four independent families,
against `sim/anchors.py` — every figure a public estimate, tagged
HIGH/MED/LOW.

| Family | Error | Typical | Notes |
|---|---|---|---|
| Frontier run size | 0.320 | **2.1x** | GPT-4 lands at 2.0e25 vs 2.1e25; o1 at 1.01e26 vs 1.0e26 |
| Capex | 0.379 | 2.4x | Right shape, ~2x light in 2022–23 |
| Revenue | 0.554 | 3.6x | Right shape and timing; overshoots 2025 |
| Power | 0.692 | **4.9x** | **Weakest family.** Consistently 2–3x under |
| **Weighted** | **0.472** | **3.0x** | |

Benchmarks are fitted separately: one saturating curve per suite against
15 reported scores, **mean absolute error ~1.9 benchmark points**.

**This is a v0.1 fit, not a good one yet.** Being within ~3x on a decade of
an industry whose true figures are mostly unpublished is a reasonable
starting point and nothing more. The honest reading: compute and capability
are well-modeled, money is approximately modeled, and power is not modeled
well enough.

### Known residuals, in priority order
1. **Power undershoots 2–3x.** Labs contract too conservatively. The
   lookahead multiple is a single crude number where reality is a
   negotiation over specific sites.
2. **2025 revenue overshoots ~2.5x.** Adoption friction — procurement
   cycles, security review, integration work — isn't modeled at all.
3. **Capex is light in 2022–23**, before the debt channel opens.
4. **Structural realism cost 6% of historical fit.** Bounding private
   algorithmic advantage at 4x and letting capability advantage saturate
   in buyers' eyes made 2020–26 fit slightly worse and made 2027–30 stop
   collapsing to a single winner. That trade was taken deliberately.

## 4. What the model says about the back half

With no player and six scripted doctrines, 2030 comes out as: **~104 GW**
of AI load, a **1e29 FLOP** frontier run, **~$1.26T** sector revenue, and a
leader at **71% share** with five labs still alive. The leader's private
efficiency edge sits at 3.6x — bounded, because you cannot out-research the
whole world by orders of magnitude in secret.

The 2027–30 spend ceiling (~1.75x/yr) is an assumption and is the single
biggest lever on how the back half feels. It should be a scenario axis, not
a constant.

## 5. Files

```
sim/constants.py    physical and economic constants, confidence-tagged
sim/anchors.py      the 2020-2026 record: what actually happened
sim/capability.py   scaling, efficiency, reasoning, benchmark curves
sim/economics.py    hardware, fleets, serving cost, demand
sim/world.py        labs, the market, capital, power, the monthly tick
sim/scenarios.py    six lab doctrines, January 2020 starting positions
sim/score.py        calibration error across all anchor families
sim/fit_report.py   capability curve fit and residuals
```

Deterministic and dependency-free. `results_calibration.txt` is the current
committed output.

## 6. Next

1. **Fix power.** Site-level contracting with real lead times, and a grid
   queue that is a queue rather than a constant.
2. **Adoption friction** on the enterprise channel, to kill the 2025
   revenue overshoot.
3. **Talent, safety and regulation** — designed in `DESIGN.md`, not yet in
   the model.
4. **The player.** Only once the world stands up on its own: the game is a
   window onto this, and the window comes last.
