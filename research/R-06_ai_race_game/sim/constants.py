"""
Physical and economic constants for the Frontier world model.

EVERYTHING IN THIS FILE IS IN REAL UNITS. No abstract "compute units".

    compute      FLOP (training runs), FLOP/s (fleet capacity)
    hardware     accelerator count, by generation
    power        watts, megawatts, kWh
    money        US dollars, nominal
    data         tokens
    text I/O     tokens, and dollars per million tokens ($/Mtok)
    time         months (internal tick); the game surfaces quarters

Figures are public estimates, not disclosures. Confidence is tagged where
it matters: HIGH = vendor spec or published paper, MED = widely reported
and mutually consistent, LOW = inference from indirect evidence.
"""

# ---------------------------------------------------------------- time
SIM_START = (2020, 1)
SIM_END = (2030, 12)
MONTHS = 132
HOURS_PER_MONTH = 730.0
SECONDS_PER_MONTH = 2_628_000.0


# ------------------------------------------------------------ hardware
# peak_tflops: dense BF16/FP16 TFLOP/s per accelerator            (HIGH)
# watts:       board power, excludes datacenter overhead          (HIGH)
# capex:       all-in $ per accelerator incl. network+host share  (MED)
# train_mfu:   realized model-FLOP utilization on a large run     (MED)
# infer_util:  realized fraction of peak achieved serving under a
#              latency SLO, after batching/KV-cache overheads     (LOW)
ACCELERATORS = [
    # name        avail    peak_tflops  watts  capex$   train_mfu  infer_util
    ("V100",    (2017, 5),      125.0,   300,   10_000,      0.33,       0.18),
    ("A100",    (2020, 5),      312.0,   400,   15_000,      0.40,       0.22),
    ("H100",    (2023, 3),      989.0,   700,   30_000,      0.42,       0.25),
    ("B200",    (2025, 2),     2250.0,  1000,   40_000,      0.45,       0.28),
    ("GX-1",    (2026,10),     3600.0,  1400,   45_000,      0.46,       0.30),
    ("GX-2",    (2028, 6),     7200.0,  1800,   52_000,      0.47,       0.32),
    ("GX-3",    (2030, 2),    14000.0,  2300,   60_000,      0.48,       0.34),
]
# GX-* are projections past the announced roadmap: ~2x per ~20 months at
# ~1.35x the power, i.e. perf/W improving ~1.5x per generation.

PUE = 1.25                    # datacenter power overhead             (MED)
ELECTRICITY_PER_KWH = 0.062   # $/kWh, large industrial contract      (MED)
DEPRECIATION_MONTHS = 48      # straight-line; the industry argues     (MED)
                              # about 4 vs 6 years, and it matters
DC_OPEX_FRAC_OF_POWER = 0.35  # cooling, staff, maintenance           (LOW)

# Datacenter buildout
DC_CAPEX_PER_MW = 9_500_000   # $/MW of IT capacity, shell+power      (MED)
DC_LEAD_TIME_MONTHS = 20      # greenfield, grid-connected            (MED)
GRID_QUEUE_MONTHS = 14        # additional interconnect wait post-2025 (LOW)
LEASE_LEAD_MONTHS = 9         # colocation in existing shells         (MED)
LEASE_OPEX_PER_MW_MONTH = 105_000   # what you pay instead of building (LOW)
LEASE_MARKET_MW = {           # colocation capacity the market can offer
    2020: 400, 2021: 700, 2022: 1_200, 2023: 2_600, 2024: 6_000,
    2025: 12_000, 2026: 20_000, 2027: 28_000, 2028: 36_000,
    2029: 44_000, 2030: 52_000,
}

# Accelerator supply: the whole industry's advanced-packaging-limited
# output of leading-edge accelerators per month. This is the hard wall
# nobody can buy past.                                                (LOW)
FAB_OUTPUT_PER_MONTH = {
    2020:   40_000, 2021:   70_000, 2022:  110_000, 2023:  180_000,
    2024:  400_000, 2025:  750_000, 2026: 1_200_000, 2027: 1_700_000,
    2028: 2_300_000, 2029: 3_000_000, 2030: 3_800_000,
}


