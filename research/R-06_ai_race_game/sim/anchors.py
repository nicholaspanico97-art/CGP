"""
Historical calibration anchors, 2020-2026.

These are the real world's answers. The simulator is judged by whether a
scripted replay of history lands near them. Every figure is a public
estimate; none is a disclosure. Confidence:

    HIGH  published paper, vendor spec, or company statement
    MED   widely reported, multiple consistent sources
    LOW   inferred from indirect evidence; treat as an order of magnitude

Where a range is known, the midpoint is stored and the range is in `note`.
"""

# ---------------------------------------------------- frontier training runs
# flop: total training FLOP, pretraining only unless noted.
TRAINING_RUNS = [
    # date        label                 flop      params  tokens   conf
    ((2020, 6), "GPT-3 class",        3.1e23,   175e9,   300e9, "HIGH",
     "6ND from the paper; 175B params, 300B tokens"),
    ((2021,12), "Gopher class",       6.3e23,   280e9,   300e9, "HIGH", ""),
    ((2022, 4), "PaLM class",         2.5e24,   540e9,   780e9, "HIGH", ""),
    ((2022, 4), "Chinchilla",         5.8e23,    70e9,   1.4e12, "HIGH",
     "the compute-optimal correction: 20 tokens per parameter"),
    ((2023, 3), "GPT-4 class",        2.1e25,   1.8e12,  13e12, "MED",
     "estimates cluster 1e25-4e25; MoE, ~280B active"),
    ((2024, 7), "Llama 3.1 405B",     3.8e25,   405e9,   15e12, "HIGH",
     "16k H100s, 54 days, published"),
    ((2024,12), "o1 class",           1.0e26,     None,   None, "LOW",
     "pretraining plus large-scale RL; the split is not public"),
    ((2025, 6), "2025 frontier",      4.0e26,     None,   None, "LOW",
     "100k+ accelerator clusters, months-long runs"),
    ((2026, 3), "2026 frontier",      1.5e27,     None,   None, "LOW",
     "gigawatt-class sites coming online"),
]

# --------------------------------------------------------------- benchmarks
# Reported scores for the frontier model of that date.
BENCHMARKS = [
    # date       suite        score  model            conf
    ((2020, 6), "MMLU",        43.9, "GPT-3",         "HIGH"),
    ((2022, 4), "MMLU",        69.3, "PaLM 540B",     "HIGH"),
    ((2023, 3), "MMLU",        86.4, "GPT-4",         "HIGH"),
    ((2024, 3), "MMLU",        86.8, "Claude 3 Opus", "HIGH"),
    ((2025, 6), "MMLU",        90.5, "frontier",      "MED"),

    ((2023, 3), "GPQA",        35.7, "GPT-4",         "HIGH"),
    ((2024, 3), "GPQA",        50.4, "Claude 3 Opus", "HIGH"),
    ((2024,12), "GPQA",        78.0, "o1",            "HIGH"),
    ((2025, 6), "GPQA",        83.0, "frontier",      "MED"),
    ((2026, 3), "GPQA",        88.0, "frontier",      "LOW"),

    ((2023, 3), "SWE",          1.7, "GPT-4",         "MED"),
    ((2024, 6), "SWE",         26.0, "Claude 3.5 S",  "HIGH"),
    ((2024,12), "SWE",         49.0, "o1/3.5 S v2",   "HIGH"),
    ((2025, 6), "SWE",         72.0, "frontier",      "MED"),
    ((2026, 3), "SWE",         80.0, "frontier",      "LOW"),
]
BENCHMARK_CEILING = {"MMLU": 92.0, "GPQA": 90.0, "SWE": 86.0}
# Ceilings are practical, not nominal: label noise on MMLU and a tail of
# near-unsolvable instances on SWE-bench Verified put a real lid on each.
BENCHMARK_FLOOR = {"MMLU": 25.0, "GPQA": 25.0, "SWE": 0.0}

# ------------------------------------------------------------ inference cost
# Cheapest $/Mtok (blended in/out) at which a given MMLU level was
# purchasable. The collapse here is one of the decade's real stories.
PRICE_FOR_QUALITY = [
    # date        mmlu_level   $/Mtok   conf
    ((2020, 6),   43.0,        60.00, "HIGH", "GPT-3 davinci launch price"),
    ((2022,11),   55.0,         2.00, "HIGH", "text-davinci-003 era"),
    ((2023, 3),   86.0,        37.50, "HIGH", "GPT-4 8k, 1:1 in/out blend"),
    ((2024, 5),   86.0,         7.50, "HIGH", "GPT-4o"),
    ((2024, 7),   82.0,         0.60, "HIGH", "open-weight 70B hosted"),
    ((2025, 6),   86.0,         0.45, "MED",  "small frontier-adjacent models"),
    ((2026, 3),   88.0,         0.18, "LOW",  ""),
]

# --------------------------------------------------------------- lab revenue
# Annualized run-rate revenue, $ billions, for the sector's leaders.
# These are the most-reported and least-confirmable numbers in the field.
LAB_REVENUE = [
    # year   leader   #2     sector total   conf
    (2020,    0.02,   0.00,     0.05, "LOW"),
    (2021,    0.05,   0.00,     0.15, "LOW"),
    (2022,    0.20,   0.01,     0.40, "LOW"),
    (2023,    1.60,   0.10,     2.60, "MED"),
    (2024,    3.70,   0.90,     7.00, "MED"),
    (2025,   13.00,   5.00,    26.00, "LOW"),
    (2026,   30.00,  14.00,    62.00, "LOW"),
]

# ------------------------------------------------------------- capital & iron
CLUSTER_SCALE = [
    # date       accelerators in the largest single training cluster  conf
    ((2020, 6),    10_000, "LOW",  "V100-class"),
    ((2022, 4),     6_144, "HIGH", "PaLM, TPU v4 pods"),
    ((2023, 3),    25_000, "MED",  "A100-class"),
    ((2024, 7),    16_000, "HIGH", "Llama 3.1, H100"),
    ((2025, 3),   100_000, "MED",  "H100/H200-class"),
    ((2026, 3),   300_000, "LOW",  "B200-class, multi-site"),
]

SECTOR_CAPEX = [           # $B/yr on AI datacenters and accelerators
    (2020,   2.0, "LOW"), (2021,   5.0, "LOW"), (2022,  12.0, "LOW"),
    (2023,  30.0, "MED"), (2024,  95.0, "MED"), (2025, 220.0, "LOW"),
    (2026, 380.0, "LOW"),
]

POWER_DRAW = [             # GW of IT load dedicated to AI, sector-wide
    (2023,  1.5, "LOW"), (2024,  4.0, "LOW"),
    (2025,  9.0, "LOW"), (2026, 17.0, "LOW"),
]


def month_index(ym, start=(2020, 1)):
    """(year, month) -> months since sim start."""
    return (ym[0] - start[0]) * 12 + (ym[1] - start[1])
