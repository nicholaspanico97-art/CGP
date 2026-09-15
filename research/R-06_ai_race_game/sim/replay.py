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


def _run(labs, seed, months, now=None):
    """`now`: immediate purchases from a log, {month: [(lab, kind, amount)]},
    applied before that month's tick, as they were made."""
    w = World(labs, seed=seed)
    by_name = {l.name: l for l in labs}
    for _ in range(months):
        for who, kind, amount in (now or {}).get(w.month, []):
            w.buy_now(by_name[who], kind, amount)
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
    now = {}
    for m, who, changed in log:
        if "now" in changed:
            now.setdefault(m, []).append((who, changed["now"]["kind"], changed["now"]["amount"]))
    return _run(labs, seed, save["months"], now)


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


def check_game(seed=7, player=2, quarters=8):
    """A played game - human orders and interrupt answers - replays too."""
    from .game import Game
    from .policy import Release
    answers = iter([Release(True, True), Release(False), Release(True, False)])
    def ask(obs, cand, held):
        return next(answers, Release(True, True))
    g = Game(seed=seed, player=player, ask_release=ask)
    o = g.orders
    o.data_buy = "web_crawl"
    o.train, o.serve, o.experiment = 0.5, 0.35, 0.15
    o.comp_offer = 950e3
    for q in range(quarters):
        g.commit()
        if q == 1:
            g.buy_now("power", 8)
            g.buy_now("accels", 600)
        if q == 2:
            g.buy_now("accels", {"count": 300, "supplier": "Aurex"})
        if q == 3:
            o = g.orders
            o.price_stance = 0.8
            g.buy_now("data", "code_repos")
            g.buy_now("raise", 0.1)
    save = {"seed": seed, "randomized": True, "months": g.world.month,
            "log": [[m, who, c] for m, who, c in g.world.action_log]}
    save = json.loads(json.dumps(save))
    w2 = replay(save)
    ok = same_run(g.world, w2)
    n = len(g.policy.interrupts)
    print(f"  played game, seed {seed}, {quarters} quarters, {n} interrupts answered"
          f"  -> {'IDENTICAL' if ok else 'DIVERGED'}")
    return ok


if __name__ == "__main__":
    seeds = [int(x) for x in sys.argv[1:]]
    print("REPLAY CHECK  (record -> save -> replay, must match bit for bit)")
    ok = check_illegal()
    ok &= check_game()
    if seeds:
        for s in seeds:
            ok &= check(s, randomized=True)
    else:
        ok &= check(0, randomized=False)
        ok &= check(7, randomized=True)
    print("  seam holds" if ok else "  SEAM LEAKS")
    sys.exit(0 if ok else 1)