# ------------------------------------------------- algorithmic progress
# Pretraining efficiency: FLOP needed for a fixed capability falls over
# time. Epoch AI put this near 3x/year for 2012-2023; sustaining that for
# a full decade is not credible, so the rate decays.                 (MED)
# The sector's algorithmic frontier is ENDOGENOUS: it advances because labs
# do research, not because the calendar advances. The two rates below are no
# longer a schedule the world follows - they are what the historical period
# has to reproduce, and SECTOR_ALGO_SCALE is calibrated so that it does.
#
# This is what lets the self-improvement loop matter. With an exogenous
# schedule, automating research could only redistribute relative advantage
# between labs; the field's absolute progress was fixed in advance, so the
# capability curve could never bend.
ALGO_EFF_RATE_2020 = 3.0      # x per year the historical period must show
ALGO_EFF_RATE_2030 = 1.7      # the no-automation baseline it decays toward
SECTOR_ALGO_SCALE = 0.07     # calibrated: research output -> frontier growth
SECTOR_ALGO_ALPHA = 0.45      # diminishing returns to piling on researchers
IDEA_DIFFICULTY = 0.6         # ideas get harder to find: each further
                              # doubling of efficiency costs more research
                              # than the last. Without this the loop has no
                              # damping and the frontier explodes in 2021.
MAX_ALGO_ADVANTAGE = 7.0      # most a lab can privately be ahead of the
                              # field on efficiency, as a multiple      (LOW)
LEADER_EDGE_DECAY = 0.55      # how fast a private edge becomes common  (LOW)
CAPABILITY_PERCEPTION_OOM = 1.4  # beyond this much of a capability gap,
                                 # buyers stop being able to tell       (LOW)
MIN_VIABLE_SHARE = 0.012      # second-source rules, data residency and
                              # switching costs keep rivals alive       (LOW)
ALGO_DIFFUSION_HALFLIFE_M = 11  # months for a follower to close half the
                                # gap to the frontier through papers,
                                # open weights and hiring             (LOW)

# Post-training (RLHF -> RLAIF -> large-scale RL on verifiable rewards)
# acts as a separate multiplier on effective compute. It barely existed
# in 2020 and became a primary driver from late 2024.                (LOW)
POST_TRAIN_ERA_START = (2022, 11)
POST_TRAIN_RL_ERA_START = (2024, 9)
RLHF_ERA_TOTAL_GAIN = 3.0      # effective-compute multiple by the RL era
REASONING_OOM_PER_YEAR = 0.36  # lowered when per-model x.5 releases
                               # were added: they now carry part of what
                               # this sector-wide term used to absorb  # RL-era post-training gains, OOM/yr    (LOW)
REASONING_DECAY_YEARS = 2.5    # halving time of that rate

# Inference-time scaling: spending more FLOP per query buys capability.
# Returns per OOM of test-time compute, relative to an OOM of training
# compute. Empirically similar order, sublinear, and it saturates.   (LOW)
TEST_TIME_KAPPA = 0.33
TEST_TIME_SATURATION_OOM = 3.0   # beyond ~1000x baseline, returns die


# ----------------------------------------------------------- economics
# Serving arithmetic: a dense forward pass costs ~2 FLOP per active
# parameter per token. Attention and overheads add; 2.1 is a working
# figure for long-context serving.                                   (MED)
FLOP_PER_TOKEN_PER_ACTIVE_PARAM = 2.1

