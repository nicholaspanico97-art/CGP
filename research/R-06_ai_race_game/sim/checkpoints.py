"""
Calibration by TIMING, not by magnitude.

The old instrument (`sim/score.py`) compares the sim's value at a fixed
calendar date against what actually happened, in log space. On a curve
rising about an order of magnitude a year that is a bad question to ask: a
sim that is six months early reads as a 0.5 OOM error, indistinguishable
from one that is genuinely misshapen. It punishes a timing offset, which for
an alternate-universe sim is not an error at all.

This asks the right question instead:

    for each checkpoint, WHEN did the sim reach it, and how far is that
    from when the world reached it, in months?

Signed, because early and late are not equally bad. A campaign whose
consumer market opens in 2020 is broken in a way one that opens in 2024 is
not - the first removes the game's opening act, the second only delays it.

The acceptance criterion is a band, not a number: every checkpoint inside
+/- 18 months, nothing inside the first year that should not be there, and
the ORDER preserved. Order matters more than dates. A world where
SWE-bench-hard falls before the consumer assistant exists is a different
world; one where both happen a year late is the same world running slow.
"""
import statistics
from . import domains as D
from . import tasks as TASKS
from .world import World
from .scenarios import historical_2020

# (key, label, real date, probe) - probe(world, month) -> bool
# Ordered as they actually happened; the order is itself part of the test.
CHECKPOINTS = [
    ("gpt3",      "A GPT-3-class model exists",        (2020, 6),
     lambda w, m: _best_run(w) >= 2.5e23),
    ("api",       "A paid model API exists",           (2020, 7),
     lambda w, m: _seg_open(w, "api_general")),
    ("mmlu70",    "Broad-knowledge score reaches 70",  (2022, 4),
     lambda w, m: _best_score(w, "MMLU") >= 70),
    ("assistant", "A consumer assistant market opens", (2022, 11),
     lambda w, m: _seg_open(w, "consumer_chat")),
    ("flop1e25",  "A 1e25 FLOP training run",          (2023, 3),
     lambda w, m: _best_run(w) >= 1e25),
    ("mmlu86",    "Broad knowledge reaches 86",        (2023, 3),
     lambda w, m: _best_score(w, "MMLU") >= 86),
    ("rev1b",     "Sector revenue passes $1B/yr",      (2023, 6),
     lambda w, m: _revenue(w) >= 1e9),
    ("gw1",       "1 GW of AI load",                   (2023, 12),
     lambda w, m: _power(w) >= 1000),
    ("swe25",     "Software-issue solving reaches 25%", (2024, 6),
     lambda w, m: _best_score(w, "SWE") >= 25),
    ("gpqa78",    "Graduate science reaches 78",       (2024, 12),
     lambda w, m: _best_score(w, "GPQA") >= 78),
    ("flop1e26",  "A 1e26 FLOP training run",          (2024, 12),
     lambda w, m: _best_run(w) >= 1e26),
    ("rev10b",    "Sector revenue passes $10B/yr",     (2025, 3),
     lambda w, m: _revenue(w) >= 1e10),
    ("cluster100k", "A 100k-accelerator coherent cluster", (2025, 3),
     lambda w, m: _biggest_cluster(w) >= 100_000),
    ("agents",    "An enterprise agent market opens",  (2025, 6),
     lambda w, m: _seg_open(w, "enterprise_agents")),
    ("gw10",      "10 GW of AI load",                  (2025, 12),
     lambda w, m: _power(w) >= 10_000),
    ("rev60b",    "Sector revenue passes $60B/yr",     (2026, 6),
     lambda w, m: _revenue(w) >= 6e10),
]


def _biggest_cluster(w):
    """
    Accelerators any lab has had to operate as ONE coherent cluster.

    A lab's total fleet is not a cluster - 100k accelerators across five
    sites is not a 100k cluster, and conflating them was making this
    checkpoint fire in 2021. Derive it from the run instead: a run of F FLOP
    finished in T months needed F / (per-accelerator throughput x T).
    """
    from . import constants as K
    best = 0
    for l in w.labs:
        if l.largest_run <= 0:
            continue
        # the chips a run of that size takes, at the fleet's average
        # throughput per chip (the newest chip alone halved the count once
        # a new generation landed - an instrument artefact, v1.15.1)
        n = max(l.fleet.count(), 1)
        months = max(l.doctrine.get("run_months", 4.0), 0.5)
        per = (l.fleet.train_flops() / n) * K.SECONDS_PER_MONTH * months
        if per > 0:
            best = max(best, int(l.largest_run / per))
    return best


