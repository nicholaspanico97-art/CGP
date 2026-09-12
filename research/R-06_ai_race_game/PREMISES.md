# Do the premises make sense?

Written Sep 12 2026, at Nick's prompting: *stop optimising the fit and audit
what the model is actually claiming.* This is that audit, sorted by how much
I would defend each claim.

It also records a change of instrument, because the old one was asking the
wrong question.

---

## The instrument was wrong

Calibration was `mean |log10(model/actual)|` at fixed calendar dates. On a
curve rising about an order of magnitude a year, **being six months early
reads as a 0.5 OOM error** — indistinguishable from being genuinely
misshapen. For an alternate-universe sim that is not an error at all, so the
metric was penalising precisely the thing that does not matter.

`sim/checkpoints.py` asks instead: **for each capability or economic
checkpoint, when did the sim reach it, and how many months is that from when
the world reached it?** Signed, because early and late are not symmetric — a
campaign whose consumer market opens in 2020 has lost its opening act, while
one that opens in 2024 is only slow.

Current standing: **16/16 checkpoints inside ±18 months**, median offset −6
months, mean absolute offset 8.4 months, worst −16.

And a second criterion that matters more than dates: **order**. 115 of 120
checkpoint pairs fire in the right sequence. A world where hard software
tasks fall before a consumer assistant exists is a *different world*; one
where everything happens a year late is the same world running slow.

The magnitude score is kept as a secondary check that nothing is off by an
order of magnitude. It is not the target any more.

## Two premises the new instrument caught immediately

**1. Compute was not the binding constraint — and the model's whole thesis
is that it is.**

Run size was `min(what the fleet can do, last run x a growth ceiling)`.
Checking which side bound revealed the ceiling was deciding it in **73% of
lab-months**. A lab could hold five million accelerators and still plan a
modest run; in 2030 one could have run 2.2e29 FLOP and was capped at 3.6e28.

That makes the entire capex, power and capital half of the model nearly
decorative. Worse, it was invisible to the magnitude metric *because the
ratchet had been tuned to reproduce historical run growth* — a fitted
parameter quietly doing the job a mechanism was supposed to do. That is the
most instructive failure in this project so far.

Now compute is the constraint and over-ambition is a **risk**: reaching far
past anything you have landed widens the outcome distribution and raises the
odds the run comes apart. Labs did attempt big jumps and did sometimes eat
them. Run size is now compute-limited in 100% of lab-months; median ambition
is 1.09x the last landed run, with the 90th percentile at 2.8x.

**2. A lab was pointing its entire training lane at one model.**

Real labs run the frontier model alongside ablations, smaller production
models, distillation targets and restarts. Modelling one run consuming the
whole lane made every frontier model roughly twice the size it should be.
`FRONTIER_RUN_SHARE = 0.30` now, and the timing offsets moved from 10/16 in
band to 16/16.

---

## What I would defend

- **6ND scaling and Chinchilla token ratios.** Published. The model
  independently reproduces GPT-3's and Llama-3-405B's shapes from FLOP
  budgets alone.
- **Serving cost from FLOP per token.** Arithmetic over published hardware
  specs. An H100 at $678/month all-in serving a 70B-active model at
  ~1,680 tok/s for $0.34/Mtok is a calculation, not a guess.
- **Power, lead times, and the interconnect queue.** Public.
- **Data as a real constraint with epoch limits.** Published; the free
  corpora yielding ~15T effective language tokens matches what real frontier
  runs use.
- **Benchmarks as distributions over task difficulty.** Structurally sound,
  fits better than the sigmoid it replaced, and makes saturation and suite
  retirement fall out instead of being configured.
- **Imperfect information causing over-investment.** A standard result, and
  the magnitudes it produces (+9% capex, +63% researcher pay) are plausible.

## What is a guess wearing a parameter's clothes

Stated so nobody mistakes these for findings:

