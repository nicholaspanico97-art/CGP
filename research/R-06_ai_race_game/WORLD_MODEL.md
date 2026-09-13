# Frontier — World Model v1.4

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

**v0.4, Sep 12 2026 — uncertain runs and the release ratchet.** A training
run no longer returns what the scaling law says; it returns that times how
the run actually went. And a lab never ships a model worse than the one it
already sells, so that variance shows up as *flat stretches and jumps*,
never as capability going down. Plus talent (v0.3), demand unlocked by
capability rather than by the calendar (v0.3), and a `COMPETITIVENESS` dial
that trades a little fidelity for a much more contested race.

**v1.4, Sep 13 2026 — the decision seam.** Nothing in `sim/` decided
anything: the tick read each lab's parameters inline out of a `doctrine`
dict, so policy and physics were the same code. Now every month each lab
observes, its policy decides, and the world applies — validated and
logged. The eleven strategies are policies; a player is one more. The
log plus the seed is a saved game, and replaying it reproduces the run
bit for bit. See §2g.

**v1.3, Sep 12 2026 — safety, incidents and regulation.** `safety_debt`
used to accumulate and do nothing, which made shipping without
evaluating strictly free. Three severity tiers now fire, with frequency
driven by sloppiness and deployment surface and severity gated on what
the models can actually *do*. A severe incident regulates the whole
sector, not just the lab that caused it. See §2f.

**v1.2, Sep 12 2026 — capability transfer between domains.** See
`PREMISES.md`.

**v1.1, Sep 12 2026 — timing replaced magnitude as the calibration
instrument**, and immediately found a hard run-size ceiling that had
been deciding outcomes in 73% of lab-months while the model claimed
compute was the constraint. See `PREMISES.md`.

**v1.0, Sep 12 2026 — the observability seam.** Labs no longer read the
world's true state. Each forms beliefs about rivals from visible signals,
with error bars, and every decision runs on the beliefs. That makes
misrepresentation worth doing and produces an arms-race spiral as an
emergent result rather than a scripted one. See §2e.

**v0.9, Sep 12 2026 — the AA index**, one number for where the frontier is,
built by inverting each suite's score back to the difficulty it implies so
that it does not saturate when the suites underneath it do. Plus per-model
evaluation noise, and a calibration score that finally averages over seeds.
See `ROADMAP.md` for what is still missing before a game sits on this.

**v0.8, Sep 12 2026 — benchmarks became measurements.** Capability is now a
difficulty frontier and a benchmark is a distribution over task difficulty,
so saturation, suite retirement, elicitation quality and benchmark-chasing
all fall out of one structure instead of being configured. See
`BENCHMARKS_PROPOSAL.md` for the design and the outcome.

**v0.7, Sep 12 2026 — the self-improvement loop, distillation, endogenous
algorithmic progress.** See the commit log.

**v0.6, Sep 12 2026 — each strategy is scored on its own goals.** Revenue
share was the wrong scoreboard. An open-weights lab is not trying to
out-earn an enterprise vendor; it is trying to keep the field close and stay
the developers' default. Every strategy now carries its own objectives and
balance is measured against those.