# Training recipes are knowledge, and knowledge has a date. A lab in 2020
# cannot choose a Chinchilla token ratio because nobody had worked it out,
# and cannot serve a sparse mixture because nobody could train one at scale.
# A lab that invests in research reaches each recipe early; the rest follow.
RECIPE_ERA_TOKENS_PER_PARAM = {   # (year, month): sector-best known ratio
    (2020, 1): 2.0, (2022, 4): 20.0, (2023, 1): 25.0, (2023, 9): 40.0,
    (2024, 6): 70.0, (2025, 6): 120.0, (2027, 1): 180.0,
}
RECIPE_ERA_MOE = {                # (year, month): sector-best sparsity factor
    (2020, 1): 1.0, (2023, 6): 3.0, (2024, 6): 6.0, (2026, 1): 10.0,
    (2028, 1): 16.0,
}
# Engineering, not physics: the largest run a lab can actually land grows
# with experience. Runs in the real record grew ~3-5x per generation, never
# 100x, because the failure modes at each new scale have to be learned.
# Ambition, not a ceiling.
#
# This used to be a HARD cap: a run could be at most this multiple of your
# last one. Checking which constraint actually bound revealed that it was
# deciding run size in 73% of lab-months - so an invented ratchet, tuned to
# reproduce historical run growth, was doing the job that compute was
# supposed to do. A lab could hold five million accelerators and still plan
# a modest run. That makes the entire capex and power half of the model
# nearly decorative, and it is the opposite of the thesis.
#
# Now the constraint is compute, and over-ambition is a RISK instead: a run
# far beyond anything you have landed before is more likely to come apart.
# Labs did attempt big jumps and did sometimes eat them.
# A lab does not point its whole training lane at one model. The frontier
# run shares that compute with ablations, smaller production models,
# distillation targets and restarts. Modelling one run consuming the entire
# lane made every lab's frontier model roughly twice as large as it should
# be, which is the kind of error a magnitude-at-a-date metric hides and a
# timing metric finds immediately.
FRONTIER_RUN_SHARE = 0.30

AMBITION_COMFORT = 2.6        # multiple of your last run you can attempt
                              # without materially raising the odds of a dud
AMBITION_RISK = 0.30          # extra dud probability per doubling above it
AMBITION_SIGMA = 0.22         # extra outcome spread per doubling above it

# Mass-market adoption needed a conversational product, which needed a
# capability level that arrived in late 2022 - not a moment earlier.
CONSUMER_PRODUCT_CAPABILITY = 26.35
CONSUMER_ADOPT_MIDPOINT = 28.8
CONSUMER_ADOPT_WIDTH = 0.62

# Market structure
CONSUMER_TAM_2020 = 60_000_000     # plausible paying-consumer ceiling
CONSUMER_TAM_2030 = 900_000_000    # after a decade of diffusion      (LOW)
API_PRICE_ELASTICITY = 1.9         # demand elasticity to $/Mtok      (LOW)
                                   # >1: cutting price grows revenue
QUALITY_ELASTICITY = 2.4           # demand sensitivity to capability (LOW)

SERVING_UTILIZATION = 0.45   # fraction of serving capacity actually sold;
                             # load is spiky and SLOs need headroom   (LOW)
GROSS_MARGIN_FLOOR = -0.6    # how far below cost a lab will price

# Demand is ultimately bounded by budgets, not by capability. This is the
# addressable annual spend on the work these models can do - software,
# services, and the cheaper end of knowledge labour - which grows as
# capability unlocks new categories but never becomes infinite.
# Demand is unlocked by CAPABILITY, not by the calendar. If an assistant
# worth paying for exists in 2020, people buy it in 2020. What the calendar
# cannot do is make organisations adopt faster than they adopt: value
# unlocked is immediate, realised spend chases it with a lag.
#
#   value_unlocked($/yr) = SPEND_AT_REFERENCE x 10^(SPEND_PER_OOM x (C - C_ref))
#   realised spend approaches that with a half-life of DIFFUSION_HALFLIFE_M
SPEND_REFERENCE_CAPABILITY = 26.50   # frontier LANG capability, GPT-4 class
SPEND_AT_REFERENCE = 2.0e9          # $/yr the world would eventually pay there
SPEND_PER_OOM = 0.45                 # OOMs of spend per OOM of capability
DIFFUSION_HALFLIFE_M = 12            # how slowly organisations actually adopt

CONSUMER_USAGE_MULT = 2.6    # flat-rate consumers burn this many times the
                             # tokens per dollar that an API buyer does (LOW)

RESEARCHER_COST_PER_YEAR = 900_000  # fully loaded frontier researcher (MED)
ENGINEER_COST_PER_YEAR = 420_000    # everyone else                    (MED)

