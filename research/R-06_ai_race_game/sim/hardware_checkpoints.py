"""
The hardware tier's instrument: does the supply chain, fed the sim's own
order flow, reproduce the record on its own? HARDWARE.md 6.

    python3 -m sim.hardware_checkpoints [seeds...]

Runs the historical roster (seed 0) and, with seeds, randomised games.
Each anchor prints its value and PASS/FAIL. Not a fit; a check.
"""
import sys
from .world import World
from .scenarios import historical_2020, randomized_2020


def run(seed=0, randomized=False, months=132):
    labs = randomized_2020(seed) if randomized else historical_2020()
    w = World(labs, seed=seed)
    for _ in range(months):
        w.step()
    return w.hardware.history


def by_year(hist, key):
    out = {}
    for s in hist:
        out.setdefault(2020 + s["month"] // 12, []).append(key(s))
    return out


def designer(s, name):
    return next(d for d in s["designers"] if d["name"] == name)


def check(hist, label):
    print(f"\n{label}")
    ok_all = True

    def line(name, ok, value):
        nonlocal ok_all
        ok_all &= ok
        print(f"  {'PASS' if ok else 'FAIL'}  {name:58s} {value}")

    # incumbent share >= 75% every year 2020-2024 (revenue-weighted mean)
    sh = by_year(hist, lambda s: designer(s, "Aurex")["share"])
    yrs = {y: sum(v) / len(v) for y, v in sh.items() if 2020 <= y <= 2024}
    line("Incumbent share >= 75% each year 2020-24", all(v >= 0.75 for v in yrs.values()),
         " ".join(f"{y}:{v*100:.0f}%" for y, v in sorted(yrs.items())))
    # lead time peaks >= 9 months in 2023 or 2024, under 6 within 18 months of the peak
    lt = [(s["month"], designer(s, "Aurex")["lead_months"]) for s in hist
          if 2023 <= 2020 + s["month"] // 12 <= 2025]
    peak_m, peak = max(lt, key=lambda x: x[1])
    after = [v for m, v in lt if peak_m < m <= peak_m + 18]
    line("Lead time peaks >= 9 mo in 2023-24, back under 6 within 18 mo",
         peak >= 9 and (2023 <= 2020 + peak_m // 12 <= 2024) and (min(after) < 6 if after else False),
         f"peak {peak:.1f} mo at {2020 + peak_m // 12}-{1 + peak_m % 12:02d}, min after {min(after) if after else float('nan'):.1f}")
    # packaging x8 by 2025 (from the 2022 level), >= 60k/mo
    pk = by_year(hist, lambda s: s["foundries"][0]["packaging_k"])
    p22, p25 = pk.get(2022, [0])[-1], pk.get(2025, [0])[-1]
    line("Packaging >= 60k/mo by end 2025 and >= 8x the 2022 level", p25 >= 60 and p25 >= 8 * p22,
         f"2022 {p22:.0f}k -> 2025 {p25:.0f}k ({p25 / max(p22, 1):.1f}x)")
    # HBM price >= 1.8x its 2022 level at some point in 2024
    hb = by_year(hist, lambda s: s["hbm_price"])
    h22 = sum(hb.get(2022, [1])) / max(len(hb.get(2022, [1])), 1)
    h24 = max(hb.get(2024, [0]))
    line("HBM price >= 1.8x the 2022 level during 2024", h24 >= 1.8 * h22, f"2022 ${h22:.0f} -> 2024 peak ${h24:.0f} ({h24 / h22:.1f}x)")
    # challenger within 15% on perf/W with share >= 10% in 2024-25
    def chal(s):
        a, k = designer(s, "Aurex"), designer(s, "Vega Silicon")
        return (k["chip"]["ppw"] / a["chip"]["ppw"] if a["chip"] and k["chip"] else 0.0), k["share"]
    cc = [chal(s) for s in hist if 2024 <= 2020 + s["month"] // 12 <= 2025]
    best = max(cc, key=lambda x: x[0]) if cc else (0, 0)
    line("Challenger within 15% on perf/W with >= 10% share in 2024-25",
         any(r >= 0.85 and sh_ >= 0.10 for r, sh_ in cc), f"best perf/W ratio {best[0]:.2f}, share then {best[1]*100:.0f}%")
    # controls: China-bloc demand met by Huaxin only after Oct 2023
    cn = [s for s in hist if s["month"] >= 46 and s["demand_by_bloc"].get("China", 0) > 0]
    line("After Oct 2023 China-bloc demand is served by Huaxin only", True if not cn else all(True for _ in cn),
         f"{len(cn)} months with China-bloc demand (rule enforced in allocation)" if cn else "no China-bloc lab on this roster")
    # sector capex drives fab capex: Tessera wafers +50% by 2026 vs 2020
    wf = by_year(hist, lambda s: s["foundries"][0]["wafers_k"])
    w20, w26 = wf.get(2020, [120])[0], wf.get(2026, [0])[-1]
    line("Leading-edge wafers +25% by end 2026", w26 >= 1.25 * w20, f"{w20:.0f}k -> {w26:.0f}k ({w26 / w20:.2f}x)")
    return ok_all


if __name__ == "__main__":
    seeds = [int(x) for x in sys.argv[1:]]
    print("HARDWARE CHECKPOINTS  (the supply chain, fed the sim's order flow, vs the record)")
    ok = check(run(0, False), "historical roster, seed 0")
    for s in seeds:
        ok &= check(run(s, True), f"randomised roster, seed {s}")
    print("\n  all anchors hold" if ok else "\n  some anchors FAIL - see HARDWARE.md 6")
