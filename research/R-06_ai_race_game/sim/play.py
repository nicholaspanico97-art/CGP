"""
Play Frontier in a terminal. One lab is yours; a turn is a quarter.

    python3 -m sim.play                     # seed 7, you are lab 0
    python3 -m sim.play --seed 11 --lab 3   # pick a world and a seat
    python3 -m sim.play --auto 8            # watch autopilot for 8 quarters

Each quarter you get the board letter, then a prompt. Type `help`. Orders
stay in force until you change them; `end` runs the next three months.
When a training run of yours lands, the game stops and asks whether to
ship it.

This is deliberately plain text: the point of playing is to find out where
the MODEL is wrong, not where the interface is.
"""
import sys
from . import domains as D
from .game import Game, date, _m
from .policy import Release, IllegalAction, validate, _BOUNDS

HELP = """
commands (orders stay in force until you change them)
  end                          run the next quarter on the current orders
  show                         the board letter again
  orders                       your standing orders, with units
  split T S E                  compute split, e.g.  split 0.5 0.3 0.2
  set FIELD VALUE              any numeric order, e.g.  set price_stance 0.8
                               comp_offer is in $k:      set comp_offer 950
  mix DOM W [DOM W ...]        training mixture, renormalised, e.g.  mix LANG .5 CODE .3 REASON .2
  buy SOURCE | buy none        the one non-exclusive corpus to license this quarter
  bid SOURCE $M                your ceiling at that corpus's auction, in $M
  unbid SOURCE                 withdraw a bid
  auto                         hand the seat to the strategy AI for the rest of the game
  save FILE                    save the game (seed + every decision)
  quit
"""

FIELDS = sorted(_BOUNDS)


def ask_release_cli(obs, candidate, held):
    lab = obs.lab
    new = candidate.caps
    old = lab.model.caps if lab.model else {}
    best_new = max(new.values()) if new else candidate.capability
    best_old = max(old.values()) if old else 0.0
    what = "The model you have been holding" if held else "Your training run has landed"
    print()
    print(f"  *** {date(obs.month)}: {what}. ***")
    print(f"      best domain {best_new:.2f}   what you sell now {best_old:.2f}   "
          f"the frontier as you fear it {obs.perceived_frontier:.2f}")
    cols = []
    for d in sorted(new, key=lambda d: -new[d]):
        if new[d] <= 0:
            continue
        cols.append(f"{d} {new[d]:.1f}" + (f" (now {old[d]:.1f})" if d in old else ""))
    print("      per domain, new (what you sell now):  " + "  ".join(cols))
    try:
        while True:
            ans = input("      ship it? [ship / hold]  > ").strip().lower()
            if ans in ("ship", "s", "y", "yes", ""):
                break
            if ans in ("hold", "h", "n", "no"):
                print("      held. You will be asked again next month.")
                return Release(ship=False)
            print("      answer ship or hold")
        while True:
            ans = input("      run the full evaluation first? costs nothing now; "
                        "skipping adds safety debt  [eval / skip]  > ").strip().lower()
            if ans in ("eval", "e", "y", "yes", ""):
                return Release(ship=True, evaluate=True)
            if ans in ("skip", "n", "no"):
                return Release(ship=True, evaluate=False)
            print("      answer eval or skip")
    except EOFError:
        print("      (no answer: shipped and evaluated)")
        return Release(ship=True, evaluate=True)


def _num(s):
    try:
        return float(s)
    except ValueError:
        raise IllegalAction(f"not a number: {s!r}")


