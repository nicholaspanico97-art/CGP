"""
The hardware supply chain: foundries, memory makers, chip designers.

v1.10: the tier exists, is fed the sector's real order flow every month,
runs its own deterministic rules (HARDWARE.md 3), and is shown on the
Hardware tab. It does NOT yet change what a lab can buy: labs still buy
the year's best chip from constants.ACCELERATORS at list price with a
5-month lead. Wiring order and the anchors the tier must reproduce first
are in HARDWARE.md 5 and 6.

Nothing here draws randomness, so replay is unaffected.
"""
import math
from . import constants as K
from . import anchors as A

WAFER_USABLE_MM2 = 10_000.0     # 300 mm wafer, after yield on a reticle-sized die
PACKAGING_COST = 2_500.0        # $/module: packaging, test, board, cooling
CHIPS_PER_PACKAGING_WAFER = 32  # interposer wafers per month -> chips
GEN_COST_0 = 1.2e9              # R&D to land the first next generation
GEN_COST_GROWTH = 1.6
GEN_MIN_MONTHS = 24
PERF_STEP_SAME_NODE = 2.0
PERF_STEP_NEW_NODE = 2.8
WATT_STEP = 1.35


def _mi(y, m):
    return A.month_index((y, m))


class Chip:
    __slots__ = ("name", "lands", "peak_tflops", "watts", "hbm_gb", "die_mm2", "node")

    def __init__(self, name, lands, peak_tflops, watts, hbm_gb, die_mm2, node):
        self.name, self.lands = name, lands
        self.peak_tflops, self.watts = peak_tflops, watts
        self.hbm_gb, self.die_mm2, self.node = hbm_gb, die_mm2, node

    def perf_per_watt(self):
        return self.peak_tflops / self.watts

    def as_accelerator(self, price):
        """The chip as something a fleet can hold (economics.Accelerator)."""
        from . import economics as E
        y, mo = 2020 + self.lands // 12, 1 + self.lands % 12
        return E.Accelerator((self.name, (y, mo), self.peak_tflops, self.watts,
                              price, 0.40, 0.24))


class Foundry:
    def __init__(self, name, wafers_k, packaging_k, wafer_price, node, bloc,
                 packaging_from=None, growth=0.0):
        self.name = name
        self.wafers_k = float(wafers_k)          # per month
        self.packaging_k = float(packaging_k)    # interposer wafers per month
        self.wafer_price = float(wafer_price)
        self.node0 = node                        # 0 = leading edge in 2020
        self.node = node
        self.bloc = bloc
        self.packaging_from = packaging_from     # (month, k/mo) when it starts
        self.growth = growth                     # state-driven growth, per year
        self.util_hist = []                      # wafer utilisation, monthly
        self.pkg_util_hist = []
        self.pending = []                        # (lands_month, kind, delta)
        self.booked_wafers = 0.0
        self.booked_pkg = 0.0
        self.capex_by_year = {}

    def step(self, m):
        # capacity landing
        keep = []
        for lands, kind, delta in self.pending:
            if lands <= m:
                if kind == "wafers":
                    self.wafers_k += delta
                else:
                    self.packaging_k += delta
            else:
                keep.append((lands, kind, delta))
        self.pending = keep
        if self.packaging_from and m == self.packaging_from[0]:
            self.packaging_k = self.packaging_from[1]
        # the record's pre-surge packaging growth, ~40%/yr to end 2022
        # (4k -> 8k); after that the forecast rule carries it
        if self.packaging_k > 0 and m < 36:
            self.packaging_k *= 1.40 ** (1 / 12)
        if self.growth:
            self.wafers_k *= (1 + self.growth) ** (1 / 12)
        # the leading edge moves about one node every 30 months
        self.node = self.node0 + m // 30
        # utilisation from last month's bookings, on top of the non-AI
        # load (phones, PCs, cloud CPUs) that keeps a leading-edge fab
        # ~82% busy on its own, growing ~2%/yr
        non_ai = 0.82 * (1.02 ** (m / 12.0))
        u = non_ai + self.booked_wafers / max(self.wafers_k * 1e3, 1.0)
        pu = self.booked_pkg / max(self.packaging_k * 1e3, 1.0) if self.packaging_k > 0 else 0.0
        self.util_hist.append(u)
        self.pkg_util_hist.append(pu)
        # capex rule: sustained high utilisation -> capacity 30 months out
        year = 2020 + m // 12
        if len(self.util_hist) >= 12 and min(self.util_hist[-12:]) > 0.90 \
                and not any(k == "wafers" for _l, k, _d in self.pending):
            self.pending.append((m + 30, "wafers", self.wafers_k * 0.25))
            self.capex_by_year[year] = self.capex_by_year.get(year, 0.0) + self.wafers_k * 0.25 * 1e3 * 1.2e5
        # packaging is cheaper and faster to add than a fab: a doubling
        # lands 12 months after six months of saturation (the record is
        # ~x19 from 2020 to 2025, demand-driven)
        # ... and it is built on forecast, not on saturation: three months
        # above 70% is enough
        if self.packaging_k > 0 and len(self.pkg_util_hist) >= 3 and min(self.pkg_util_hist[-3:]) > 0.70                 and sum(1 for _l, k, _d in self.pending if k == "pkg") < 3:
            self.pending.append((m + 12, "pkg", self.packaging_k * 1.0))
        self.booked_wafers = 0.0
        self.booked_pkg = 0.0