# ------------------------------------------------------------------ safety
# How often something goes wrong is about sloppiness and exposure. How BAD
# it is when it does is about what the models can actually do. Keeping those
# two separate is the point: a chat assistant misbehaving is a news cycle,
# and the same misalignment in something with real autonomy is not.
INCIDENT_BASE = 0.010          # monthly baseline, before everything else
INCIDENT_JUMP_GAIN = 0.55      # per OOM shipped without evaluating it
INCIDENT_DEBT_GAIN = 0.16      # per point of safety debt

# Severity ceiling, keyed on AGENT capability. Below the floor, real-world
# harm is essentially unreachable however careless a lab is.
HARM_FLOOR = 26.5              # roughly: agents that can use tools at all
HARM_CEILING = 32.0            # roughly: agents that act unsupervised
SEVERE_SCALE = 0.42            # weight on the severe tier at full potential

MINOR_TRUST = 6.0
MODERATE_TRUST = 14.0
MODERATE_REVENUE_COST = 0.90   # of one month's revenue
MODERATE_FIXED = 9.0e7
SEVERE_TRUST = 26.0
SEVERE_REVENUE_COST = 3.20     # litigation, remediation, churn - and it
                               # scales with the business, because a severe
                               # incident at a $100B lab is not a $600M event
SEVERE_FIXED = 1.4e9
SEVERE_RESTRICT_MONTHS = 15    # offender barred from agentic deployment.
                               # Losing your best segments for over a year is
                               # the consequence that actually bites
SEVERE_REGULATION_STEP = 0.55  # sector-wide response to a severe incident

# Reputation heals. Without this, trust is a one-way ratchet to the floor -
# every lab bottoms out, the variable stops carrying information, and safety
# investment buys nothing because there is no reputation left to protect.
# Recovery is slow, and slower the further you have fallen: a lab with a
# history has to earn its way back.
TRUST_BASELINE = 55.0
TRUST_RECOVERY = 0.055         # fraction of the gap closed per month
TRUST_SCAR = 0.11             # recovery slowed per incident on the record

# Evaluation and safety work
EVAL_CAPABILITY_COVERAGE = 0.85  # of a capability jump, when a run is evaluated
SAFETY_SPEND_PER_POINT = 2.2e7   # $ per month to retire one point of debt
SAFETY_DEBT_DRIFT = 0.035        # debt accrues slowly just from operating

# Regulation: a sector-wide level that rises with severe incidents and
# decays slowly. Costs everyone compliance and raises the bar for agentic
# products. Not yet a real actor - see ROADMAP.md item 5.
REGULATION_DECAY = 0.985         # per month
REGULATION_COMPLIANCE_COST = 0.045  # of revenue, per unit of regulation
REGULATION_GATE_LIFT = 0.30      # OOM added to agentic gates per unit

# ------------------------------------------------- information and paranoia
# Nobody can see a rival's true position. They can see the scoreboard (which
# the rival had reasons to inflate), the power siting and hiring (noisy and
# lagged), and how long it has been since the rival shipped anything.
#
# The last of those is the dangerous one: silence plus growing compute is
# the signature of a lab sitting on a breakthrough, AND the signature of a
# lab that is simply stuck. From outside they are identical.
INTEL_BASE_SIGMA = 0.30       # OOM of uncertainty about a rival's true best
INTEL_STALENESS = 0.20        # extra uncertainty per year of their silence
INTEL_SPEND_EFFECT = 0.55     # how much intel investment narrows it
SCALE_OBS_NOISE = 0.20        # log10 error in counting someone's fleet
LATENT_FROM_SILENCE = 0.26    # assumed hidden progress per year of silence
LATENT_FROM_SCALE = 0.40      # weight on their observed compute growth
LATENT_MAX = 0.55             # ceiling on what silence and siting can tell
                              # you. Outside observers are not omniscient:
                              # past about half an order of magnitude the
                              # signals stop carrying information, and
                              # without this cap the 2020-22 buildout has
                              # every lab believing every rival is 2.6 OOM
                              # ahead, which is not paranoia, it is a bug.

