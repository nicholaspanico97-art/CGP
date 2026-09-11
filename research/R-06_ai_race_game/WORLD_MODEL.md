# Frontier — World Model v0.2

**What changed:** the paper prototype (`PAPER_PROTOTYPE.md`) is superseded.
Nick's direction, Sep 11 2026: *model the world really well, run the sims,
and make the game a window into that simulation.* Abstract "compute units"
are gone. Everything below is in real units and is calibrated against the
2020–2026 record.

**v0.2, Sep 11 2026 — domains and data.** A model is not one number. It is
a profile across capability domains, each bought with a different mixture of
compute *and data*, and the market is segmented with each segment gated on a
domain. This is the structural reason a niche leader survives a frontier leap
somewhere else. Calibration improved from 2.6x to **1.58x** typical error in
the process — segmentation made the economics more accurate, not less.

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

## 2b. Domains, data, and segmented markets

### Eight domains
`LANG` · `REASON` · `CODE` · `AGENT` · `IMAGE` · `VIDEO` · `AUDIO` · `ROBOT`

A training run has a **mixture** over domains. Capability in each:

```
C_domain = log10(effective_flop x mixture_weight)
         + log10(data_sufficiency)
         + 0.6 x log10(data_quality)
```

Compute you point at a domain you have no data for is compute you set on
fire. A domain with weight zero produces no capability at all, and no
product.

### Data is a market, not a stat
Ten sources, each with real volume, quality, cost, lead time, legal risk,
and a mix over domains:

| Source | Volume | Quality | Cost | Exclusive |
|---|---|---|---|---|
| Open web crawl | 32T tok | 0.70 | free | no |
| Books, papers, reference | 1.6T | 1.35 | $180k/Btok | no |
| Public code repositories | 2.1T | 1.15 | $20k/Btok | no |
| Forum & social licence | 1.3T | 0.90 | $60M/yr | **yes** |
| News & periodical licence | 260B | 1.45 | $160M/yr | **yes** |
| Licensed image & footage | 600B | 1.30 | $90M/yr | **yes** |
| Video platform corpus | 24T | 0.85 | $400M/yr + extraction FLOP | **yes** |
| Speech & call-centre | 200B | 1.20 | $45M/yr | **yes** |
| Expert annotation | 30B | **3.40** | $42M/Btok | **yes** |
| Simulated environments | 10T | 0.95 | FLOP, not dollars | no |

Free sources yield ~15T effective language tokens — which is what real
frontier runs use — and **exactly zero** video, audio or robotics data.
Those capabilities have to be bought.

Three mechanisms make data behave like the real thing:

- **Repetition has limits.** Below sufficiency you re-read the corpus; past
  ~4 epochs the returns stop. A data-poor domain wastes the compute
  pointed at it.
- **Exclusives are auctioned on strategic value, not size.** A bid is
  capped by `ask x (1 + 7 x mixture_overlap)`. A rights holder takes the
  higher bid, and a specialist's bid for the corpus its whole business
  depends on can beat a giant's bid for something it would weight at 7%.
- **Telemetry cannot be bought.** Usage becomes training data in the
  domains your customers actually use. This is the only source a
  competitor cannot buy into, and it is why an incumbent's lead compounds
  specifically in the segments it already leads.

Synthetic data is unlimited, costs FLOP, and its quality is capped at 0.92
of the generating model's level — you can amplify what you have, not
bootstrap past yourself.

### Nine segments, each gated on a domain
Gates are calibrated so a segment opens in the quarter its real product
category appeared: the consumer assistant in late 2022, video generation in
2024, robotics in 2025.

| Segment | Gate | Share of ceiling | Differentiation |
|---|---|---|---|
| Consumer assistant | LANG 25.2 | 30% | 0.30 |
| General API | LANG 23.2 | 16% | 0.00 |
| Coding & software agents | CODE 24.2 | 22% | 0.06 |
| Enterprise agents | AGENT 25.8 + REASON 26.0 | 14% | 0.22 |
| Scientific & technical | REASON 26.3 | 5% | 0.10 |
| Image generation | IMAGE 24.4 | 5% | **0.55** |
| Video generation | VIDEO 25.7 | 5% | **0.50** |
| Voice & audio | AUDIO 24.7 | 2% | **0.45** |
| Embodied & robotics | ROBOT 26.5 + AGENT 26.8 | 1% | 0.15 |

