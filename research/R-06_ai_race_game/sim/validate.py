"""Replay 2020-2026 and score the simulation against what actually happened."""
import math
from . import anchors as A
from . import constants as K
from .world import World
from .scenarios import historical_2020


def run(months=84, quiet=False):
    w = World(historical_2020())
    for _ in range(months):
        w.step()
    if quiet:
        return w
    print("SECTOR TRAJECTORY  (model)")
    print(f"  {'year':6s}{'revenue $B':>12s}{'capex $B':>10s}{'accels':>10s}"
          f"{'GW':>7s}{'front C':>9s}{'$/Mtok':>9s}")
    for y in range(2020, 2020 + months // 12):
        m = (y - 2020) * 12 + 11
        rev = sum(l.history[m]["rev"] for l in w.labs) * 12 / 1e9
        accels = sum(l.history[m]["accels"] for l in w.labs)
        gw = sum(l.history[m]["mw"] for l in w.labs) / 1000.0
        cap = max(l.history[m]["cap"] for l in w.labs)
        price = min(l.history[m]["price"] for l in w.labs)
        capex = sum(getattr(l, "capex_by_year", {}).get(y, 0) for l in w.labs) / 1e9
        print(f"  {y:<6d}{rev:12.2f}{capex:10.1f}{accels:10,d}{gw:7.2f}{cap:9.2f}{price:9.2f}")

    print("\n  vs ACTUAL")
    print(f"  {'year':6s}{'revenue $B':>12s}{'capex $B':>10s}{'GW':>7s}")
    for y, lead, second, total, conf in A.LAB_REVENUE:
        capex = dict((a, b) for a, b, _c in A.SECTOR_CAPEX).get(y, float('nan'))
        gw = dict((a, b) for a, b, _c in A.POWER_DRAW).get(y, float('nan'))
        print(f"  {y:<6d}{total:12.2f}{capex:10.1f}{gw:7.2f}   [{conf}]")
    return w


if __name__ == "__main__":
    run()