def _best_run(w):
    return max((l.largest_run for l in w.labs), default=0.0)


def _best_score(w, suite):
    # the suite as originally posed: a later generation is a harder test, so
    # crossing 70 on a successor does not count as crossing 70 on this one
    if w.suites.gen.get(suite, 0) > 0:
        return 100.0
    return max((sc for sc in (w.scores.get(suite) or {}).values()), default=0.0)


def _seg_open(w, seg):
    st = getattr(w, "segment_state", {}).get(seg)
    return bool(st and st[1])


def _revenue(w):
    return sum(l.revenue_m for l in w.labs) * 12.0


def _power(w):
    return sum(l.fleet.megawatts() for l in w.labs)


def month_of(ym):
    return (ym[0] - 2020) * 12 + (ym[1] - 1)


def run_one(seed, months=132):
    """When does each checkpoint first fire, in this run?"""
    w = World(historical_2020(), seed=seed)
    hit = {}
    for m in range(months):
        w.step()
        for key, _label, _date, probe in CHECKPOINTS:
            if key in hit:
                continue
            try:
                if probe(w, m):
                    hit[key] = m
            except Exception:
                pass
    return hit


def report(seeds=(0, 1, 2, 3, 4), months=132, band=18):
    runs = [run_one(s, months) for s in seeds]
    print(f"CHECKPOINT TIMING  ({len(seeds)} seeds, band +/-{band} months)\n")
    print(f"  {'checkpoint':38s}{'real':>9s}{'sim':>10s}{'offset':>9s}{'spread':>9s}")
    errs, missing, rows = [], [], []
    for key, label, date, _p in CHECKPOINTS:
        target = month_of(date)
        hits = [r[key] for r in runs if key in r]
        if not hits:
            print(f"  {label:38s}{date[0]}-{date[1]:02d}{'never':>10s}{'—':>9s}{'—':>9s}")
            missing.append(label)
            continue
        med = statistics.median(hits)
        off = med - target
        spread = (max(hits) - min(hits))
        flag = "" if abs(off) <= band else "  <-- outside band"
        print(f"  {label:38s}{date[0]}-{date[1]:02d}"
              f"{2020 + int(med) // 12}-{int(med) % 12 + 1:02d}".ljust(0)
              + f"{off:+9.0f}{spread:9.0f}{flag}")
        errs.append(off)
        rows.append((key, label, target, med))

    if errs:
        inside = sum(1 for e in errs if abs(e) <= band)
        print(f"\n  median offset   {statistics.median(errs):+.0f} months"
              f"   (positive = sim runs late)")
        print(f"  mean |offset|   {statistics.mean(abs(e) for e in errs):.1f} months")
        print(f"  worst           {max(errs, key=abs):+.0f} months")
        print(f"  inside +/-{band}     {inside}/{len(errs)} checkpoints")
    if missing:
        print(f"  never reached   {len(missing)}: {', '.join(missing[:4])}")

    # order preservation - the part that matters more than the dates
    real_order = [k for k, _l, _d, _p in CHECKPOINTS]
    sim_order = [k for k, _l, t, med in sorted(rows, key=lambda x: x[3])]
    inversions = 0
    for i, a in enumerate(sim_order):
        for b in sim_order[i + 1:]:
            if real_order.index(a) > real_order.index(b):
                inversions += 1
    n = len(sim_order)
    pairs = n * (n - 1) // 2
    print(f"\n  ORDER: {pairs - inversions}/{pairs} pairs in the right sequence"
          f"  ({inversions} inversions)")
    print("  Order matters more than dates: a world where the milestones happen")
    print("  in the wrong sequence is a different world. One where they all happen")
    print("  a year late is the same world running slow.")
    return errs, inversions


if __name__ == "__main__":
    report()
