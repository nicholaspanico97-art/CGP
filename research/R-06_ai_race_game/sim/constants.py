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
ALGO_EFF_RATE_2020 = 3.0      # x per year at the frontier
ALGO_EFF_RATE_2030 = 1.7      # x per year by end of decade
MAX_ALGO_ADVANTAGE = 4.0      # most a lab can privately be ahead of the
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
REASONING_OOM_PER_YEAR = 0.40  # RL-era post-training gains, OOM/yr    (LOW)
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
MAX_RUN_GROWTH_PER_SHIP = 1.5   # calibrated, not assumed: see sim/score.py

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
# Calibrated so that 2020-2026 lands on the observed revenue record; the
# 2027-2030 continuation is an assumption (~1.75x/yr) and is the single
# biggest lever on how the back half of a campaign feels.
SECTOR_SPEND_CEILING = {      # $ per year the world will pay, sector-wide
    2020: 1.2e8, 2021: 3.5e8, 2022: 8.0e8, 2023: 5.0e9,  2024: 1.3e10,
    2025: 4.5e10, 2026: 1.1e11, 2027: 2.0e11, 2028: 3.6e11,
    2029: 6.2e11, 2030: 1.0e12,
}

RESEARCHER_COST_PER_YEAR = 900_000  # fully loaded frontier researcher (MED)
ENGINEER_COST_PER_YEAR = 420_000    # everyone else                    (MED)