class MemoryMaker:
    def __init__(self, name, eb_per_year, price_per_gb, bloc):
        self.name = name
        self.capacity_gb = eb_per_year * 1e9 / 12.0      # GB per month
        self.base_price = float(price_per_gb)
        self.price = float(price_per_gb)
        self.bloc = bloc
        self.util_hist = []
        self.pending = []
        self.demand_gb = 0.0

    def step(self, m):
        keep = []
        for lands, delta in self.pending:
            if lands <= m:
                self.capacity_gb += delta
            else:
                keep.append((lands, delta))
        self.pending = keep
        u = self.demand_gb / max(self.capacity_gb, 1.0)
        self.util_hist.append(u)
        self.price = self.base_price * max(0.5, min(2.2, u)) ** 0.8
        if len(self.util_hist) >= 9 and min(self.util_hist[-9:]) > 0.90 and len(self.pending) < 2:
            self.pending.append((m + 18, self.capacity_gb * 0.30))
        self.demand_gb = 0.0


class Designer:
    def __init__(self, name, bloc, chips, rd_rate, margin, foundry, for_sale=True,
                 stickiness=0.0, sells_to=None, rd_floor=0.0):
        self.name, self.bloc = name, bloc
        self.rd_floor = rd_floor                 # $/yr from other businesses
        self.chips = list(chips)                 # generations, in order
        self.rd_rate = rd_rate
        self.margin = margin
        self.foundry = foundry                   # Foundry name
        self.for_sale = for_sale
        self.stickiness = stickiness             # software moat, in logit units
        self.sells_to = sells_to                 # None = anyone allowed by controls
        self.rd_bank = 0.0
        self.gen_cost = GEN_COST_0
        self.last_gen_month = 0
        self.cash = 0.0
        self.revenue_m = 0.0
        self.revenue_by_year = {}
        self.backlog = 0.0                       # chips ordered, not yet built
        self.built_m = 0.0
        self.lead_months = 5.0
        self.share = 0.0
        self.orders_hist = []

    def current(self, m):
        avail = [c for c in self.chips if c.lands <= m]
        return avail[-1] if avail else None

    def next_gen(self, m):
        later = [c for c in self.chips if c.lands > m]
        return later[0] if later else None

    def unit_cost(self, m, foundries, hbm_price):
        c = self.current(m)
        if c is None:
            return 0.0
        f = foundries[self.foundry]
        return (c.die_mm2 / WAFER_USABLE_MM2 * f.wafer_price
                + c.hbm_gb * hbm_price + PACKAGING_COST)

    def price(self, m, foundries, hbm_price):
        # margin is a gross margin: price = cost / (1 - margin)
        return self.unit_cost(m, foundries, hbm_price) / max(1.0 - self.margin, 0.2)