**Differentiation** is how much of a segment is decided by something other
than raw capability — taste, style, workflow, ecosystem. At zero the best
benchmark takes the market; high, a smaller specialist holds ground against
a rival an order of magnitude ahead on compute. Creative work sits high;
price-per-token API sits at zero.

Below a gate you have no product, not a worse one. Above it you compete on
that segment's quality weighting alone — which is why AGI-grade coding does
not touch an image-generation business.

### Does it work?
A 2030 run with a deliberately included media specialist (`Lumen`, starting
with 3,500 accelerators against a hyperscaler's 26,000):

- **Lumen ends at $46.9B/yr**, leading video generation and second in
  image, with **zero** revenue in language, coding, reasoning or agents. It
  has no coding business and does not need one.
- **Redshift holds 100% of robotics** — the only lab that put mixture
  weight on `ROBOT`.
- The two generalist giants end near-tied at ~$328B each, and neither one
  can take the creative segments.

## 3. Calibration

Scored as mean `|log10(model/actual)|` across four independent families,
against `sim/anchors.py` — every figure a public estimate, tagged
HIGH/MED/LOW.

| Family | Error | Typical | Notes |
|---|---|---|---|
| Capex | 0.111 | **1.3x** | |
| Power | 0.223 | 1.7x | Was the worst family at 4.9x before segmentation |
| Frontier run size | 0.228 | 1.7x | |
| Revenue | 0.210 | **1.6x** | 2022 lands at $0.40B vs $0.40B; 2023 $3.9B vs $2.6B |
| **Weighted** | **0.198** | **1.58x** | |

Every free parameter that could be calibrated was swept against the anchors
rather than chosen. The per-ship run-growth ceiling has a clear interior
optimum at 2.4x and is the single most sensitive parameter in the model.

Benchmarks are fitted separately: one saturating curve per suite against
15 reported scores, **mean absolute error ~1.9 benchmark points**.

Within ~1.6x across four independent families, over a decade whose true
figures are mostly unpublished, is a fit worth building on. It is not a
claim of predictive accuracy.

### Known residuals, in priority order
1. **Only three of eight domains are anchored.** `MMLU`/`GPQA`/`SWE` are
   fitted to 15 real scores. `IMAGE`, `VIDEO`, `AUDIO`, `ROBOT` and `AGENT`
   use **hand-set curves** — structurally reasonable, empirically
   unsupported. Every report flags them. This is now the biggest gap.
2. **Power still undershoots ~1.7x** in the mid-decade.
3. **Revenue overshoots from 2023** (~1.5x), for lack of enterprise
   adoption friction — procurement, security review, integration.
4. **Data source figures are the least grounded numbers in the model.**
   Volumes and qualities are order-of-magnitude judgments; the licence
   costs are anchored on a handful of reported deals.
5. **Structural realism cost some historical fit, deliberately.** Bounding
   private algorithmic advantage at 4x and letting capability advantage
   saturate in buyers' eyes keeps 2027–30 from collapsing to one winner.

## 4. What the model says about the back half

With no player and seven scripted doctrines, 2030 comes out as: **157 GW**
of AI load, a **1.1e29 FLOP** frontier run, **~$827B** sector revenue,
two near-tied generalists at ~$328B each, a robotics monopolist, and a
creative-media specialist at $47B that never sold a line of code. The leader's private
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
sim/domains.py      8 domains, 10 data sources, 9 gated market segments
sim/scenarios.py    seven lab doctrines and mixtures, Jan 2020 positions
sim/score.py        calibration error across all anchor families
sim/fit_report.py   capability curve fit and residuals
```

Deterministic and dependency-free. `results_calibration.txt` is the current
committed output.

## 6. Next

1. **Anchor the other five domains.** Find or construct public score
   histories for image, video, audio, agentic and embodied capability, and
   fit those curves instead of hand-setting them.
2. **Fix power** — site-level contracting, a grid queue that is a queue.
3. **Adoption friction** on the enterprise channel.
4. **Talent, safety and regulation** — designed in `DESIGN.md`, not yet in
   the model.
4. **The player.** Only once the world stands up on its own: the game is a
   window onto this, and the window comes last.
