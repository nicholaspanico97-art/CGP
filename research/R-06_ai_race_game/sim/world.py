"""
The world: labs, months, and the market they share.

The simulation ticks monthly. A player turn is a quarter, so the game
surfaces every third tick; the months in between are where training runs
finish, hardware lands, and demand moves.
"""
import math
from . import constants as K
from . import anchors as A
from . import economics as E
from .capability import (BenchmarkModel, algo_efficiency, reasoning_multiplier,
                         capability_index)


class Model:
    """A shipped model: what it can do and what it costs to serve."""

    def __init__(self, name, capability, active_params, month):
        self.name = name
        self.capability = capability
        self.active_params = active_params
        self.shipped = month


class Lab:
    def __init__(self, name, doctrine, cash, researchers, fleet_accel,
                 fleet_count, start_month=0):
        self.name = name
        self.doctrine = doctrine          # dict of policy weights
        self.cash = cash
        self.researchers = researchers
        self.engineers = researchers * 2
        self.fleet = E.Fleet()
        self.fleet.add(fleet_accel, fleet_count, start_month)
        self.orders = []                  # [accel, count, arrival_month, paid]
        self.algo_mult = 1.0              # lab-specific, vs the frontier track
        self.rl_investment = 1.0
        self.train_bank = 0.0             # FLOP accumulated in the current run
        self.largest_run = 0.0            # engineering experience, in FLOP
        self.cooldown = 0                 # months between finishing and starting
        self.run_target = None
        self.model = None
        self.price_per_mtok = 40.0
        self.sub_price = 20.0
        self.subscribers = 0
        self.contracted_mw = fleet_accel.megawatts(fleet_count) * 1.4
        self.mw_pipeline = []             # [mw, arrival_month]
        self.capex_by_year = {}
        self.arr = 0.0                    # annualized revenue run-rate
        self.valuation = 1.0e9
        self.safety_debt = 0.0
        self.trust = 50.0
        self.revenue_m = 0.0
        self.history = []

    # -------------------------------------------------------------- compute
    def deliver(self, month):
        still = []
        for accel, count, arrival, _paid in self.orders:
            if arrival <= month:
                self.fleet.add(accel, count, month)
            else:
                still.append([accel, count, arrival, _paid])
        self.orders = still

    def order(self, accel, count, month, lead_months=6):
        cost = accel.capex * count
        if cost > self.cash:
            count = int(self.cash / accel.capex)
            cost = accel.capex * count
        if count <= 0:
            return 0
        self.cash -= cost
        self.orders.append([accel, count, month + lead_months, cost])
        return count

    # ------------------------------------------------------------- training
    def train_step(self, month, frac, months=1.0):
        """
        Pour compute into the current run. A run has a declared size; compute
        beyond it is not wasted on this run, it is simply not spent here -
        which is why a bigger fleet shortens a run rather than enlarging it.
        Returns the fraction of the training allocation left unused.
        """
        if self.run_target is None:
            return frac
        capacity = self.fleet.train_flops() * frac * K.SECONDS_PER_MONTH * months / 1.18
        needed = max(0.0, self.run_target - self.train_bank)
        used = min(capacity, needed)
        self.train_bank += used
        if capacity <= 0:
            return 0.0
        return frac * (1.0 - used / capacity)

    def maybe_ship(self, month):
        if (self.run_target is None or self.train_bank <= 0.0
                or self.train_bank < self.run_target):
            return None
        # recipe knowledge: the sector's best, reached early by labs whose
        # algorithmic efficiency runs ahead of the frontier track
        edge = max(0.0, math.log10(max(self.algo_mult, 1e-6))) * 6.0
        era_r = E.era_recipe(month + int(edge), K.RECIPE_ERA_TOKENS_PER_PARAM)
        era_moe = E.era_recipe(month + int(edge), K.RECIPE_ERA_MOE)
        r = min(self.doctrine.get("tokens_per_param", 20.0), era_r)
        moe = min(self.doctrine.get("moe_sparsity", 1.0), era_moe)
        shape = E.run_shape(self.train_bank, r, moe)
        tt = self.doctrine.get("test_time_oom", 0.0)
        cap = capability_index(self.train_bank, month, self.algo_mult,
                               self.rl_investment, tt)
        self.model = Model(f"{self.name}-{month}", cap, shape["active_params"], month)
        if not self.doctrine.get("always_eval", True):
            self.safety_debt += 2.0
        self.largest_run = max(self.largest_run, self.train_bank)
        self.train_bank = 0.0
        self.run_target = None
        return self.model

    # -------------------------------------------------------------- research
    def research_step(self, frac, months=1.0):
        """
        Algorithmic efficiency above or below the frontier track. Driven by
        researcher-years and by experiment FLOP, with sharply diminishing
        returns to either alone.
        """
        r_years = self.researchers * months / 12.0
        exp_flop = self.fleet.train_flops() * frac * K.SECONDS_PER_MONTH * months
        if exp_flop <= 0 or r_years <= 0:
            return
        # Cobb-Douglas in researcher-years and experiment FLOP. This is a
        # LAB-RELATIVE advantage: sector-wide progress already lives in
        # algo_efficiency(month). A lab can run ahead of the field, but the
        # advantage is bounded - you cannot privately out-research the entire
        # world by orders of magnitude - and it decays as others catch up.
        gain = 0.0016 * (r_years ** 0.35) * ((exp_flop / 1e21) ** 0.22)
        headroom = max(0.0, 1.0 - (self.algo_mult - 1.0) / (K.MAX_ALGO_ADVANTAGE - 1.0))
        self.algo_mult *= (1.0 + gain * headroom)
        self.algo_mult = min(self.algo_mult, K.MAX_ALGO_ADVANTAGE)

    def diffuse(self, frontier_algo, months=1.0):
        """
        Nobody stays ahead for free: papers, weights and people all leak.
        Followers are pulled up toward the best lab; the leader's private
        edge erodes as the techniques become common knowledge.
        """
        k = 1 - 0.5 ** (months / K.ALGO_DIFFUSION_HALFLIFE_M)
        if self.algo_mult < frontier_algo:
            self.algo_mult += (frontier_algo - self.algo_mult) * k
        else:
            self.algo_mult -= (self.algo_mult - 1.0) * k * K.LEADER_EDGE_DECAY

    # --------------------------------------------------------- power & price
    def deliver_power(self, month):
        keep = []
        for mw, arrival in self.mw_pipeline:
            if arrival <= month:
                self.contracted_mw += mw
            else:
                keep.append([mw, arrival])
        self.mw_pipeline = keep

    def contract_power(self, mw, month, lease_share=0.6):
        """
        Two ways to get megawatts. Leasing colocation is fast and you pay
        forever; building your own is slow, capital-heavy, and cheap to run.
        Most of the 2023-25 buildout was leased, which is why it happened at
        all - a 34-month greenfield queue cannot produce a 2024 cluster.
        """
        leased = mw * lease_share
        built = mw - leased
        self.leased_mw = getattr(self, "leased_mw", 0.0) + leased
        self.mw_pipeline.append([leased, month + K.LEASE_LEAD_MONTHS])
        lead = K.DC_LEAD_TIME_MONTHS
        if month >= A.month_index((2025, 6)):
            lead += K.GRID_QUEUE_MONTHS      # the interconnect queue arrives
        if built > 0:
            self.mw_pipeline.append([built, month + lead])
        return built * K.DC_CAPEX_PER_MW

    def headroom_accels(self, accel):
        used = self.fleet.megawatts() + sum(
            a.megawatts(c) for a, c, _m, _p in self.orders)
        free_mw = max(0.0, self.contracted_mw - used)
        per = accel.watts * K.PUE / 1e6
        return int(free_mw / per) if per > 0 else 0

    def serving_cost_per_mtok(self):
        if not self.model:
            return 1e9
        return E.cost_per_mtok(self.fleet.newest(), self.model.active_params)

    def set_price(self, close_rivals, month):
        """
        Cost-plus, with the markup competed away. In 2020 one lab sold the
        only frontier model there was and charged accordingly; by 2026 a
        dozen near-substitutes exist and the markup collapses toward the
        cost of the iron.
        """
        cost = self.serving_cost_per_mtok()
        markup = 1.25 + 11.0 / (1.0 + 2.2 * close_rivals)
        markup *= self.doctrine.get("price_stance", 1.0)
        self.price_per_mtok = max(cost * markup, cost * 0.4)

    # --------------------------------------------------------------- money
    def monthly_opex(self):
        staff = (self.researchers * K.RESEARCHER_COST_PER_YEAR
                 + self.engineers * K.ENGINEER_COST_PER_YEAR) / 12.0
        return staff + self.fleet.monthly_cost(0) * 0  # fleet billed separately


