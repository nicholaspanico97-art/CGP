"""Dump a full run to JSON for the viewer."""
import json, math
from . import domains as D
from .world import World
from .scenarios import historical_2020
from .capability import BenchmarkModel


SUITE = {"LANG": "MMLU", "REASON": "GPQA", "CODE": "SWE", "AGENT": "AGENT",
         "IMAGE": "IMAGE", "VIDEO": "VIDEO", "AUDIO": "AUDIO", "ROBOT": "ROBOT"}


def r(x, n=3):
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))):
        return 0
    return round(float(x), n)


def run(months=132, seed=7):
    w = World(historical_2020(), seed=seed)
    bm = w.bm
    frames = []
    for m in range(months):
        w.step()
        segs = {}
        for k, (tam, rows) in getattr(w, "segment_state", {}).items():
            segs[k] = {"tam": r(tam * 12 / 1e9, 2),
                       "shares": {n: r(sh, 4) for n, sh in rows}}
        labs = {}
        for l in w.labs:
            h = l.history[-1]
            labs[l.name] = {
                "cash": r(h["cash"] / 1e9, 2),
                "rev": r(h["rev"] * 12 / 1e9, 3),
                "net": r(h["net"] * 12 / 1e9, 2),
                "accels": int(h["accels"]),
                "mw": r(h["mw"], 1),
                "price": r(h["price"], 3),
                "algo": r(h["algo"], 3),
                "run": h["largest"],
                "res": int(h.get("researchers", 0)),
                "stars": r(h.get("stars", 0), 1),
                "caps": {d: r(l.model.caps.get(d, 0), 2) for d in D.DOMAIN_KEYS}
                        if l.model else {d: 0 for d in D.DOMAIN_KEYS},
                "bench": {d: r(bm.score(SUITE[d], l.model.caps.get(d, 0)), 1)
                          for d in D.DOMAIN_KEYS} if l.model else
                         {d: 0 for d in D.DOMAIN_KEYS},
                "segrev": {k: r(v * 12 / 1e9, 3) for k, v in l.seg_revenue.items() if v > 0},
                "excl": sorted(l.data.exclusives),
                "ship": (l.ships[-1][1] if l.ships and l.ships[-1][0] == m else ""),
                "tag": (l.ships[-1][2] if l.ships and l.ships[-1][0] == m else ""),
                "shelved": l.shelved,
                "data": {d: r(math.log10(max(l.data.effective(d), 1)), 2)
                         for d in D.DOMAIN_KEYS},
            }
        frames.append({
            "m": m,
            "year": 2020 + m // 12,
            "month": m % 12 + 1,
            "spend": r(getattr(w, "spend_stock", 0) / 1e9, 2),
            "unlocked": r(getattr(w, "spend_unlocked", 0) / 1e9, 2),
            "comp": r(getattr(w, "market_comp", 0) / 1000, 1),
            "segments": segs,
            "labs": labs,
        })
    meta = {
        "releases": {l.name: [[int(x[0]), x[1], x[2]] for x in l.ships] for l in w.labs},
        "domains": D.DOMAIN_KEYS,
        "domain_names": {k: v["name"] for k, v in D.DOMAINS.items()},
        "anchored": {k: v["anchored"] for k, v in D.DOMAINS.items()},
        "segments": {k: {"name": v["name"], "gates": v["gates"],
                         "differentiation": v.get("differentiation", 0)}
                     for k, v in D.SEGMENTS.items()},
        "labs": [l.name for l in w.labs],
        "doctrines": {l.name: {"mixture": l.mixture} for l in w.labs},
        "sources": {k: {"name": v["name"], "exclusive": v["exclusive"]}
                    for k, v in D.DATA_SOURCES.items()},
    }
    return {"meta": meta, "frames": frames}


if __name__ == "__main__":
    import sys
    out = sys.argv[1] if len(sys.argv) > 1 else "run.json"
    data = run()
    with open(out, "w") as f:
        json.dump(data, f, separators=(",", ":"))
    print(f"wrote {out}: {len(data['frames'])} monthly frames, "
          f"{len(data['meta']['labs'])} labs")