**v0.5, Sep 12 2026 — strategies.** A lab is no longer a parameter bundle,
it is a set of intentions. Eleven strategies (fifteen counting the vertical
specialist's focus variants), each with variation drawn per game, assigned
at random and not disclosed. Some of them deliberately decline to ship.

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

## 2c. Runs, releases, and the ratchet

### A run is a bet, not a calculation
On completion, a run draws an outcome multiplier on effective compute:
ordinary spread of ±0.105 OOM, a 6% chance of a **breakthrough** (+0.44 OOM
— an architecture bet that transfers), a 13% chance of a **dud**. Strong
teams see a narrower distribution in both directions; a lab that is behind
takes bigger swings, because matching the leader is not good enough when
you are losing.

### Labs do not ship backwards
A completed run whose model is not better than what the lab already sells
is **shelved**. The compute is spent, the engineering lesson is kept — the
lab can still attempt a bigger run next time — and the shipped capability
stays flat. About 15% of runs end this way.

This asymmetry is the whole design. Variance plus a no-regression rule
produces a **ratchet**: long plateaus while nothing ships, punctuated by
jumps when something lands. One lab's language capability in a sample run
sits at 25.22 for seven months, then a breakthrough takes it to 26.48 in a
single release. Another sits dead flat for fourteen months in 2029.

### The x.5 release
Between pretraining runs a lab improves what it already ships one to three
times (drawn per base model), with each release worth about half the last
and post-training weighted toward the domains where RL works — reasoning,
code, agency — far more than toward image or video. Release timing jitters.
This is what gives a release history its real shape: a big jump, a couple
of small ones, a plateau, then a big jump.

*Note on double counting:* the sector-wide `reasoning_multiplier` already
absorbed post-training gains. Adding per-model releases on top double-counted
them, and the calibration sweep caught it — the fix was letting the sweep
re-split the two terms rather than hand-waving it.

### The COMPETITIVENESS dial
| Setting | Calibration | Lead changes | Dominant lab holds | Runaway runs |
|---|---|---|---|---|
| 1.0 | 1.83x | 69 | 87% | 25% |
| **1.8 (default)** | **1.85x** | **106** | **~60%** | **20%** |

Going from a coronation to a real race costs about 1% of aggregate
calibration. That sounds free, and it is not: **every anchor in this model
is sector-level** — revenue, capex, power, frontier run size — so none of
them knows *which lab* is leading. History's concentration is closer to the
1.0 setting. 1.8 is the default because the game wants a race. That is a
values choice, stated as one, and it is one line to change.

At the default, across 20 seeds: 106 lead changes per run, the top lab
averaging 46% of revenue (range 29–65%), 20% of runs ending with someone
genuinely running away, and 4.7 of 7 labs still viable in 2030.

## 2d. Strategies

Each lab draws one of eleven strategies at the start of a game, with
parameter variation inside it, so the same archetype is never quite the same
twice. The player is not told who drew what — it has to be inferred from
what a lab ships, what it charges, and what it is visibly not doing.

| Strategy | What compute is for |
|---|---|
| **Scale maximalist** | Biggest runs in the field, terrible margins |
| **Self-improvement racer** | Points compute at its own research and **hoards what it learns** |
| **Efficiency leader** | Overtrained sparse models; wins on $/Mtok, not benchmarks |
| **Open weights** | Publishes everything; lifts the whole field's efficiency |
| **Vertical specialist** | One domain — robotics, media, code, science or voice |
| **Enterprise & trust** | Slow, evaluated, expensive, and signable-off-on |
| **Consumer land grab** | Prices below cost to own the default |
| **Data monopolist** | Signs every exclusive, partly so nobody else can |
| **Fast follower** | Spends nothing on research, copies, undercuts |
| **Sovereign champion** | State capital, hard ceiling on silicon |
| **Platform incumbent** | Funds itself from a business that already prints money |

### Two mechanisms make strategies more than a parameter sheet

**Withholding.** The self-improvement racer will not release a model it
could release: shipping hands rivals a target to measure against and to
distill from, and the plan is to compound privately. It releases when the
money runs short. In a sample run one such lab **withheld for 50 months**
across the decade and shipped 10 models against rivals' 13–19, with a
visible two-year silence. While it sits, the open-weights lab racing it
cannot catch up by copying — which is exactly the dynamic this is for.

**Openness drives diffusion.** How fast algorithmic advantage spreads is now
a property of *who is in the field*, weighted by capability. An open-weights
lab lifts everyone; a field of secretive labs grinds diffusion down. That is
what a hoarding strategy is buying, and it is why the same strategy plays
differently depending on who else got drawn.

### Each strategy is scored on its own goals

`sim/objectives.py` gives every strategy two or three weighted goals in its
own terms. The efficiency leader wants to be the cheapest tokens in the
world *and still make money*; the open-weights lab wants the field kept
inside an order of magnitude and to stay the developers' default; the
self-improvement racer wants a decisive capability level and an outright
lead, and does not care about revenue beyond staying funded.

Two subtleties the scoring has to get right:

- **A lab's goals are judged on what it BUILT, not what it released.** A
  strategy whose plan is to sit on capability is not failing at capability
  because it is succeeding at sitting on it. The market still only ever sees
  what shipped.
- **Targets have to live inside the achievable range.** They were set by
  measuring the best value any lab reaches in a game, then placing the bar
  where attainment lands in a sensible band rather than at 0% or 100%.

Over 36 games:

| Strategy | Goal score | Achieved | Revenue share |
|---|---|---|---|
| Efficiency leader | 91% | 78% | **4%** |
| Vertical specialist | 91% | 89% | 13% |
| Open weights | 83% | 74% | 10% |
| Sovereign champion | 82% | 100% | 17% |
| Enterprise & trust | 77% | 72% | 13% |
| Platform incumbent | 73% | 58% | **28%** |
| Data monopolist | 72% | 69% | 23% |
| Self-improvement racer | 70% | 38% | 11% |
| Fast follower | 69% | 85% | 6% |
| Scale maximalist | 66% | 50% | 16% |
| Consumer land grab | 65% | 55% | 13% |

The efficiency leader takes 4% of revenue and succeeds 78% of the time.
That is the whole point of the reframe: it was never trying to take
revenue share. They are deliberately not even — the racer is a 38%
strategy, high risk and high ceiling; the follower is an 85% strategy that
never wins big. The sovereign champion at 100% is still too easy and is
the one target left to raise.

### Three model bugs this exposed
1. **The research lane was worthless.** Algorithmic advantage converged to
   ~1.0 for every lab (range 0.88–1.05): spending 39% of compute on
   experiments bought a 4% edge, because diffusion and renormalisation
   erased it faster than research created it. A leader's edge now erodes at
   a rate that depends on how open the field is — which is the other half
   of what a hoarding strategy is buying — and the ceiling on private
   advantage went from 4x to 7x.
2. **Capability-led strategies had no way to fund themselves.** The scale
   maximalist was spending $218B of capex against a hyperscaler's $2,416B,
   because it served few customers, so earned little, so could not raise. A
   lab at the frontier with no revenue was in fact fundable on the
   narrative for the whole 2020–2023 period; valuation now scales with
   capability, per strategy. Calibration *improved* when this was added —
   the anchors wanted that capex.
3. **No market had any memory.** Share was re-decided from scratch every
   month, so a consumer land grab could never hold a default. Segments now
   carry stickiness: a consumer habit at 0.90, an enterprise contract at
   0.88, an API call at 0.45.

## 2e. Imperfect information

Until v1.0 every actor read `lab.model.caps` directly. That made half the
model decorative: benchmark-chasing only matters if rivals cannot see your
real frontier, and hoarding only works if nobody knows what you have. The
AI opponents were implicitly cheating.

`sim/intel.py` puts a boundary in. A lab observes signals and forms a
belief per rival — a point estimate and a sigma — and decisions read the
belief.

| Public | Inferable, noisily | Private |
|---|---|---|
| Published scores, AA, prices | Fleet scale and power siting | True difficulty frontier |
| Funding rounds, valuations | Headcount | Unreleased models |
| Announced products | Months since they last shipped | Cash, runway, mixture |

The inference that matters: **silence plus a growing cluster is the
signature of a lab sitting on a breakthrough, and also of a lab that is
simply stuck.** From outside those are identical. Inference is capped at
0.55 OOM — outside observers are not omniscient, and without the cap the
2020–22 buildout has everyone believing everyone is 2.6 OOM ahead.

### Threat, and why it is biased
A lab acts on **threat**: the gap to the most alarming rival, measured
against the *upper* end of its estimate by a per-strategy paranoia. That
pessimism is the engine. Planning against the bad case means over-building,
and over-building is itself the signal that makes a rival price in theirs.
Private information plus an incentive to misrepresent is the standard
bargaining-failure setup, and this is what it produces here.

### What it costs the sector, measured

Same seeds, three worlds:

| | Sector capex | Researcher pay | Frontier reached |
|---|---|---|---|
| Perfect information, no panic | $8.4T | $375k | 34.35 |
| Uncertainty, no pessimism bias | $8.7T | $579k | 34.78 |
| **Uncertainty + strategy paranoia** | **$9.2T** | **$613k** | **34.90** |

**+9% on capex and +63% on researcher pay, purely from not knowing** — and
the frontier ends **0.55 OOM higher** for it. The arms race accelerates
progress precisely because nobody can see what anyone has. The pay result
is the sharper one: fear shows up in the talent market before it shows up
in concrete.

Across twelve games: labs over-estimate the frontier by **+0.69 OOM** on
average (sd 0.83), spend **86% of lab-months believing they are losing
badly**, and **27% of lab-months fearing the wrong rival** — pouring money
into catching someone who is not actually ahead.

### Where the spiral is allowed to act
The anchors pin release *pace* tightly, so routing panic through the
cooldown wrecked the fit on its own (1.68x → 2.15x): the historical record
is consistent with labs not panicking much about cadence. But nothing in
the anchors says how much a frightened lab overpays for researchers, bids
for a corpus, or gambles on an architecture. Routed through those, the
`SPIRAL` dial is **fidelity-neutral** — flat at 1.74–1.78x from 0.6 to 1.5,
and slightly better than switching it off. Set `SPIRAL = 0` for a
no-panic run.

## 2f. Safety, incidents and regulation

Until v1.3 `safety_debt` accumulated and did nothing. Shipping a model
without evaluating it was strictly free, which meant every strategy should
have done it, and a player would have worked that out in three turns.

The design separates two questions that are usually collapsed into one
"risk" number, and keeping them apart is the whole point:

| | driven by |
|---|---|
| **How often** something goes wrong | deployment surface, safety debt, and how big a capability jump you shipped without evaluating |
| **How bad** it is when it does | what your models can actually **do** in the world |

The second is the one that carries the design. A chat assistant that
misbehaves is a news cycle. The same misalignment in something that books
travel, runs shell commands and calls APIs unsupervised is an economic
event. In a system with real autonomy over real infrastructure it is a body
count. So severity is gated on **AGENT capability** and on **how much
agentic product is actually deployed** — not on how sloppy the lab has
been. Sloppiness changes the odds; capability changes the ceiling.

### Three tiers

| Tier | What it is | What it costs |
|---|---|---|
| **MINOR** | anomalous behaviour, embarrassing, makes the news | trust −6 |
| **MODERATE** | agents reach something they should not: a service defaced, a system compromised, money lost | trust −14, ~0.9 months of revenue + $90M, legal exposure |
| **SEVERE** | real-world consequence through action — infrastructure, medical systems, physical harm | trust −26, ~3.2 months of revenue + $1.4B, barred from agentic segments for 15 months, **and the whole sector gets regulated** |

Catastrophic, world-ending outcomes are deliberately out of scope for now.

### The hazard

```
p(month) = INCIDENT_BASE
         × (0.35 + log10(1 + served_Mtok/1e4))      deployment surface
         × (1 + INCIDENT_JUMP_GAIN × unevaluated_jump)
         × (1 + INCIDENT_DEBT_GAIN × safety_debt)
```

A model nobody uses cannot embarrass you. The jump term is the real driver:
shipping a large capability increase you have not evaluated is where the
surprises live. Evaluating covers 85% of the jump you just shipped; skipping
it adds 2.0 points of debt, and debt also drifts up 0.035/month just from
operating a deployed system. Safety spend retires debt at $22M per point.

### Severity, given trouble

```
w_minor    = 1
w_moderate = (0.10 + 1.25·h) · sloppy
w_severe   = SEVERE_SCALE · h² · (0.20 + 0.80·exposure) · sloppy
```

where `h` is harm potential — AGENT capability ramped between 26.5 (agents
that can use tools at all) and 32.0 (agents that act unsupervised) — and
`exposure` is the share of revenue coming from products that *act* rather
than answer. You cannot take down a grid with a product nobody has pointed
at anything, so severe needs **both** the capability and the deployment.

The consequence is the gradient the design asked for, measured over 24
seeded runs:

```
  era          minor  moderate  severe   severe share
  2019-2021       83        11       0             0%
  2022-2024      218        33       0             0%
  2025-2027      154        71       5             2%
  2028-2030      110       150      16             6%
```

Nothing severe is even *possible* before agentic capability exists. The
early decade is embarrassment; the late decade is liability.

### Regulation, and why it is sector-wide

A severe incident raises `world.regulation` by 0.55, decaying 1.5%/month.
Regulation does two things: it adds `0.30 × regulation` OOM to the gates on
agentic segments (enterprise agents, robotics, coding), and it costs every
lab 4.5% of revenue per unit in compliance. The offending lab is separately
barred from those segments for 15 months.

This is the mechanism that makes one lab's recklessness everyone's problem,
which is the thing that actually happens and the thing that makes a
safety-first rival's complaints about a reckless one more than flavour text.

### Does safety pay?

This is the question the pillar exists to answer, and it took three wrong
attempts to measure honestly. The instrument that works is **paired**: flip
*one* lab's safety posture in an otherwise identical world on the same seed,
and compare that lab to itself. Comparing worlds where *every* lab is
careless against worlds where every lab is diligent is a null experiment by
construction — the relative standings do not move.

84 paired lab-runs, 12 seeds x 7 labs, careless (`safety_spend` 0,
`eval_rate` 0.05) against diligent (0.9 / 0.95):

```
             ARR $B  trust   minor   mod   sev   incident $B   safety $B
  careless    121.3    6.3    2698  1436   105        3820.6         0.0
  diligent    148.3   32.7     306   175    17         975.0       244.4

  paired delta in 2030 ARR (diligent - careless), $B
    p10  -50.5    p25  -7.3    median  +19.1    p75  +58.4    p90  +145.9
    mean +27.0    diligence is ahead in 51 of 84 pairs
```

Diligence buys **8.5x fewer incidents** and costs $244B to do it. The mean is
strongly positive and the median is clearly positive — but the **p10 and p25
are negative**. A quarter of the time you would have been better off not
paying.

That is the shape the design wanted. It is insurance you resent paying: worth
buying, obviously worth buying on average, and often visibly a waste in the
run you are actually in. A safety budget that always paid would not be a
decision; a safety budget that never paid would be a tax nobody should pay.

The careless column also shows *why* it is not free: trust 6.3 is the floor.
A lab that never evaluates ends the decade with no reputation at all, which
in the enterprise segment (`brand_weight` 1.4) is most of the market gone.

### Trust heals, but scars

Trust was a one-way ratchet in the first draft, which pinned every lab at
the floor of 5 by mid-decade and made incidents free after the first one.
It now heals toward a baseline of 55 at 5.5% of the gap per month, slowed by
`1/(1 + 0.11 × incidents_on_record)`. A clean lab recovers from a bad
quarter; a lab with a history does not get the benefit of the doubt. Trust
enters segment share through `brand_weight`, which is 1.4 in enterprise and
0.4 in the undifferentiated API market — reputation is worth most exactly
where the contracts are largest.

## 2g. The decision seam

Until v1.4 a lab did not decide anything. `world.py` reached into
`lab.doctrine` wherever it needed a number — the compute split, the price
stance, how hard to panic — so the physics of the world and the policy of
the labs were one body of code, and there was nowhere for a player to plug
in. `sim/policy.py` separates them:

```
obs     = world.observe(lab)        # own books in full; rivals as beliefs;
                                    # the market as it was published
actions = lab.policy.decide(obs)    # a strategy AI, or a human
world.apply(lab, actions)           # validated, logged, in force
```

**What is a decision and what is identity.** `Actions` carries everything a
lab *chooses* each month: the compute split; the run window and recipe
(tokens per parameter, sparsity, test-time compute); the training mixture;
release cadence; benchmark chasing; which corpus to license and what to bid
at auction; price stance and loss-leading; hiring appetite and the
compensation actually offered; safety spend; capex aggression, power
lookahead, lease-vs-build; when to raise and how much to sell; intel spend;
openness. `doctrine` keeps what a lab *is* — its strategy, researcher
quality, corporate parent, geopolitical supply share, paranoia, its first
run — and the world reads only those.

**The release interrupt.** One decision cannot be standing: a run lands
mid-month with an outcome nobody knew in advance. `decide_release` is asked
right then, result in hand — *ship it, or sit on it; and if shipping, run
the real evaluation first or carry the debt.* A game surfaces this as a
modal; a strategy AI answers from a rule. A held model is re-asked every
month, and a held model that is finally released now faces the same eval
question as any other (before v1.4 it skipped it).

**The spiral is now something a lab does.** Fear compressing the run
window, bidding up compensation, raising capex aggression, widening the
wallet at a data auction — all of it moved out of the world and into
`DoctrinePolicy`, where it reads `obs.threat`. A player gets no automatic
panic. The world still prices the *consequence* of over-reach (the ambition
term in the outcome distribution); it no longer decides the over-reach.

**Two proofs.** First, the mechanical refactor was checked bit for bit:
`DoctrinePolicy` reproduces v1.3 exactly on three full exports and the
five-seed checkpoint table. Second, and the one that matters going forward:
`ReplayPolicy` replays a recorded action log with no access to the doctrine
or the observation, and a replayed game matches the original exactly. Any
future mechanic that reaches around the seam and reads `doctrine` for a
choice will show up there as a divergence. `python3 -m sim.replay` runs it.

**A policy has its own dice.** Policies draw from `lab.rng_policy`, a fifth
stream the world never touches, so the world's realisation cannot depend on
how a policy decided — a human draws nothing, a replay draws nothing, the
run is the same run. This moved the per-release evaluation roll off
`lab.rng`, which changed the realisation of every run. Calibration was
re-measured over seeds: 15/16 inside ±18 months, median −10, mean |offset|
9.4, order 113/120 — the same standing.

**What the log is.** `World.action_log` is `(month, lab, what changed)`,
diffs only, plus every release interrupt. With the seed it is the whole
game: save, resume, replay, and — later — run a strategy against a recorded
game to see whether it would have done better.

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
| **Weighted** | **0.266** | **1.85x** | |

(v0.2 scored 1.58x. Talent, capability-driven demand and run variance each
cost a little aggregate accuracy and each bought a mechanism the model
needed. Power remains the worst family and the top fix.)

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
sim/policy.py       the decision seam: Observation, Actions, Policy,
                    DoctrinePolicy (the strategies), ReplayPolicy
sim/replay.py       record -> save -> replay, must match bit for bit
sim/domains.py      8 domains, 10 data sources, 9 gated market segments
sim/talent.py       researchers, stars, and the people-to-compute shift
sim/release.py      run outcomes, the ship decision, x.5 releases
sim/tasks.py        benchmarks as task-difficulty distributions
sim/objectives.py   what each strategy is actually trying to do
sim/intel.py        what a lab can see: beliefs, error bars, threat
sim/strategy.py     eleven strategies, drawn per game and not disclosed
sim/safety.py       the incident hazard, three severity tiers, regulation
sim/checkpoints.py  TIMING calibration - the primary instrument
sim/balance.py      multi-seed instrument: is it a race, and did each
                    strategy reach its own goals?
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