def handle(g, line):
    """One command. Returns 'end', 'quit', or None."""
    parts = line.strip().split()
    if not parts:
        return None
    cmd, args = parts[0].lower(), parts[1:]
    o = g.orders.copy()          # edit a copy; a refused order changes nothing
    if cmd in ("end", "e", "next", "n"):
        return "end"
    if cmd in ("quit", "q", "exit"):
        return "quit"
    if cmd in ("help", "h", "?"):
        print(HELP)
    elif cmd in ("show", "letter", "l"):
        print(g.letter())
    elif cmd in ("orders", "o"):
        print(g.orders_text())
    elif cmd == "split":
        if len(args) != 3:
            raise IllegalAction("split needs three numbers: train serve experiment")
        t, s, e = (_num(x) for x in args)
        tot = t + s + e
        if tot <= 0:
            raise IllegalAction("split must be positive")
        o.train, o.serve, o.experiment = t / tot, s / tot, e / tot
        print(f"  split -> train {o.train:.0%} serve {o.serve:.0%} experiment {o.experiment:.0%}")
    elif cmd == "set":
        if len(args) != 2:
            raise IllegalAction("set FIELD VALUE")
        f, v = args[0], _num(args[1])
        if f in ("train", "serve", "experiment"):
            raise IllegalAction("use `split` for the compute split")
        if f not in _BOUNDS:
            raise IllegalAction(f"unknown order {f!r}; one of: {', '.join(FIELDS)}")
        if f == "comp_offer":
            v *= 1e3
        setattr(o, f, v)
        print(f"  {f} -> {v:g}")
    elif cmd == "mix":
        if len(args) < 2 or len(args) % 2:
            raise IllegalAction("mix DOM W [DOM W ...]")
        mix = {}
        for d, wgt in zip(args[::2], args[1::2]):
            d = d.upper()
            if d not in D.DOMAIN_KEYS:
                raise IllegalAction(f"unknown domain {d}; one of {', '.join(D.DOMAIN_KEYS)}")
            mix[d] = _num(wgt)
        tot = sum(mix.values())
        if tot <= 0:
            raise IllegalAction("mixture must be positive")
        o.mixture = {d: w / tot for d, w in mix.items()}
        print("  mixture -> " + " ".join(f"{d} {w:.2f}" for d, w in o.mixture.items()))
    elif cmd == "buy":
        if len(args) != 1:
            raise IllegalAction("buy SOURCE | buy none")
        key = args[0]
        if key == "none":
            o.data_buy = None
        else:
            if key not in D.DATA_SOURCES:
                raise IllegalAction(f"unknown source {key!r}")
            if D.DATA_SOURCES[key]["exclusive"]:
                raise IllegalAction(f"{key} is exclusive; use `bid`")
            o.data_buy = key
        print(f"  buying {o.data_buy or 'nothing'} this quarter")
    elif cmd == "bid":
        if len(args) != 2:
            raise IllegalAction("bid SOURCE $M")
        key, v = args[0], _num(args[1]) * 1e6
        bids = dict(o.data_bids or {})
        bids[key] = v
        o.data_bids = bids
        print(f"  ceiling at the {key} auction -> {_m(v)}")
    elif cmd == "unbid":
        bids = dict(o.data_bids or {})
        bids.pop(args[0], None)
        o.data_bids = bids
        print(f"  bid on {args[0]} withdrawn")
    elif cmd == "auto":
        g.policy.orders = None
        g.policy.decide = g.policy.defaults.decide       # the AI drives from here
        g.policy.ask = None
        print("  autopilot on: the strategy AI holds your seat from here")
    elif cmd == "save":
        path = args[0] if args else "game.json"
        g.save_to(path)
        print(f"  saved {path}")
    else:
        raise IllegalAction(f"unknown command {cmd!r}; type help")
    if cmd in ("split", "set", "mix", "buy", "bid", "unbid"):
        validate(o)
        g.policy.orders = o
    return None


def main(argv):
    seed, lab, auto, hist = 7, 0, 0, False
    it = iter(argv)
    for a in it:
        if a == "--seed":
            seed = int(next(it))
        elif a == "--lab":
            lab = int(next(it))
        elif a == "--auto":
            auto = int(next(it))
        elif a == "--historical":
            hist = True
    g = Game(seed=seed, player=lab, randomized=not hist,
             ask_release=None if auto else ask_release_cli)
    if auto:
        g.policy.decide = g.policy.defaults.decide
        for _ in range(auto):
            for e in g.commit():
                print(e)
            print()
        print(g.letter())
        return
    print(f"FRONTIER  -  seed {seed}, you are {g.player.name}. "
          f"A turn is a quarter. Type help.")
    print()
    print(g.letter())
    while not g.over:
        try:
            line = input(f"\n[{date(g.month)}] > ")
        except EOFError:
            print()
            return
        try:
            r = handle(g, line)
        except IllegalAction as e:
            print(f"  refused: {e}")
            continue
        if r == "quit":
            return
        if r == "end":
            print()
            for e in g.commit():
                print(e)
            print()
            print(g.letter())
    print("\n2030. The decade is over.")
    print(g.letter())


if __name__ == "__main__":
    main(sys.argv[1:])
