"""
The seam check: record a game, replay it from the log alone, and demand the
same run bit for bit.

A `ReplayPolicy` never reads the doctrine and never looks at the world; it
only hands back what was logged. So if a replayed game matches the original
exactly, every decision that affected the run went through
observe -> decide -> apply. Any mechanic that reaches around the seam and
reads `doctrine` inline for a CHOICE will show up here as a divergence.

This is also the save format: `{"seed": s, "roster": ..., "log": [...]}`
is the whole game.

    python -m sim.replay            # check seeds 0 (historical) and 7
    python -m sim.replay 3 11 19    # check these seeds (randomised)
"""
import json
import sys
from .world import World
from .scenarios import randomized_2020, historical_2020
from .policy import ReplayPolicy, IllegalAction, Actions


def _run(labs, seed, months):
    w = World(labs, seed=seed)
    for _ in range(months):
        w.step()
    return w


def record(seed, randomized=True, months=132):
    labs = randomized_2020(seed) if randomized else historical_2020()
    w = _run(labs, seed, months)
    return w, {"seed": seed, "randomized": randomized, "months": months,
               "log": [[m, who, changed] for m, who, changed in w.action_log]}


def replay(save):
    seed = save["seed"]
    labs = randomized_2020(seed) if save["randomized"] else historical_2020()
    log = [(m, who, changed) for m, who, changed in save["log"]]
    for l in labs:
        l.policy = ReplayPolicy(log, l.name)
    return _run(labs, seed, save["months"])


def same_run(w1, w2):
    return (all(a.history == b.history for a, b in zip(w1.labs, w2.labs))
            and w1.action_log == w2.action_log)


def check(seed, randomized=True, months=132):
    w1, save = record(seed, randomized, months)
    # through JSON and back, so the save format is what is tested
    save = json.loads(json.dumps(save))
    w2 = replay(save)
    ok = same_run(w1, w2)
    n_stand = sum(1 for e in save["log"] if "release" not in e[2])
    n_rel = len(save["log"]) - n_stand
    print(f"  seed {seed:>3} {'historical' if not randomized else 'randomised':10s}"
          f"  {n_stand:4d} standing changes  {n_rel:3d} release interrupts"
          f"  -> {'IDENTICAL' if ok else 'DIVERGED'}")
    return ok


def check_illegal():
    """The world refuses what it should refuse."""
    labs = historical_2020()
    w = World(labs, seed=0)
    lab = labs[0]
    good = lab.actions.copy()
    bad = [("split", dict(train=0.9)), ("capex", dict(capex_aggression=1.5)),
           ("mixture", dict(mixture={"LANG": 0.5})),
           ("bid", dict(data_bids={"web_crawl": 1e6}))]
    n = 0
    for label, patch in bad:
        a = good.copy()
        for k, v in patch.items():
            setattr(a, k, v)
        try:
            w.apply(lab, a)
            print(f"  illegal {label}: ACCEPTED (wrong)")
        except IllegalAction as e:
            n += 1
    print(f"  {n}/{len(bad)} illegal actions refused")
    return n == len(bad)


if __name__ == "__main__":
    seeds = [int(x) for x in sys.argv[1:]]
    print("REPLAY CHECK  (record -> save -> replay, must match bit for bit)")
    ok = check_illegal()
    if seeds:
        for s in seeds:
            ok &= check(s, randomized=True)
    else:
        ok &= check(0, randomized=False)
        ok &= check(7, randomized=True)
    print("  seam holds" if ok else "  SEAM LEAKS")
    sys.exit(0 if ok else 1)
