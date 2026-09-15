"""One number for 'how close is this model to what actually happened'."""
import math
from . import anchors as A
from .world import World
from .scenarios import historical_2020

WEIGHTS = {"revenue": 1.0, "capex": 0.8, "power": 0.8, "frontier_flop": 1.2}


def log_err(model, actual):
    if model <= 0 or actual <= 0:
        return 2.0
    return abs(math.log10(model / actual))


def score(months=84, verbose=False, seeds=(0, 1, 2, 3, 4)):
    """
    Calibration error, averaged over several seeded runs of the fixed
    calibration roster. A single run is noisy enough that a change can look
    like a 0.2 improvement purely from where the dice landed.
    """
    if len(seeds) > 1 and not verbose:
        vals = [score(months, False, (s,))[0] for s in seeds]
        return sum(vals) / len(vals), None
    w = World(historical_2020(), seed=seeds[0])
    for _ in range(months):
        w.step()
    parts, detail = {}, []

    rev = {}
    for y, _l, _s, total, _c in A.LAB_REVENUE:
        m = (y - 2020) * 12 + 11
        if m >= months:
            continue
        mod = sum(l.history[m]["rev"] for l in w.labs) * 12 / 1e9
        rev[y] = (mod, total)
    parts["revenue"] = sum(log_err(a, b) for a, b in rev.values()) / max(1, len(rev))

    cap = {}
    for y, actual, _c in A.SECTOR_CAPEX:
        mod = sum(l.capex_by_year.get(y, 0.0) for l in w.labs) / 1e9
        cap[y] = (mod, actual)
    parts["capex"] = sum(log_err(a, b) for a, b in cap.values()) / max(1, len(cap))

    pw = {}
    for y, actual, _c in A.POWER_DRAW:
        m = (y - 2020) * 12 + 11
        if m >= months:
            continue
        mod = w.sector_mw_hist[m] / 1000.0
        pw[y] = (mod, actual)
    parts["power"] = sum(log_err(a, b) for a, b in pw.values()) / max(1, len(pw))

    ff = {}
    for date, label, flop, *_r in A.TRAINING_RUNS:
        m = A.month_index(date)
        if m >= months or "Chinchilla" in label:
            continue
        mod = max((l.largest_run for l in w.labs), default=0.0)
        hist = [max((x for x in [lb.history[mm].get("largest", 0)] ), default=0)
                for lb in w.labs for mm in [m]]
        ff[date] = (mod, flop)
    # use the run size at each date, tracked in history
    parts["frontier_flop"] = sum(
        log_err(max(l.history[A.month_index(d)].get("largest", 0.0) for l in w.labs), f)
        for d, lb, f, *_r in A.TRAINING_RUNS
        if A.month_index(d) < months and "Chinchilla" not in lb) / 8.0

    total = sum(WEIGHTS[k] * v for k, v in parts.items()) / sum(WEIGHTS.values())
    if verbose:
        print("  calibration error, mean |log10(model/actual)| per family:")
        for k, v in parts.items():
            print(f"    {k:14s} {v:5.3f}   ({10**v:.2f}x typical error)")
        print(f"    {'WEIGHTED':14s} {total:5.3f}   ({10**total:.2f}x)")
        print("\n  revenue $B      model   actual")
        for y, (a, b) in rev.items():
            print(f"    {y}       {a:9.2f}{b:9.2f}")
        print("  sector GW       model   actual")
        for y, (a, b) in pw.items():
            print(f"    {y}       {a:9.2f}{b:9.2f}")
        print("  capex $B        model   actual")
        for y, (a, b) in cap.items():
            print(f"    {y}       {a:9.1f}{b:9.1f}")
        print("  frontier run    model   actual")
        for d, lb, f, *_r in A.TRAINING_RUNS:
            m = A.month_index(d)
            if m >= months or "Chinchilla" in lb:
                continue
            mod = max(l.history[m].get("largest", 0.0) for l in w.labs)
            print(f"    {d[0]}-{d[1]:02d}    {mod:9.2e}{f:9.2e}  {lb}")
    return total, w


if __name__ == "__main__":
    score(verbose=True)