# Threat is what a lab acts on, and it is deliberately pessimistic: a lab
# plans against the upper end of its estimate, by this many sigma. That bias
# is the engine of the spiral - pricing in the bad case means over-building,
# and your over-building is the signal that makes a rival price in theirs.
PARANOIA_DEFAULT = 0.85
# Where the spiral is allowed to act matters more than how hard.
#
# The historical anchors pin release PACE tightly, so routing panic through
# the cooldown wrecks the fit (1.68x -> 2.15x on its own) - the record is
# consistent with labs not panicking much about cadence. But the anchors say
# nothing about how much a frightened lab overpays for researchers, bids for
# a corpus, or gambles on an architecture. So the spiral runs mostly through
# those, and only lightly through pace.
THREAT_CAPEX_GAIN = 0.22      # extra capex aggression per OOM of deficit
THREAT_COOLDOWN_CUT = 0.5     # months cut from a release cooldown per OOM
THREAT_RISK_GAIN = 0.45       # extra architectural risk-taking per OOM
THREAT_COMP_GAIN = 0.30       # how much more a frightened lab pays per head
THREAT_BID_GAIN = 0.55        # how much more it will pay for a data licence
SPIRAL = 1.0                  # master dial. 0 disables the panic channels
                              # entirely for a historical-realism run.

# --------------------------------------------------- benchmarks as measures
# Elicitation: how well a lab gets its own model to actually perform, through
# scaffolding, prompting and tooling. Lower is sharper. Two labs at the same
# difficulty frontier do not score the same.
ELICITATION_BEST = 0.26
ELICITATION_WORST = 0.62

# Benchmark chasing. Optimising for the published suites lifts the MEASURED
# score without moving the frontier. The market prices what it can see, so
# this buys real share now - and it is worthless to the self-improvement
# loop, which keys off what the model can actually do. That fork is the
# whole point of separating the two.
CHASE_MAX_OOM = 0.55          # most a determined chaser can fake
CHASE_RATE = 0.020            # OOM per month of sustained optimisation
CHASE_DECAY = 0.010           # fades when a new suite arrives or effort stops
CONTAMINATION_BASE = 0.004    # monthly chance of being caught, per OOM chased
CONTAMINATION_TRUST = 16.0    # trust lost when caught
CONTAMINATION_SETBACK = 0.75  # fraction of the chased advantage destroyed

# ------------------------------------------------ the self-improvement loop
# Research is itself a task, and it is a task made of code, long-horizon
# agency and scientific reasoning. Once a lab's models are good enough at
# those three, they start doing the research, and the loop closes: better
# models do better research which makes better models.
#
# This is the one genuinely explosive mechanism in the model, so it is
# bounded: the multiplier saturates, because even a perfect researcher is
# still waiting on experiments that take wall-clock time and silicon.
RSI_DOMAINS = {"CODE": 0.40, "AGENT": 0.35, "REASON": 0.25}
RSI_THRESHOLD = 32.2      # research index where automation starts to bite
RSI_WIDTH = 1.05          # how sharply it comes on, in OOM
RSI_MAX_FACTOR = 9.0      # ceiling on research throughput multiple
RSI_COMPUTE_TAX = 0.22    # fraction of the experiment lane the agents eat

# ------------------------------------------------------------- distillation
# You can study a model you can query. Every token a frontier model serves is
# a token someone can learn from - by distillation, by synthetic data, by
# simply reading what good output looks like. So the leaders' own commercial
# success is what lets the field catch up, and hoarding is the only way to
# stop it.
DISTILL_COEF = 0.42
DISTILL_REF_MTOK = 1.5e6  # monthly served volume at which this gets serious

# The price of hoarding. A lab whose best model is unreleased is visibly not
# shipping, and the market notices: it bleeds the consumer loyalty it is not
# defending, and it cannot raise on a story nobody can verify.
WITHHOLD_TRUST_DECAY = 0.85    # trust points per month while sitting on one
WITHHOLD_STICKINESS_LOSS = 0.45  # how much of a sticky default it forfeits

