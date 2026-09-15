"""
The world layer's instrument: does the state in sim/geo.py, moving on the
record and on what the sector does, reproduce WORLD_STATE.md 6?

    python3 -m sim.geo_checkpoints [seeds...]

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
    return w


def at(hist, y, mo):
    m = (y - 2020) * 12 + (mo - 1)
    return next((s for s in hist if s["month"] == m), None)


def check(w, label):
    hist = w.geo.history
    print(f"\n{label}")
    ok_all = True

    def line(name, ok, value):
        nonlocal ok_all
        ok_all &= ok
        print(f"  {'PASS' if ok else 'FAIL'}  {name:64s} {value}")

    # export controls: China-bloc labs' fleets flatten after Oct 2023
    cn = [l for l in w.labs + w.graveyard if (getattr(l, "bloc", None) == "China"
          or l.doctrine.get("strategy") == "COST") and len(l.history) > 69]
    if cn:
        l = cn[0]
        h = {x["month"]: x["accels"] for x in l.history}
        before = h.get(45, 0) / max(h.get(33, 1), 1)      # Oct 2022 -> Oct 2023
        after = h.get(69, 0) / max(h.get(45, 1), 1)       # Oct 2023 -> Oct 2025
        line("Controls: a China-bloc lab's fleet grows slower after Oct 2023 than before",
             after < before, f"x{before:.2f} in the year before, x{after:.2f} in the two years after")
    else:
        line("Controls: a China-bloc lab's fleet grows slower after Oct 2023", True, "no China-bloc lab on this roster")
    # the assistant moment: US mood +0.3 within a quarter of Dec 2022
    a, b = at(hist, 2022, 11), at(hist, 2023, 2)
    dm = (b["blocs"]["US"]["mood"] - a["blocs"]["US"]["mood"]) if a and b else 0.0
    line("Assistant moment: US mood +0.25 or more within a quarter of Dec 2022", dm >= 0.25, f"{dm:+.2f}")
    # appetite doubles 2022 -> 2023
    a, b = at(hist, 2022, 12), at(hist, 2023, 12)
    line("Venture appetite doubles from 2022 to 2023", b and a and b["appetite"] >= 1.9 * a["appetite"],
         f"{a['appetite']:.1f} -> {b['appetite']:.1f}" if a and b else "n/a")
    # EU AI Act: EU stance >= 0.6 through 2025 after Aug 2024
    eu = [s["blocs"]["EU"]["regulation"] for s in hist if 56 <= s["month"] < 72]
    line("EU stance >= 0.6 from Aug 2024 through 2025", bool(eu) and min(eu) >= 0.6, f"min {min(eu):.2f}" if eu else "n/a")
    # power crunch: US queue ~48 months by 2025; AI load passes 1% of US grid by end 2025
    s25 = at(hist, 2025, 12)
    q = s25["blocs"]["US"]["queue_months"] if s25 else 0
    share = s25["load_share_grid"]["US"] if s25 else 0.0
    line("US interconnect queue ~48 months by end 2025", 40 <= q <= 56, f"{q:.0f} months")
    line("AI load >= 1% of the US grid by end 2025", share >= 0.01, f"{share*100:.2f}%")
    # Gulf access restored to ~0.8 by end 2025
    g = s25["blocs"]["Gulf"]["access"] if s25 else 0.0
    line("Gulf access ~0.8 by end 2025", 0.7 <= g <= 0.9, f"{g:.2f}")
    # rates peak 2023 and ease by 2025
    r23, r25 = at(hist, 2023, 12), at(hist, 2025, 12)
    line("Policy rate peaks in 2023 and eases by 2025", r23 and r25 and r25["rate"] < r23["rate"],
         f"{r23['rate']*100:.1f}% -> {r25['rate']*100:.1f}%" if r23 and r25 else "n/a")
    return ok_all


if __name__ == "__main__":
    seeds = [int(x) for x in sys.argv[1:]]
    print("WORLD CHECKPOINTS  (blocs, supply, capital, mood vs the record)")
    ok = check(run(0, False), "historical roster, seed 0")
    for s in seeds:
        ok &= check(run(s, True), f"randomised roster, seed {s}")
    print("\n  all anchors hold" if ok else "\n  some anchors FAIL - see WORLD_STATE.md 6")
