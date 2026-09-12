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
from .world import World
from .scenarios import historical_2020


def analyse(seed, months=132):
    w = World(historical_2020(), seed=seed)
    caps_hist = []
    for _ in range(months):
        w.step()
        caps_hist.append({l.name: (dict(l.model.caps) if l.model else {})
                          for l in w.labs})
    out = {"domains": {}, "ships": {}, "shelved": {}, "breakthroughs": 0}
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
    for l in w.labs:
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
