"""
Is it a race, or a coronation?

Runs the model across many seeds and reports the distribution of lead
changes, how long the dominant lab holds, and how often a run ends in a
runaway. This is the fun/realism instrument: calibration says whether the
model matches history, this says whether the history it produces is worth
playing through.
"""
import statistics
from . import constants as K
from . import domains as D
from . import objectives as OBJ
from .world import World
from .scenarios import historical_2020, randomized_2020


def analyse(seed, months=132, randomized=True):
    labs = randomized_2020(seed) if randomized else historical_2020()
    w = World(labs, seed=seed)
    caps_hist = []
    for _ in range(months):
        w.step()
        caps_hist.append({l.name: (dict(l.model.caps) if l.model else {})
                          for l in w.labs})
    out = {"domains": {}, "ships": {}, "shelved": {}, "breakthroughs": 0,
           "strategies": {}, "withheld": 0}
    for dom in D.DOMAIN_KEYS:
        seq = []
        for frame in caps_hist:
            best, who = 0.0, None
            for name, caps in frame.items():
                c = caps.get(dom, 0.0)
                if c > best:
                    best, who = c, name
            if who:
                seq.append(who)
        if not seq:
            out["domains"][dom] = (0, 0.0, 0)
            continue
        changes = sum(1 for a, b in zip(seq, seq[1:]) if a != b)
        held = {}
        for x in seq:
            held[x] = held.get(x, 0) + 1
        top = max(held.values()) / len(seq)
        longest, cur, prev = 0, 0, None
        for x in seq:
            cur = cur + 1 if x == prev else 1
            prev = x
            longest = max(longest, cur)
        out["domains"][dom] = (changes, top, longest)
    snap = OBJ.snapshot(w)
    tot_rev = sum(sum(x.seg_revenue.values()) for x in w.labs) or 1.0
    for l in w.labs:
        goal_score, detail, _m = OBJ.evaluate(l, w, snap)
        out["strategies"][l.doctrine["strategy"]] = {
            "goal": goal_score,
            "detail": detail,
            "rev_share": sum(l.seg_revenue.values()) / tot_rev,
            "cap": l.model.capability if l.model else 0.0,
            "ships": len([s for s in l.ships if s[1] == "pretrain"]),
        }
        out["withheld"] += l.withheld_months
        out["ships"][l.name] = len([s for s in l.ships if s[1] == "pretrain"])
        out["shelved"][l.name] = l.shelved
        out["breakthroughs"] += len([s for s in l.ships if s[2] == "breakthrough"])
    # revenue concentration at the end
    rev = sorted((sum(l.seg_revenue.values()) for l in w.labs), reverse=True)
    tot = sum(rev) or 1.0
    out["top_share"] = rev[0] / tot
    out["alive"] = sum(1 for r in rev if r > tot * 0.02)
    return out


def report(seeds=24, months=132):
    rows = [analyse(s, months) for s in range(seeds)]
    print(f"BALANCE over {seeds} seeds\n")
    print(f"  {'domain':8s}{'lead changes':>22s}{'dominant holds':>18s}"
          f"{'longest reign':>15s}")
    for dom in D.DOMAIN_KEYS:
        ch = [r["domains"][dom][0] for r in rows]
        sh = [r["domains"][dom][1] for r in rows]
        lo = [r["domains"][dom][2] for r in rows]
        print(f"  {dom:8s}{statistics.mean(ch):8.1f} "
              f"(min {min(ch)}, max {max(ch)}){statistics.mean(sh)*100:15.0f}%"
              f"{statistics.mean(lo):12.0f} mo")
    allch = [sum(r["domains"][d][0] for d in D.DOMAIN_KEYS) for r in rows]
    tops = [r["top_share"] for r in rows]
    runaway = sum(1 for r in rows if r["top_share"] > 0.60) / len(rows)
    print(f"\n  total lead changes per run : mean {statistics.mean(allch):.1f}"
          f"  median {statistics.median(allch):.0f}"
          f"  range {min(allch)}-{max(allch)}")
    print(f"  top lab's revenue share    : mean {statistics.mean(tops)*100:.0f}%"
          f"  range {min(tops)*100:.0f}-{max(tops)*100:.0f}%")
    print(f"  runs ending in a runaway   : {runaway*100:.0f}%  (top lab over 60%)")
    print(f"  labs still viable at 2030  : {statistics.mean([r['alive'] for r in rows]):.1f} of 7")
    print("\n  DID EACH STRATEGY MEET ITS OWN GOALS?")
    print("  Revenue share is the wrong scoreboard for most of these; each is")
    print("  scored against what it was actually trying to do.\n")
    print(f"    {'strategy':14s}{'games':>7s}{'goal score':>12s}{'achieved':>11s}"
          f"{'rev share':>11s}")
    agg = {}
    for r in rows:
        for k, v in r["strategies"].items():
            a = agg.setdefault(k, {"n": 0, "rev": 0.0, "goal": 0.0, "won": 0,
                                   "goals": {}})
            a["n"] += 1
            a["rev"] += v["rev_share"]
            a["goal"] += v["goal"]
            a["won"] += 1 if v["goal"] >= 0.65 else 0
            for label, frac in v["detail"]:
                a["goals"].setdefault(label, []).append(frac)
    for k in sorted(agg, key=lambda x: -agg[x]["goal"] / max(agg[x]["n"], 1)):
        a = agg[k]
        print(f"    {k:14s}{a['n']:7d}{a['goal']/a['n']*100:11.0f}%"
              f"{a['won']/a['n']*100:10.0f}%{a['rev']/a['n']*100:10.0f}%")
    print("\n  WHICH GOALS ARE FAILING")
    for k in sorted(agg):
        a = agg[k]
        worst = sorted(a["goals"].items(),
                       key=lambda kv: sum(kv[1]) / len(kv[1]))[:2]
        bits = " · ".join(f"{lbl[:40]} {sum(v)/len(v)*100:.0f}%" for lbl, v in worst)
        print(f"    {k:14s}{bits}")
    wh = statistics.mean([r["withheld"] for r in rows])
    print(f"\n  months of capability deliberately withheld: {wh:.0f} per run")
    ships = [sum(r["ships"].values()) for r in rows]
    shelved = [sum(r["shelved"].values()) for r in rows]
    brk = [r["breakthroughs"] for r in rows]
    print(f"\n  pretrained models shipped  : {statistics.mean(ships):.0f} per run, "
          f"all labs combined")
    print(f"  runs shelved as not better : {statistics.mean(shelved):.0f} per run "
          f"({statistics.mean(shelved)/max(1,statistics.mean(ships)+statistics.mean(shelved))*100:.0f}% of runs)")
    print(f"  breakthrough runs          : {statistics.mean(brk):.1f} per run")


if __name__ == "__main__":
    import sys
    report(int(sys.argv[1]) if len(sys.argv) > 1 else 24)