class Hardware:
    def __init__(self):
        self.foundries = {
            "Tessera": Foundry("Tessera", 120, 4, 17_000, 0, "RoW"),
            "Halden":  Foundry("Halden", 40, 0, 13_600, -1, "US", packaging_from=(_mi(2024, 1), 2)),
            "Jinhua":  Foundry("Jinhua", 15, 0, 9_000, -2, "China", packaging_from=(_mi(2025, 1), 1)),
        }
        self.memory = {
            "Sora Memory": MemoryMaker("Sora Memory", 0.035, 25, "RoW"),
            "Nordmark":    MemoryMaker("Nordmark", 0.025, 27, "RoW"),
        }
        V, A100, H100 = 125.0, 312.0, 989.0
        self.designers = {
            "Aurex": Designer("Aurex", "US", [
                Chip("AX-1", _mi(2017, 5), V, 300, 32, 815, 0),
                Chip("AX-2", _mi(2020, 5), A100, 400, 40, 826, 0)],
                rd_rate=0.25, margin=0.65, foundry="Tessera", stickiness=1.5),
            "Vega Silicon": Designer("Vega Silicon", "US", [
                Chip("KS-1", _mi(2018, 6), 90.0, 300, 32, 700, 0)],
                rd_rate=0.35, margin=0.40, foundry="Tessera", rd_floor=1.5e9),
            "Lattice": Designer("Lattice", "US", [
                Chip("LT-3", _mi(2019, 1), 110.0, 250, 32, 650, 0)],
                rd_rate=0.30, margin=0.0, foundry="Tessera", for_sale=False),
            "Huaxin": Designer("Huaxin", "China", [
                Chip("HX-1", _mi(2019, 6), 45.0, 320, 16, 600, -1)],
                rd_rate=0.30, margin=0.35, foundry="Jinhua", sells_to=("China",), rd_floor=1.0e9),
        }
        # seed the challenger's and the domestic designer's next generations
        self.designers["Vega Silicon"].chips.append(Chip("KS-2", _mi(2021, 6), 250.0, 400, 40, 750, 0))
        self.designers["Huaxin"].chips.append(Chip("HX-2", _mi(2022, 3), 120.0, 350, 32, 640, -1))
        self.month = 0
        self.history = []
        self.demand_chips = 0.0
        self.demand_by_bloc = {}

    # --------------------------------------------------------- the month
    def hbm_price(self):
        ms = list(self.memory.values())
        return sum(x.price for x in ms) / len(ms)

    def step(self, world):
        m = world.month
        self.month = m
        geo = getattr(world, "geo", None)
        access = {b: s["access"] for b, s in geo.blocs.items()} if geo else {}
        self._access = access
        from . import geo as GEO

        # 1. demand: what the sector ordered this month, by bloc
        demand_by_bloc = {}          # orders placed: what sits in a backlog
        wanted_by_bloc = {}          # orders wanted: what the industry builds for
        for lab in world.labs:
            n = getattr(lab, "accels_bought_month", 0) or 0
            wnt = max(getattr(lab, "accels_wanted_month", 0) or 0, n)
            b = GEO.bloc_of(lab)
            if n > 0:
                demand_by_bloc[b] = demand_by_bloc.get(b, 0.0) + n
            if wnt > 0:
                wanted_by_bloc[b] = wanted_by_bloc.get(b, 0.0) + wnt
        self.demand_by_bloc = demand_by_bloc
        self.demand_chips = sum(demand_by_bloc.values())
        self.wanted_chips = sum(wanted_by_bloc.values())
        # unmet demand, as a multiple of what was placed: the foundries book
        # against it (they build for the orders they turned away too)
        self.unmet_mult = (self.wanted_chips / self.demand_chips) if self.demand_chips > 0 else 1.0

        # 2. allocate demand across sellers, per bloc, by perf/$ and lead time
        hbm = self.hbm_price()
        sellers = [d for d in self.designers.values() if d.for_sale and d.current(m)]
        orders = {name: 0.0 for name in self.designers}
        # orders placed with a named supplier go straight to it; the rest
        # of what was wanted (turned away by supply) queues by the rule
        named = 0.0
        for lab in world.labs:
            for name, n in (getattr(lab, "bought_from_month", None) or {}).items():
                if name in orders:
                    orders[name] += n
                    named += n
            lab.bought_from_month = {}
        for b, n in wanted_by_bloc.items():
            n = max(0.0, n - named * (wanted_by_bloc[b] / max(self.wanted_chips, 1.0)))
            elig = [d for d in sellers if self._may_sell(d, b, access)]
            if not elig:
                continue
            scores = []
            for d in elig:
                c = d.current(m)
                p = max(d.price(m, self.foundries, hbm), 1.0)
                perf_per_dollar = c.peak_tflops / p
                scores.append(2.0 * math.log(perf_per_dollar) - 0.15 * d.lead_months + d.stickiness)
            mx = max(scores)
            ws = [math.exp(s - mx) for s in scores]
            tot = sum(ws)
            for d, w in zip(elig, ws):
                orders[d.name] += n * w / tot
        # in-house silicon: its parent's lab buys from it (not modelled per lab yet)

        # 3. each designer: book capacity, build, ship, book revenue, do R&D
        total_rev = 0.0
        for d in self.designers.values():
            c = d.current(m)
            if c is None:
                continue
            d.backlog += orders[d.name]
            d.orders_hist.append(orders[d.name])
            f = self.foundries[d.foundry]
            # capacity this designer can get: pro rata on trailing orders
            want_chips = max(d.backlog, 0.0)
            wafers_needed = want_chips * c.die_mm2 / WAFER_USABLE_MM2
            pkg_needed = want_chips / CHIPS_PER_PACKAGING_WAFER
            f.booked_wafers += wafers_needed
            f.booked_pkg += pkg_needed
            # what the foundry can actually build for it this month
            share_of_f = self._foundry_share(d, m)
            wafer_cap = f.wafers_k * 1e3 * share_of_f
            pkg_cap = (f.packaging_k * 1e3 * share_of_f * CHIPS_PER_PACKAGING_WAFER
                       if f.packaging_k > 0 else want_chips)
            buildable = min(want_chips, wafer_cap * WAFER_USABLE_MM2 / c.die_mm2, pkg_cap)
            built = max(0.0, buildable)
            d.backlog -= built
            # orders that cannot be served within a year lapse - a lab
            # re-decides monthly, it does not queue forever
            d.backlog = min(d.backlog, 12.0 * max(built, 1.0))
            d.built_m = built
            rate = max(built, 1.0)
            d.lead_months = 5.0 + (d.backlog / rate if d.backlog > 0 else 0.0) * 0.5
            d.lead_months = min(d.lead_months, 24.0)
            price = d.price(m, self.foundries, hbm)
            rev = built * price if d.for_sale else built * d.unit_cost(m, self.foundries, hbm)
            d.revenue_m = rev
            year = 2020 + m // 12
            d.revenue_by_year[year] = d.revenue_by_year.get(year, 0.0) + rev
            total_rev += rev if d.for_sale else 0.0
            d.cash += rev * d.margin if d.for_sale else 0.0
            # memory demand
            for mm in self.memory.values():
                mm.demand_gb += built * c.hbm_gb / len(self.memory)
            # margin rule
            if d.for_sale:
                if d.lead_months > 6:
                    d.margin = min(0.75, d.margin + 0.02)
                elif d.lead_months < 3:
                    d.margin = max(0.25, d.margin - 0.02)
            # R&D
            best_ppw = max(x.current(m).perf_per_watt() for x in self.designers.values() if x.current(m))
            behind = c.perf_per_watt() < best_ppw * 0.999
            rd = max(rev * d.rd_rate, d.rd_floor / 12.0) * (1.5 if behind else 1.0)
            d.rd_bank += rd
            if d.next_gen(m) is None and d.rd_bank >= d.gen_cost and m - d.last_gen_month >= GEN_MIN_MONTHS:
                self._land_generation(d, m)
        for d in self.designers.values():
            if d.for_sale and d.current(m):
                d.share = d.revenue_m / total_rev if total_rev > 0 else 0.0

        # 4. foundries and memory step
        for f in self.foundries.values():
            f.step(m)
        for mm in self.memory.values():
            mm.step(m)
        self.history.append(self.snapshot())

    def sellable_per_month(self, bloc=None):
        """
        Chips the industry can deliver to labs this month: packaging
        capacity at the foundries that sell into `bloc` (all, if None),
        times chips per packaging wafer, times the share of packaging that
        goes to AI. Demand-responsive through the foundries' capex rules
        (v1.19, HARDWARE.md 5 step 3 / ROADMAP item 8).
        """
        access = getattr(self, "_access", {})
        total = 0.0
        for f in self.foundries.values():
            if f.packaging_k <= 0:
                continue
            if bloc == "China" and f.bloc != "China" and access.get("China", 1.0) < 0.5:
                continue                    # controls: only the domestic fab
            total += f.packaging_k * 1e3 * CHIPS_PER_PACKAGING_WAFER
        return total * 0.8

    def offers(self, bloc, m=None):
        """What each seller offers a lab in `bloc` this month: chip, price,
        lead time, perf per dollar - and whether controls allow it."""
        m = self.month if m is None else m
        geo_access = getattr(self, "_access", {})
        hbm = self.hbm_price()
        out = []
        for d in self.designers.values():
            c = d.current(m)
            if c is None or not d.for_sale:
                continue
            allowed = self._may_sell(d, bloc, geo_access)
            price = d.price(m, self.foundries, hbm)
            out.append(dict(designer=d.name, chip=c.name, tflops=c.peak_tflops, watts=c.watts,
                            hbm_gb=c.hbm_gb, price=price, lead_months=int(round(max(3.0, min(14.0, d.lead_months)))),
                            perf_per_dollar=c.peak_tflops / max(price, 1.0), allowed=allowed,
                            share=d.share, backlog=d.backlog))
        out.sort(key=lambda o: -o["perf_per_dollar"])
        return out

    def choose(self, bloc, m=None, price_sensitivity=0.0):
        """
        The seller a buyer in `bloc` picks this month: best score on perf
        per dollar, lead time and the incumbent's software moat - the same
        scoring the tier allocates demand with, taken deterministically.
        `price_sensitivity` (0-1) is the buyer's: a cost-led lab weighs
        perf per dollar more and the moat less. Returns (designer, chip,
        price, lead) or None if nobody may sell.
        """
        best = None
        ps = max(0.0, min(1.0, price_sensitivity))
        for o in self.offers(bloc, m):
            if not o["allowed"]:
                continue
            d = self.designers[o["designer"]]
            score = (2.0 * (1.0 + ps) * math.log(o["perf_per_dollar"]) - 0.15 * o["lead_months"]
                     + d.stickiness * (1.0 - ps))
            if best is None or score > best[0]:
                best = (score, o)
        if best is None:
            return None
        o = best[1]
        return self.designers[o["designer"]], self.designers[o["designer"]].current(m or self.month), o["price"], o["lead_months"]

    def _may_sell(self, d, bloc, access):
        if d.sells_to is not None:
            return bloc in d.sells_to
        if d.bloc == "US" and bloc == "China":
            # controls: access below 0.5 means US designers cannot sell in
            return access.get("China", 1.0) >= 0.5
        return True

    def _foundry_share(self, d, m):
        f = self.foundries[d.foundry]
        same = [x for x in self.designers.values() if x.foundry == d.foundry and x.current(m)]
        tot = sum(sum(x.orders_hist[-6:]) for x in same) or 1.0
        mine = sum(d.orders_hist[-6:])
        # a foundry keeps ~40% of leading-edge for non-AI customers
        return 0.6 * (mine / tot if tot > 0 else 1.0 / len(same))

    def _land_generation(self, d, m):
        cur = d.current(m)
        f = self.foundries[d.foundry]
        new_node = f.node > cur.node                   # the foundry has moved a node since
        step = PERF_STEP_NEW_NODE if new_node else PERF_STEP_SAME_NODE
        n = len(d.chips) + 1
        prefix = cur.name.split("-")[0]
        d.chips.append(Chip(f"{prefix}-{n}", m + 12, cur.peak_tflops * step,
                            cur.watts * WATT_STEP, cur.hbm_gb * 1.5, min(900, cur.die_mm2 * 1.05),
                            f.node))
        d.rd_bank -= d.gen_cost
        d.gen_cost *= GEN_COST_GROWTH
        d.last_gen_month = m

    # ------------------------------------------------------------ views
    def snapshot(self):
        m = self.month
        hbm = self.hbm_price()
        des = []
        for d in self.designers.values():
            c, nx = d.current(m), d.next_gen(m)
            des.append(dict(
                name=d.name, bloc=d.bloc, for_sale=d.for_sale,
                chip=(dict(name=c.name, tflops=c.peak_tflops, watts=c.watts, hbm_gb=c.hbm_gb,
                           ppw=c.perf_per_watt()) if c else None),
                next=(dict(name=nx.name, lands=nx.lands, tflops=nx.peak_tflops, watts=nx.watts) if nx else None),
                price=d.price(m, self.foundries, hbm) if c else 0.0,
                cost=d.unit_cost(m, self.foundries, hbm) if c else 0.0,
                margin=d.margin, lead_months=d.lead_months, backlog=d.backlog,
                built_m=d.built_m, revenue_m=d.revenue_m, share=d.share,
                rd_bank=d.rd_bank, gen_cost=d.gen_cost, cash=d.cash,
                sells_to=list(d.sells_to) if d.sells_to else None))
        return dict(
            month=m, demand_chips=self.demand_chips, demand_by_bloc=dict(self.demand_by_bloc),
            hbm_price=hbm,
            foundries=[dict(name=f.name, bloc=f.bloc, wafers_k=f.wafers_k, packaging_k=f.packaging_k,
                            wafer_price=f.wafer_price, node=f.node,
                            util=(f.util_hist[-1] if f.util_hist else 0.0),
                            pkg_util=(f.pkg_util_hist[-1] if f.pkg_util_hist else 0.0),
                            pending=[(l, k, round(dd, 1)) for l, k, dd in f.pending])
                       for f in self.foundries.values()],
            memory=[dict(name=x.name, capacity_gb_month=x.capacity_gb, price=x.price,
                         util=(x.util_hist[-1] if x.util_hist else 0.0))
                    for x in self.memory.values()],
            designers=des)