| Parameter | Value | Basis |
|---|---|---|
| `IDEA_DIFFICULTY` | 0.6 | None. Huge lever on the whole back half |
| `RSI_THRESHOLD` / `RSI_MAX_FACTOR` | 32.2 / 9x | Invented. Nothing constrains either |
| Talent elasticity shift | 0.78 → 0.16 | My claim about the decade, no data |
| Five of eight domain curves | hand-set | No public score history behind them |
| `LATENT_MAX` | 0.55 OOM | Judgment about what outsiders can infer |
| `SPEND_PER_OOM` | 0.45 | Fitted to revenue, but unidentified |
| Fitted "broken item" fractions | 0.14–0.18 | Above published label noise (0.05–0.08), so absorbing something else |
| `HARM_FLOOR` / `HARM_CEILING` | 26.5 / 32.0 | Judgment about where agency becomes dangerous. Decides the whole shape of the late decade |
| `SEVERE_SCALE` | 0.42 | Invented. Sets how often the worst tier fires at full harm potential |
| `INCIDENT_BASE` and the cost tiers | 0.010, 0.9x/3.2x revenue | Tuned so that safety posture is a decision rather than a tax. No empirical basis — there is no reference class for a severe AI incident |
| `SAFETY_SPEND_PER_POINT` | $22M/point/month | Invented entirely |

## What may be structurally wrong

Ordered by how much I think it matters.

**1. ~~No capability transfer between domains.~~ FIXED — see `sim/domains.py`
`TRANSFER`.** Capability now transfers: `TRANSFER[source][target]` is the
fraction of compute pointed at source that also counts toward target, added
in effective-compute space before the log.

Two rules make it behave:

- **A modality must be present to receive transfer.** A text-only model does
  not acquire image generation from having read a great deal — with no pixels
  in the mixture there is no encoder for them. Skills inside text are
  different: reasoning and code are not separate senses, so a lab that never
  aimed at agency still has some.
- **Transferred capability needs less data to elicit** than direct training
  does — a 0.35 floor with no target-domain data at all, rising with
  sufficiency. Skills move between domains far more readily than data does.

The matrix has **clusters**: CODE/REASON/AGENT feed each other heavily, as do
IMAGE/VIDEO/AUDIO, while across clusters transfer is weak. So concentrating
on a related *group* is efficient and scattering is not — which rewards
specialisation rather than punishing it.

That last part needed a correction. The first draft's cross-cluster
coefficients were about twice as high, and generalists leaked into creative
segments on the strength of their text compute — vertical specialists fell
from ~40% of their own segment to 26%. Halving text→pixel transfer restored
them to 38%. Reading a great deal of prose does not teach you to render a
scene, and the numbers should say so.

**2. The incident model has no reference class.** Every number in §2f of
`WORLD_MODEL.md` is a judgment call. The *structure* is defensible —
frequency from sloppiness and exposure, severity from what the models can
actually do, a sector-wide regulatory response — and it is the structure
that produces the behaviour. The magnitudes are not defensible; they were
tuned until the posture was a decision rather than a tax. Nobody has
observed a severe AI incident, so nothing anchors the cost of one. Treat
this as the part of the model most likely to be wrong, and the part where
being wrong matters least, because the *shape* of the tradeoff is what the
game needs.

What *is* measured: safety posture is worth buying. Paired across 84
lab-runs, diligence is ahead in 51 of them, mean +$27B of 2030 ARR — but
negative at p10 and p25. It should feel like insurance you resent paying,
and on the numbers it does.

**3. Demand is a spend ceiling, not a labour market.** By 2030, with agents
doing real work, the demand side should be "fraction of knowledge work
automatable x the wage bill it displaces", with feedback: cheaper capable
agents expand the addressable work. Instead there is a ceiling curve. This
is the weakest part of the late game, and the late game is where the
interesting decisions are.

**4. Inference-time compute is a doctrine constant.** `test_time_oom` is set
per strategy and never changes. In reality it is a live decision every
quarter, and a real margin/capability tradeoff: spend more per query for a
better answer at worse unit economics.

**5. Labs never actually die.** They decay to near-zero revenue and persist.
No bankruptcy, no acquisition, no fire sale of a cluster — which removes
both a real consequence and a real event.

**6. No qualitative regime change.** Capability is monotone in effective
compute forever. The decade's actual history includes at least two shifts
(instruction tuning, RL on verifiable rewards) that reset what compute
bought. The model has one such shift, hard-coded by date, in
`reasoning_multiplier`.

**7. One frontier run at a time.** Now partially addressed by
`FRONTIER_RUN_SHARE`, but a lab still cannot deliberately run two
generations concurrently, which is a real strategic option.

---

## What this means for the target

The campaign should be judged on:

1. **Order** of the milestones — currently 115/120 pairs correct.
2. **Timing** within about a year and a half — currently 16/16.
3. **Magnitudes within an order of magnitude** — currently yes on every
   anchor family.
4. **Shape**: does the decade have an opening act, a middle, and a takeoff?

Not on matching 2020–2026 to two significant figures. That was never the
goal and chasing it hid a premise error for several versions.
