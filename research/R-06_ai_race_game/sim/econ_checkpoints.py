"""
The economy layer's instrument: does the labour-market demand model,
read beside the sim, reproduce the record? ECONOMY.md 5.

    python3 -m sim.econ_checkpoints [seeds...]

Prints each anchor with its value and PASS/FAIL, on the historical
roster and any randomised seeds given. Not a fit; a check. The switch
(K.DEMAND_MODEL) stays on the capability curve until this holds.
"""
import sys
from .world import World
from .scenarios import historical_2020, randomized_2020


def run(seed=0, randomized=False, months=132):
    labs = randomized_2020(seed) if randomized else historical_2020()
    w = World(labs, seed=seed)
    for _ in range(months):
        w.step()
    return w.economy.history, w


def at(hist, y, mo):
    m = (y - 2020) * 12 + (mo - 1)
    return next((s for s in hist if s["month"] == m), None)


def check(hist, w, label):
    print(f"\n{label}")
    ok_all = True

    def line(name, ok, value):
        nonlocal ok_all
        ok_all &= ok
        print(f"  {'PASS' if ok else 'FAIL'}  {name:62s} {value}")

    # enterprise AI spend ~$40B/yr in 2024 (labour model, enterprise tiers)
    s24 = at(hist, 2024, 12)
    ent24 = sum(v["realised_ent"] for v in s24["per_bloc"].values()) if s24 else 0.0
    line("Enterprise AI spend $25-60B/yr at end 2024 (labour model)", 25e9 <= ent24 <= 60e9, f"${ent24/1e9:.0f}B")
    # AI ~5% of US software spend in 2025
    s25 = at(hist, 2025, 12)
    us25 = s25["blocs"]["US"]["ai_share_software"] if s25 else 0.0
    line("US AI spend 3-8% of software spend at end 2025", 0.03 <= us25 <= 0.08, f"{us25*100:.1f}%")
    # no measurable productivity effect through 2025
    worst = max(abs(s["blocs"]["US"]["growth"] - s["blocs"]["US"]["trend"]) for s in hist if s["month"] < 72)
    line("US growth within +/-0.2 pt of trend through 2025 (negative anchor)", worst <= 0.002, f"max deviation {worst*100:.2f} pt")
    # knowledge-work unemployment flat through 2025
    du = max(s["blocs"]["US"]["unemployment"] - s["blocs"]["US"]["unemployment_0"] for s in hist if s["month"] < 72)
    line("US unemployment <= +0.5 pt over trend by end 2025 (negative anchor)", du <= 0.005, f"+{du*100:.2f} pt")
    # the labs' share of world AI spend, against the fitted lab-revenue curve
    from .econ import LAB_SHARE_2025
    for (y, target, name) in ((2023, 1e9, "$1B"), (2025, 10e9, "$10B")):
        s = at(hist, y, 12)
        lab_, cap_ = (s["labour_spend"] * LAB_SHARE_2025, s["capability_spend"]) if s else (0.0, 0.0)
        ratio = lab_ / cap_ if cap_ > 0 else float("inf")
        line(f"Labour model x labs' share within 2x of the curve, end {y}", 0.5 <= ratio <= 2.0,
             f"${lab_/1e9:.1f}B vs curve ${cap_/1e9:.1f}B ({ratio:.1f}x)")
    # by 2030 they converge within 3x
    s30 = hist[-1]
    ratio = s30["labour_spend"] / s30["capability_spend"] if s30["capability_spend"] > 0 else float("inf")
    line("Labour model within 3x of the capability curve at 2030", 0.33 <= ratio <= 3.0,
         f"labour ${s30['labour_spend']/1e9:.0f}B vs curve ${s30['capability_spend']/1e9:.0f}B ({ratio:.1f}x)")
    return ok_all


if __name__ == "__main__":
    seeds = [int(x) for x in sys.argv[1:]]
    print("ECONOMY CHECKPOINTS  (the labour-market demand model, read beside the sim, vs the record)")
    h, w = run(0, False)
    ok = check(h, w, "historical roster, seed 0")
    for s in seeds:
        h, w = run(s, True)
        ok &= check(h, w, f"randomised roster, seed {s}")
    print("\n  all anchors hold" if ok else "\n  some anchors FAIL - see ECONOMY.md 5")