# --------------------------------------------------- run outcomes & releases
# A training run does not return what the scaling law says. It returns what
# the scaling law says times how the run actually went: the data mix, the
# architecture bet, the loss spikes you never fully recovered from. Most runs
# land near trend, some disappoint, and occasionally one lands well above it.
#
# Crucially, a lab does NOT ship a model worse than the one it already sells.
# So this variance never shows up as capability going DOWN - it shows up as
# flat stretches while a disappointing run is shelved, and as the occasional
# jump when one lands. The ratchet is the whole point.
RUN_SIGMA_LOG10 = 0.105        # ordinary run-to-run spread, in OOM
RUN_BREAKTHROUGH_P = 0.06      # a genuine architectural win
RUN_BREAKTHROUGH_OOM = 0.44
RUN_DUD_P = 0.13               # a bet that did not transfer
RUN_DUD_OOM = -0.30
TALENT_VARIANCE_DAMP = 0.40    # good teams get fewer surprises in both
                               # directions - they know what works
BEHIND_RISK_APPETITE = 0.25    # a trailing lab takes bigger architectural
                               # swings, because parity is not good enough.
                               # Was 0.55 while `behind` read the TRUE
                               # frontier (a seam breach, v1.7); against a
                               # lab's belief - the max of six noisy
                               # estimates, biased high - the same
                               # behaviour needs a smaller gain. Refit on
                               # the checkpoint table, 5 seeds.
SHIP_THRESHOLD_OOM = 0.035     # won't replace a shipped model for less
SHELVE_LEARNING = 0.40         # a shelved run still teaches you something
SHIP_JITTER_MONTHS = 3         # release timing is not a metronome

# Post-training releases - the x.5 between pretrains. A shipped model can be
# improved two or three times without a new pretraining run, with sharply
# diminishing returns, which is what gives the real release cadence its
# shape: a big jump, then a couple of smaller ones, then a big jump.
POST_TRAIN_GAIN_OOM = 0.155
POST_TRAIN_DECAY = 0.55
POST_TRAIN_MAX = 3             # ceiling; how many a given base model
                               # actually gets is drawn per model
POST_TRAIN_MONTHS = 2

# Scenario dial. 1.0 is the historical-realism setting. Higher values widen
# run variance and speed diffusion, producing a more contested race at some
# cost in fidelity - the realism/fun trade, made explicit and tunable.
# 1.0 reproduces history's concentration (one lab holding ~87% of the
# decade). 1.8 is the default because the game wants a race: it costs about
# 1% of aggregate calibration, and the anchors cannot tell the difference -
# they are all sector-level, so they do not know who is winning. This is a
# values choice, not a fit. Set it to 1.0 for a historical-realism campaign.
COMPETITIVENESS = 1.8

# ------------------------------------------------------------------ talent
# Progress shifts from people to compute across the decade. In 2020 a small
# team with the right idea moved the field; by 2030 the constraint is how
# many experiments an organisation can run. These four numbers are the claim.
TALENT_ELASTICITY_2020 = 0.78     # exponent on researcher-years, 2020
TALENT_ELASTICITY_2030 = 0.16     # ... and 2030
COMPUTE_ELASTICITY_2020 = 0.08    # exponent on experiment FLOP, 2020
COMPUTE_ELASTICITY_2030 = 0.52    # ... and 2030
STAR_EXPONENT_2020 = 0.55         # weight on exceptional individuals, 2020
STAR_EXPONENT_2030 = 0.10         # ... and 2030
RESEARCH_SCALE = 0.0065           # calibrated overall rate

STAR_POOL_2020 = 130              # frontier-caliber researchers worldwide
STAR_POOL_GROWTH = 1.32           # per year; training one takes years   (LOW)
RESEARCHER_POOL_2020 = 4_500
RESEARCHER_POOL_GROWTH = 1.40
COMP_SCARCITY_EXPONENT = 0.55     # how hard comp rises when everyone hires
STAR_MOVE_RATE = 0.055            # chance per month a star considers moving
ATTRACT_COMPUTE = 0.45            # weights on why a researcher picks a lab
ATTRACT_COMP = 0.30
ATTRACT_MISSION = 0.15
ATTRACT_PRESTIGE = 0.10