class World:
    def __init__(self, labs, benchmarks=None, seed=0):
        self.labs = labs
        self.month = 0
        self.bm = benchmarks or BenchmarkModel().fit()
        self.log = []

    # ---------------------------------------------------------- the market
    def frontier_capability(self):
        caps = [l.model.capability for l in self.labs if l.model]
        return max(caps) if caps else 22.0

    def step(self):
        m = self.month
        frontier_algo = max(l.algo_mult for l in self.labs)

        for lab in self.labs:
            lab.deliver(m)
            lab.deliver_power(m)
            lab.fleet.retire(m)
            d = lab.doctrine
            spare = lab.train_step(m, d["train"])
            # capacity the current run cannot absorb is turned to serving,
            # which is what a lab with idle accelerators actually does
            lab.serve_frac = d["serve"] + spare
            lab.research_step(d["experiment"])
            lab.diffuse(frontier_algo)
            if lab.maybe_ship(m) is not None:
                # post-training, evals, safety review and launch prep all
                # happen before the next pretraining run starts
                lab.cooldown = lab.doctrine.get("ship_cooldown", 3)
            if lab.run_target is None:
                if lab.cooldown > 0:
                    lab.cooldown -= 1
                else:
                    target = self._next_run_size(lab, m)
                    lab.run_target = target if target > 1e18 else None

        self._resolve_market(m)
        self._finance(m)
        self._procure(m)
        self.month += 1

    def _next_run_size(self, lab, m):
        """
        The largest run the fleet can finish in the doctrine's window - capped
        by what this lab has learned to land. Ambition is limited by the last
        run you actually finished, which is why nobody jumps two OOMs at once.
        """
        window = lab.doctrine.get("run_months", 4.0)
        by_fleet = (lab.fleet.train_flops() * lab.doctrine["train"]
                    * K.SECONDS_PER_MONTH * window / 1.18)
        ceiling = (lab.largest_run * K.MAX_RUN_GROWTH_PER_SHIP
                   if lab.largest_run > 0 else lab.doctrine.get("first_run_flop", 6e22))
        return min(by_fleet, ceiling)

    def _resolve_market(self, m):
        serving = [l for l in self.labs if l.model]
        if not serving:
            for l in self.labs:
                l.revenue_m = 0.0
            return
        fcap = self.frontier_capability()

        # sector demand: consumer seats and API tokens
        tam = E.consumer_tam(m)
        pot = E.adoption_potential(fcap) * tam
        avg_price = sum(l.price_per_mtok for l in serving) / len(serving)
        api_total = E.api_demand_mtok(m, avg_price, fcap)

        # price setting: count rivals within half an OOM of capability
        for l in serving:
            close = sum(1 for o in serving
                        if o is not l and abs(o.model.capability - l.model.capability) < 0.5)
            l.set_price(close, m)
        avg_price = sum(l.price_per_mtok for l in serving) / len(serving)
        api_total = E.api_demand_mtok(m, avg_price, fcap)

        # Budgets bind before capability does. Unconstrained demand is what
        # buyers would want; the ceiling is what they can pay for this year.
        year = 2020 + m // 12
        ceiling_month = K.SECTOR_SPEND_CEILING.get(year, 2.6e12) / 12.0
        wanted_spend = api_total * avg_price + pot * 20.0
        if wanted_spend > 0:
            realized = ceiling_month * (1.0 - math.exp(-wanted_spend / ceiling_month))
            throttle = realized / wanted_spend
            api_total *= throttle
            pot *= throttle

        # attractiveness: capability dominates, price matters, trust modulates
        # Attractiveness. Capability dominates, but its advantage SATURATES:
        # past roughly an order of magnitude of effective compute the extra
        # is not perceptible to most buyers, and switching costs, procurement
        # policy, data residency and second-source rules keep rivals alive.
        # Without this the model collapses to one lab, which is neither what
        # happens nor a game.
        scores = []
        for l in serving:
            gap = max(-K.CAPABILITY_PERCEPTION_OOM,
                      min(0.0, l.model.capability - fcap))
            s = (2.2 * gap
                 - 0.55 * math.log10(max(l.price_per_mtok, 0.01) / max(avg_price, 0.01))
                 + 0.9 * math.log10(max(l.trust, 5) / 50.0))
            scores.append(s)
        shares = E.logit_share(scores, temperature=0.85)
        # no buyer puts every workload with one vendor
        floor = K.MIN_VIABLE_SHARE
        shares = [max(sh, floor) for sh in shares]
        tot = sum(shares)
        shares = [sh / tot for sh in shares]

        for lab, share in zip(serving, shares):
            # consumer subscriptions, with diffusion inertia
            target = pot * share
            lab.subscribers += (target - lab.subscribers) * 0.055
            sub_rev = lab.subscribers * lab.sub_price

            # API tokens, capped by what the fleet can actually serve
            want = api_total * share
            cap_mtok = E.serving_capacity_mtok(
                lab.fleet, lab.model.active_params,
                getattr(lab, "serve_frac", lab.doctrine["serve"]))
            served = min(want, cap_mtok)
            lab.served_mtok = served
            lab.unmet = max(0.0, want - served)
            api_rev = served * lab.price_per_mtok

            lab.revenue_m = sub_rev + api_rev
            lab.share = share

    def _finance(self, m):
        for lab in self.labs:
            fleet_cost = lab.fleet.monthly_cost(m)
            staff = (lab.researchers * K.RESEARCHER_COST_PER_YEAR
                     + lab.engineers * K.ENGINEER_COST_PER_YEAR) / 12.0
            other = 0.25 * staff
            fleet_cost += getattr(lab, "leased_mw", 0.0) * K.LEASE_OPEX_PER_MW_MONTH
            net = lab.revenue_m - fleet_cost - staff - other
            lab.cash += net
            lab.last_net = net
            lab.last_costs = fleet_cost + staff + other
            lab.history.append({
                "month": m, "cash": lab.cash, "rev": lab.revenue_m,
                "net": net, "accels": lab.fleet.count(),
                "mw": lab.fleet.megawatts(),
                "cap": lab.model.capability if lab.model else 0.0,
                "price": lab.price_per_mtok,
                "subs": lab.subscribers,
                "algo": lab.algo_mult, "largest": lab.largest_run,
            })

    def _capital_market(self, m):
        """
        What investors will actually fund. Before a product existed, frontier
        labs were valued on the story and raised hundreds of millions. Once
        revenue was demonstrable they were valued on a revenue multiple that
        itself inflated with the sector's momentum.
        """
        fcap = self.frontier_capability()
        for lab in self.labs:
            lab.arr = lab.revenue_m * 12.0
            # story value: being at or near the frontier is worth something
            behind = max(0.0, fcap - (lab.model.capability if lab.model else 0))
            story = lab.doctrine.get("story_value", 2.0e9) * (10 ** (-0.55 * behind))
            multiple = 20.0 + 45.0 * min(1.0, m / 72.0)   # multiples expanded
            lab.valuation = max(story, lab.arr * multiple)
            if lab.doctrine.get("backer_funded"):
                continue

    def _procure(self, m):
        """Buy iron, subject to capital, power, and the industry's fab output."""
        year = 2020 + m // 12
        supply = K.FAB_OUTPUT_PER_MONTH.get(year, 3_800_000)
        accel = E.best_available(m)
        self._capital_market(m)
        for lab in self.labs:
            # ---- a corporate parent funds from operating cash flow, not rounds
            parent = lab.doctrine.get("parent_cashflow_2020", 0.0)
            if parent:
                growth = lab.doctrine.get("parent_growth", 1.55) ** (m / 12.0)
                lab.cash += parent * growth / 12.0

            # ---- raise, if the market will have you
            runway = lab.cash / max(lab.last_costs, 1.0)
            if (runway < 14 and lab.doctrine.get("can_raise", True)
                    and m - getattr(lab, "last_raise", -99) >= 11):
                dilution = lab.doctrine.get("raise_fraction", 0.16)
                amount = lab.valuation * dilution
                lab.cash += amount
                lab.last_raise = m
                lab.raised = getattr(lab, "raised", 0.0) + amount

            # ---- infrastructure finance: from 2024 datacenters were funded
            # against contracted revenue through SPVs and vendor credit, not
            # out of equity. This is what unlocked the gigawatt era.
            if m >= A.month_index((2024, 6)) and lab.arr > 5e8:
                capacity = lab.arr * lab.doctrine.get("debt_multiple", 3.0)
                drawn = getattr(lab, "debt_drawn", 0.0)
                headroom = max(0.0, capacity - drawn)
                if headroom > 0 and runway < 30:
                    draw = headroom * 0.30
                    lab.cash += draw
                    lab.debt_drawn = drawn + draw

            # ---- contract power ahead of need
            planned = lab.fleet.megawatts() + sum(
                a.megawatts(c) for a, c, _m, _p in lab.orders)
            pipeline = sum(mw for mw, _a in lab.mw_pipeline)
            target = max(planned, 5.0) * lab.doctrine.get("power_lookahead", 5.0)
            lease_market = K.LEASE_MARKET_MW.get(year, 52_000)
            lease_cap = lease_market * lab.doctrine.get("supply_share", 0.2)
            if lab.contracted_mw + pipeline < target:
                need = min(target - lab.contracted_mw - pipeline, lease_cap)
                share = lab.doctrine.get("lease_share", 0.6)
                cost = need * (1 - share) * K.DC_CAPEX_PER_MW
                if cost < lab.cash * 0.45:
                    lab.cash -= cost
                    lab.contract_power(need, m, share)
                    lab.capex_by_year[year] = lab.capex_by_year.get(year, 0.0) + cost

            # ---- buy accelerators
            budget = max(0.0, lab.cash * lab.doctrine.get("capex_aggression", 0.5))
            count = int(budget / accel.capex)
            count = min(count, int(supply * lab.doctrine.get("supply_share", 0.2)))
            count = min(count, lab.headroom_accels(accel))
            if count > 0:
                bought = lab.order(accel, count, m, lead_months=5)
                lab.capex_by_year[year] = (lab.capex_by_year.get(year, 0.0)
                                           + bought * accel.capex)
