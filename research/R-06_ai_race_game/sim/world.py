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
from . import domains as D
from . import talent as T
from . import release as REL
from . import strategy as STRAT
from . import intel as INTEL
from . import safety as SAFE
from . import tasks as TASKS
from . import policy as POL
from .capability import (BenchmarkModel, FrontierHistory, algo_efficiency, reasoning_multiplier,
                         capability_index, domain_capability)


class Model:
    """A shipped model: what it can do, in each domain, and what it costs."""

    def __init__(self, name, capability, active_params, month, caps=None,
                 tag="", generation=0):
        self.name = name
        self.capability = capability          # headline, for reporting only
        self.caps = caps or {}                # the real answer: per domain
        self.active_params = active_params
        self.shipped = month
        self.tag = tag                        # 'breakthrough' / 'dud' / ''
        self.generation = generation          # post-training releases so far
        # Benchmarks are run, not computed. Sampling and harness noise is
        # drawn once per shipped model, so a lab's published numbers hold
        # still between releases and jump when it ships.
        self.eval_noise = {}

    def can_serve(self, segment):
        return all(self.caps.get(d, 0.0) >= th
                   for d, th in D.SEGMENTS[segment]["gates"].items())

    def quality_for(self, segment, caps=None):
        c = caps if caps is not None else self.caps
        return sum(w * c.get(d, 0.0)
                   for d, w in D.SEGMENTS[segment]["weight_domains"].items())


class Lab:
    def __init__(self, name, doctrine, cash, researchers, fleet_accel,
                 fleet_count, start_month=0, policy=None):
        self.name = name
        # What the lab IS: strategy, quality, parent, paranoia. The world
        # reads identity from here. Anything the lab CHOOSES comes through
        # `self.actions`, set each month by `self.policy` (sim/policy.py).
        self.doctrine = doctrine
        self.policy = policy or POL.DoctrinePolicy(doctrine)
        self.actions = None               # in force this month; set by World.apply
        self.cash = cash
        self.researchers = researchers
        self.engineers = researchers * 2
        self.researcher_quality = doctrine.get("researcher_quality", 1.0)
        self.stars = doctrine.get("stars", 0)
        self.comp_offer = K.RESEARCHER_COST_PER_YEAR * doctrine.get("comp_stance", 1.0)
        self.mission_alignment = doctrine.get("mission", 50.0)
        self.fleet = E.Fleet()
        self.fleet.add(fleet_accel, fleet_count, start_month)
        self.orders = []                  # [accel, count, arrival_month, paid]
        self.algo_mult = 1.0              # lab-specific, vs the frontier track
        self.rl_investment = 1.0
        self.train_bank = 0.0             # FLOP accumulated in the current run
        self.largest_run = 0.0            # engineering experience, in FLOP
        self.cooldown = 0                 # months between finishing and starting
        self.shelved = 0                  # runs completed but not worth shipping
        self.post_gen = 0                 # post-training releases on this base
        self.post_timer = 0
        self.ships = []                   # (month, kind, tag, capability)
        self.internal = None              # built, better, deliberately unreleased
        self.elicitation = doctrine.get("elicitation", 0.42)
        self.chase = {}                   # per-domain measured-score padding
        self.scale_at_release = fleet_count  # fleet size when last shipped
        self.ambition = 1.0               # this run vs the last one landed
        self.run_window = 4.0
        self.beliefs = []                 # what this lab believes about rivals
        self.threat = 0.0                 # perceived deficit, in OOM
        self.feared = None                # who it thinks is ahead
        self.caught = 0                   # contamination scandals
        self.incidents = []               # what has gone wrong here
        self.evaluated_at = 0.0           # capability as of the last real eval
        self.legal_exposure = 0.0
        self.deploy_restricted_until = -1
        self.withheld_months = 0
        self.rng = None                   # seeded by the World
        self.run_target = None
        self.run_plan = None              # the RunPlan behind run_target
        self.model = None
        self.price_per_mtok = 40.0
        self.sub_price = 20.0
        self.subscribers = 0
        self.contracted_mw = fleet_accel.megawatts(fleet_count) * 1.4
        self.mw_pipeline = []             # [mw, arrival_month]
        self.capex_by_year = {}
        self.arr = 0.0                    # annualized revenue run-rate
        self.valuation = 1.0e9
        self.data = D.DataStock()
        self.mixture = dict(doctrine.get("mixture", {"LANG": 1.0}))
        self.seg_revenue = {}
        self.safety_debt = 0.0
        self.trust = 50.0
        self.revenue_m = 0.0
        self.history = []
        self.ledger = {}                  # month -> {category: dollars}; + in, - out
        self.notices = []                 # (month, text): why a manual order was clipped

    def book(self, month, key, amount):
        """Every dollar that moves, by category. Positive in, negative out."""
        if amount:
            row = self.ledger.setdefault(month, {})
            row[key] = row.get(key, 0.0) + amount

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

    def maybe_ship(self, month, frontier_cap, world):
        """
        Finish a run, see how it went, and decide whether it is worth
        shipping. A run that lands below what the lab already sells is
        shelved - the compute is spent, the lesson is kept, and the trajectory
        goes flat rather than down.
        """
        if (self.run_target is None or self.train_bank <= 0.0
                or self.train_bank < self.run_target):
            return None

        # recipe knowledge: the sector's best, reached early by labs whose
        # algorithmic efficiency runs ahead of the frontier track
        edge = max(0.0, math.log10(max(self.algo_mult, 1e-6))) * 6.0
        era_r = E.era_recipe(month + int(edge), K.RECIPE_ERA_TOKENS_PER_PARAM)
        era_moe = E.era_recipe(month + int(edge), K.RECIPE_ERA_MOE)
        plan = self.run_plan
        r = min(plan.tokens_per_param, era_r)
        moe = min(plan.moe_sparsity, era_moe)
        shape = E.run_shape(self.train_bank, r, moe)
        tt = plan.test_time_oom
        mixture = plan.mixture

        own = max(self.model.caps.values()) if self.model and self.model.caps else 0.0
        # frontier_cap is this lab's BELIEF about the frontier. A lab that
        # over-estimates a rival takes bigger swings than it needed to.
        behind = max(0.0, frontier_cap - own) if own > 0 else 0.0
        behind *= (1.0 + K.SPIRAL * K.THREAT_RISK_GAIN)

        mult, tag = REL.outcome_multiplier(
            self.rng, self.researcher_quality, self.stars, behind,
            ambition=getattr(self, "ambition", 1.0))

        cap = capability_index(self.train_bank * mult, month, self.algo_mult,
                               self.rl_investment, tt,
                               sector_algo=world.algo_frontier)
        caps = domain_capability(10 ** cap, mixture, shape["tokens"],
                                 self.data, D.DOMAIN_KEYS)
        # the same arithmetic, itemised, kept with the model for the record
        from . import explain as EXPL
        why = EXPL.explain(self, world, month, self.train_bank, plan.tokens_per_param,
                           plan.moe_sparsity, tt, mixture, mult=mult, tag=tag)

        # every completed run teaches you to land a bigger one, shipped or not
        self.largest_run = max(self.largest_run, self.train_bank)
        self.train_bank = 0.0
        self.run_target = None
        self.run_plan = None

        current = self.model.caps if self.model else None
        if not REL.should_ship(caps, current, behind):
            # shelved. The lesson is real even when the model is not.
            self.shelved += 1
            self.algo_mult *= (1.0 + 0.004 * K.SHELVE_LEARNING)
            self.last_outcome = ("shelved", tag, cap)
            return None

        candidate = Model(f"{self.name}-{month}", cap, shape["active_params"],
                          month, caps, tag)
        candidate.why = why
        candidate.eval_noise = {k: self.rng_eval.gauss(0.0, TASKS.EVAL_NOISE_PTS)
                                for k in TASKS.SUITES}
        # The interrupt: the run has landed and the lab is asked, with the
        # result in hand, whether to release it and whether to evaluate it
        # first. Logged like any action.
        rel = world.ask_release(self, candidate, held=False)
        if not rel.ship:
            # better than what it sells, and deliberately not released
            self.internal = candidate
            self.withheld_months += 1
            self.hoarding = True
            self.last_outcome = ("withheld", tag, cap)
            return None

        self.model = candidate
        self.internal = None
        self.post_gen = 0
        self.post_budget = REL.post_train_budget(self.rng, self.researcher_quality)
        self.post_timer = K.POST_TRAIN_MONTHS + self.rng.randint(0, 2)
        self.ships.append((month, "pretrain", tag, round(max(caps.values()), 3)))
        self.scale_at_release = self.fleet.count()
        self.last_outcome = ("shipped", tag, cap)
        self._launch_eval(rel, cap)
        return self.model

    def _launch_eval(self, rel, cap):
        """A real evaluation covers most of the jump you just shipped. Skipping
        it is cheaper now and is carried as safety debt."""
        if rel.evaluate:
            self.evaluated_at = (self.evaluated_at
                                 + K.EVAL_CAPABILITY_COVERAGE
                                 * (cap - self.evaluated_at))
        else:
            self.safety_debt += 2.0

    def maybe_release_held(self, month, world):
        """
        A lab sitting on an unreleased model releases it the moment the
        reason for sitting on it stops holding - usually when the money runs
        short. Years of quiet, then a release that resets the board.
        """
        if self.internal is None:
            return None
        cap = self.internal.capability
        rel = world.ask_release(self, self.internal, held=True)
        if not rel.ship:
            self.withheld_months += 1
            self.hoarding = True
            # You are visibly not shipping, and the market notices. The
            # customers you are not defending drift, and the story you cannot
            # demonstrate is worth less.
            self.trust = max(5.0, self.trust - K.WITHHOLD_TRUST_DECAY)
            return None
        self.hoarding = False
        self.model = self.internal
        self.internal = None
        self.post_gen = 0
        self.post_budget = REL.post_train_budget(self.rng, self.researcher_quality)
        self.post_timer = K.POST_TRAIN_MONTHS
        self.ships.append((month, "pretrain", "held",
                           round(max(self.model.caps.values()), 3)))
        self._launch_eval(rel, cap)
        return self.model

    # Post-training lifts these domains far more than the others: RL on
    # verifiable rewards works where answers can be checked.
    POST_TRAIN_WEIGHT = {"REASON": 1.00, "CODE": 0.95, "AGENT": 0.90,
                         "LANG": 0.60, "ROBOT": 0.50, "AUDIO": 0.30,
                         "IMAGE": 0.25, "VIDEO": 0.20}

    def maybe_post_train(self, month):
        """
        The x.5 release. Between pretraining runs a lab can improve what it
        already ships two or three times, with sharply diminishing returns.
        This is what gives a release history its real shape: a big jump, a
        couple of small ones, then a big jump.
        """
        if not self.model or self.post_gen >= getattr(self, "post_budget", 0):
            return None
        self.post_timer -= 1
        if self.post_timer > 0:
            return None
        gain = REL.post_train_gain(self.post_gen)
        if gain <= 0:
            return None
        for dom, c in list(self.model.caps.items()):
            if c > 0:
                self.model.caps[dom] = c + gain * self.POST_TRAIN_WEIGHT.get(dom, 0.5)
        self.model.capability = max(self.model.caps.values())
        self.post_gen += 1
        self.model.generation = self.post_gen
        self.post_timer = K.POST_TRAIN_MONTHS + self.rng.randint(0, 3)
        self.ships.append((month, "post", "", round(self.model.capability, 3)))
        return self.model

    # -------------------------------------------------------------- research
    def research_step(self, frac, months=1.0):
        """
        Algorithmic efficiency above or below the frontier track. Driven by
        researcher-years and by experiment FLOP, with sharply diminishing
        returns to either alone.
        """
        exp_flop = self.fleet.train_flops() * frac * K.SECONDS_PER_MONTH * months
        if exp_flop <= 0 or self.researchers <= 0:
            return
        # Cobb-Douglas in researcher-years and experiment FLOP. This is a
        # LAB-RELATIVE advantage: sector-wide progress already lives in
        # algo_efficiency(month). A lab can run ahead of the field, but the
        # advantage is bounded - you cannot privately out-research the entire
        # world by orders of magnitude - and it decays as others catch up.
        gain = T.research_output(self, self._month, exp_flop, months)
        self.last_research = gain
        headroom = max(0.0, 1.0 - (self.algo_mult - 1.0) / (K.MAX_ALGO_ADVANTAGE - 1.0))
        self.algo_mult *= (1.0 + gain * headroom)
        self.algo_mult = min(self.algo_mult, K.MAX_ALGO_ADVANTAGE)

    def diffuse(self, frontier_algo, months=1.0, openness=0.35, distill=0.0):
        """
        Nobody stays ahead for free: papers, weights and people all leak.
        Followers are pulled up toward the best lab; the leader's private
        edge erodes as the techniques become common knowledge.
        """
        # an open field diffuses fast; a field of closed labs barely diffuses
        halflife = K.ALGO_DIFFUSION_HALFLIFE_M / max(0.25, 0.45 + 1.3 * openness)
        rate = months / halflife
        if self.algo_mult < frontier_algo:
            # every token the labs ahead of you serve is a token you can
            # study, distill from, or turn into synthetic training data
            rate *= self.doctrine.get("follow_bonus", 1.0) * (1.0 + distill)
        k = 1 - 0.5 ** rate
        if self.algo_mult < frontier_algo:
            self.algo_mult += (frontier_algo - self.algo_mult) * k
        else:
            # A leader's private edge erodes because the techniques become
            # common knowledge - which happens fast in an open field and
            # slowly in a closed one. This is the other half of what a
            # hoarding strategy is buying.
            decay = K.LEADER_EDGE_DECAY * (0.35 + 1.15 * openness)
            self.algo_mult -= (self.algo_mult - 1.0) * k * decay

    def perceived_caps(self):
        """
        What the outside world believes this model can do: the true frontier
        plus whatever suite-specific optimisation has been bought. The market
        prices this. The research loop does not.
        """
        if not self.model:
            return {}
        return {d: c + self.chase.get(d, 0.0)
                for d, c in self.model.caps.items()}

    def chase_step(self, month):
        """Pursue the published numbers, and occasionally get caught at it."""
        rate = self.actions.chase_rate
        for d in list(self.model.caps) if self.model else []:
            cur = self.chase.get(d, 0.0)
            target = K.CHASE_MAX_OOM * rate
            cur += (K.CHASE_RATE * rate if cur < target else -K.CHASE_DECAY)
            self.chase[d] = max(0.0, min(K.CHASE_MAX_OOM, cur))
        total = sum(self.chase.values())
        if total > 0 and self.rng.random() < K.CONTAMINATION_BASE * total:
            self.trust = max(5.0, self.trust - K.CONTAMINATION_TRUST)
            for d in self.chase:
                self.chase[d] *= (1.0 - K.CONTAMINATION_SETBACK)
            self.caught += 1
            return True
        return False

    # ----------------------------------------------------------------- data
    # Which corpora to want, and what to pay, is a decision: it lives in the
    # policy (`Actions.data_buy`, `Actions.data_bids`). The world only does
    # the acquiring.
    def take_data(self, source_key, month, price):
        """An exclusive licence, won at auction for `price`."""
        res = D.acquire(self.data, source_key, month, self.actions.data_share)
        if res is None:
            return
        _dollars, flop = res
        self.cash -= price
        self.book(month, "data_licences", -price)
        self.data_flop_debt = getattr(self, "data_flop_debt", 0.0) + flop
        src = D.DATA_SOURCES[source_key]
        self.annual_data_cost = (getattr(self, "annual_data_cost", 0.0)
                                 + src["annual_cost"])

    def buy_data(self, month):
        """The non-exclusive source the policy chose this month, if any."""
        key = self.actions.data_buy
        if key is None or key in self.data.sources:
            return
        src = D.DATA_SOURCES[key]
        if src["exclusive"]:
            return
        res = D.acquire(self.data, key, month, self.actions.data_share)
        if res is None:
            return
        dollars, flop = res
        self.cash -= dollars
        self.book(month, "data_licences", -dollars)
        self.data_flop_debt = getattr(self, "data_flop_debt", 0.0) + flop
        self.annual_data_cost = (getattr(self, "annual_data_cost", 0.0)
                                 + src["annual_cost"])

    def accrue_telemetry(self, month):
        """
        Usage becomes training data, in the domains your customers actually
        use. Nobody can buy this, which is why an incumbent's lead compounds
        in exactly the segments it already leads.
        """
        total = sum(self.seg_revenue.values())
        if total <= 0:
            return
        served = getattr(self, "served_mtok", 0.0)
        tokens = served * D.TELEMETRY_TOKENS_PER_MTOK_SERVED
        if tokens <= 0:
            return
        for seg, rev in self.seg_revenue.items():
            if rev <= 0:
                continue
            frac = rev / total
            for dom, w in D.SEGMENTS[seg]["weight_domains"].items():
                self.data.add(dom, tokens * frac * w, D.TELEMETRY_QUALITY)

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
        # Price stance compresses the MARGIN, not the price through the floor.
        # An efficiency strategy wins by having a lower cost and passing it
        # on, which is a low absolute price and a positive margin - not by
        # selling below what the iron costs it.
        stance = self.actions.price_stance
        markup = 1.0 + (markup - 1.0) * stance
        # Deliberately selling below cost is a separate, explicit choice.
        markup *= self.actions.loss_leader
        self.price_per_mtok = max(cost * markup, cost * 0.35)

    # --------------------------------------------------------------- money
    def monthly_opex(self):
        staff = (self.researchers * K.RESEARCHER_COST_PER_YEAR
                 + self.engineers * K.ENGINEER_COST_PER_YEAR) / 12.0
        return staff + self.fleet.monthly_cost(0) * 0  # fleet billed separately


class World:
    def __init__(self, labs, benchmarks=None, seed=0):
        import random
        self.seed = seed
        self.rng = random.Random(seed)
        self.labs = labs
        for i, lab in enumerate(labs):
            lab.rng = random.Random(seed * 1009 + i * 7919 + 13)
            # Evaluation noise draws from its own stream. Sharing lab.rng
            # would mean that adding or removing a benchmark reshuffles every
            # training-run outcome in the game, which makes calibration
            # incomparable across changes for no reason.
            lab.rng_eval = random.Random(seed * 6421 + i * 104729 + 7)
            lab.rng_intel = random.Random(seed * 3571 + i * 15485863 + 31)
            lab.rng_safety = random.Random(seed * 8191 + i * 2750159 + 53)
            # A policy that wants randomness draws from its own stream, so
            # the world's realisation never depends on how a policy decided
            # (a human draws nothing; a replay draws nothing; the run is
            # the same run).
            lab.rng_policy = random.Random(seed * 4093 + i * 3145739 + 71)
        self.month = 0
        # The sector's algorithmic frontier, as a stock that labs advance.
        self.algo_frontier = 1.0
        self.regulation = 0.0             # sector-wide, rises with severe incidents
        self.incident_log = []
        self.sector_research = 0.0
        self.bm = benchmarks or BenchmarkModel().fit()
        self.suites = TASKS.SuiteSet(TASKS.fit_anchored(FrontierHistory()))
        self.log = []
        self.openness = 0.0
        self.market_comp = T.market_comp(
            0, sum(l.researchers for l in labs) * 1.25, T.global_researcher_pool(0))
        self.scores = {}
        self.segment_state = {}
        self.claimed_exclusives = set()
        # Every decision every lab made, as (month, lab, what changed). With
        # the seed this is the whole game: a run can be saved, resumed and
        # replayed from it, and a strategy can be run against a recorded game.
        self.action_log = []
        # Before the first tick a lab still needs standing orders: the intel
        # step reads `intel_spend` before anything has been decided. Ask each
        # policy once, at month -1, with an empty view of the world.
        self.month = -1
        for lab in self.labs:
            lab._month = -1
            self.apply(lab, lab.policy.decide(self.observe(lab)))
        self.month = 0

    # ---------------------------------------------------- the decision seam
    def observe(self, lab):
        """
        What `lab` can see this month. Own state in full; rivals only as the
        beliefs `_observe` formed; the market only as it was published.
        """
        return POL.Observation(
            month=self.month, lab=lab,
            beliefs=lab.beliefs, threat=lab.threat, feared=lab.feared,
            perceived_frontier=getattr(lab, "perceived_frontier", 0.0),
            regulation=self.regulation, openness=self.openness,
            market_comp=self.market_comp, scores=self.scores,
            segment_state=self.segment_state,
            sector_incidents=self.incident_log, rng=lab.rng_policy)

    def apply(self, lab, actions):
        """Validate, log what changed, and put the actions in force."""
        POL.validate(actions)
        changed = actions.diff(lab.actions)
        if changed:
            self.action_log.append((self.month, lab.name, changed))
        lab.actions = actions
        lab.mixture = dict(actions.mixture)

    def ask_release(self, lab, candidate, held):
        """The release interrupt: ship or sit on it, evaluated or not.
        `candidate` is the Model in question. Logged either way."""
        rel = lab.policy.decide_release(self.observe(lab), candidate, held)
        if not isinstance(rel, POL.Release):
            raise POL.IllegalAction(f"decide_release must return a Release, got {rel!r}")
        self.action_log.append((self.month, lab.name,
                                {"release": "ship" if rel.ship else "hold",
                                 "evaluate": rel.evaluate if rel.ship else None,
                                 "held": held, "cap": round(candidate.capability, 3)}))
        return rel

    def ask_run(self, lab, proposal):
        """The run interrupt: the cooldown is over; what is the next run?"""
        plan = lab.policy.decide_run(self.observe(lab), proposal)
        POL.validate_plan(plan)
        self.action_log.append((self.month, lab.name, {"run": plan.to_dict()}))
        return plan

    def _decide(self, m):
        """observe -> decide -> apply, for every lab, once a month."""
        # the going rate for people is public; every lab prices against it
        supply = T.global_researcher_pool(m)
        demand = sum(l.researchers for l in self.labs)
        self.market_comp = T.market_comp(m, demand * 1.25, supply)
        for lab in self.labs:
            self.apply(lab, lab.policy.decide(self.observe(lab)))

    # ---------------------------------------------------------- the market
    def frontier_capability(self):
        caps = [l.model.capability for l in self.labs if l.model]
        return max(caps) if caps else 22.0

    def step(self):
        m = self.month
        for lab in self.labs:
            lab._month = m
        self._observe(m)
        self._decide(m)
        frontier_algo = max(l.algo_mult for l in self.labs)
        # How freely ideas move this month. Open-weights labs lift it for
        # everyone; a field of secretive labs grinds diffusion down, which is
        # exactly what a hoarding strategy is buying.
        wts = [(1.0 + max(0.0, (l.model.capability - 22.0)) if l.model else 1.0)
               for l in self.labs]
        self.openness = (sum(l.actions.openness * w
                             for l, w in zip(self.labs, wts)) / max(sum(wts), 1e-9))
        self._talent_market(m)
        # Distillation pressure per lab: how much the labs AHEAD of it are
        # serving. A leader that sells a lot of tokens is teaching the field.
        ahead = {}
        for lab in self.labs:
            vol = sum(getattr(o, "served_mtok", 0.0) for o in self.labs
                      if o is not lab and o.algo_mult > lab.algo_mult)
            ahead[lab.name] = K.DISTILL_COEF * math.log10(
                1.0 + vol / K.DISTILL_REF_MTOK)
        self.distill = ahead

        for lab in self.labs:
            lab.deliver(m)
            lab.deliver_power(m)
            lab.fleet.retire(m)
            lab.buy_data(m)
        self._data_auction(m)

        for lab in self.labs:
            a = lab.actions
            # a run in progress can be grown, or landed on what it has
            if lab.run_target is not None:
                if a.extend_run_months > 0:
                    lab.run_target += (lab.fleet.train_flops() * a.train
                                       * K.SECONDS_PER_MONTH * a.extend_run_months / 1.18)
                if a.finish_run and lab.train_bank > 0:
                    lab.run_target = lab.train_bank
            spare = lab.train_step(m, a.train)
            # capacity the current run cannot absorb is turned to serving,
            # which is what a lab with idle accelerators actually does
            lab.serve_frac = a.serve + spare
            lab.research_step(a.experiment)
            lab.diffuse(frontier_algo, openness=self.openness,
                        distill=self.distill.get(lab.name, 0.0))
            fc = self.frontier_capability()
            lab.maybe_release_held(m, self)
            if lab.maybe_ship(m, fc, self) is not None:
                # the cooldown is where post-training, evals, safety review
                # and launch prep happen - it is not idle time. The policy
                # chose the length; the world adds its own jitter.
                jitter = lab.rng.randint(-1, K.SHIP_JITTER_MONTHS)
                lab.cooldown = max(1, int(round(lab.actions.ship_cooldown + jitter)))
            lab.maybe_post_train(m)
            if lab.run_target is None:
                if lab.cooldown > 0:
                    lab.cooldown -= 1
                else:
                    target = self._next_run_size(lab, m)
                    if target > 1e18:
                        plan = self.ask_run(lab, POL.RunPlan(
                            target, a.tokens_per_param, a.moe_sparsity,
                            a.test_time_oom, lab.mixture))
                        if plan.target_flop > 1e18:
                            lab.run_target = plan.target_flop
                            lab.run_plan = plan
                            if lab.largest_run > 0:
                                lab.ambition = plan.target_flop / lab.largest_run

        # The frontier moves because labs did research this month. Automated
        # research feeds straight into this, which is how the loop closes and
        # why the late-decade curve bends instead of continuing straight.
        self.sector_research = sum(getattr(l, "last_research", 0.0)
                                   for l in self.labs)
        growth = (K.SECTOR_ALGO_SCALE
                  * (max(self.sector_research, 1e-9) ** K.SECTOR_ALGO_ALPHA)
                  / (self.algo_frontier ** K.IDEA_DIFFICULTY))
        self.algo_frontier *= (1.0 + growth)
        self.algo_growth = growth

        # algo_mult is a RELATIVE advantage over the field, not an absolute
        # rate - sector-wide progress already lives in algo_efficiency(month).
        # Renormalising each month keeps it meaning "ahead of the others",
        # so a lab cannot bank a permanent private multiplier and neither can
        # everyone simultaneously max it out.
        mean_algo = sum(l.algo_mult for l in self.labs) / len(self.labs)
        if mean_algo > 0:
            for lab in self.labs:
                lab.algo_mult = min(K.MAX_ALGO_ADVANTAGE,
                                    max(0.25, lab.algo_mult / mean_algo))

        for lab in self.labs:
            if lab.model:
                lab.chase_step(m)
        self._safety(m)
        self._score_suites(m)
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
        # Wall-clock the lab is willing to spend - the policy's call, and
        # where competitive fear shows up as a shorter window.
        window = lab.actions.run_months
        lab.run_window = window
        by_fleet = (lab.fleet.train_flops() * lab.actions.train
                    * K.FRONTIER_RUN_SHARE
                    * K.SECONDS_PER_MONTH * window / 1.18)
        if lab.largest_run <= 0:
            return min(by_fleet, lab.doctrine.get("first_run_flop", 6e22))
        # Compute is the constraint. Reaching far past what you have landed
        # before is allowed, and dangerous - priced in outcome_multiplier.
        lab.ambition = by_fleet / lab.largest_run
        return by_fleet

    def _resolve_market(self, m):
        """
        Markets are segmented and each segment is gated on a domain. A lab
        that cannot clear a segment's gate does not compete there at all - it
        has no product - and a lab that leads one segment keeps it even if a
        rival is a full order of magnitude ahead somewhere else.
        """
        serving = [l for l in self.labs if l.model]
        for l in self.labs:
            l.revenue_m = 0.0
            l.seg_revenue = {}
        if not serving:
            return

        for l in serving:
            close = sum(1 for o in serving
                        if o is not l and abs(o.model.capability - l.model.capability) < 0.5)
            l.set_price(close, m)
        avg_price = sum(l.price_per_mtok for l in serving) / len(serving)

        if not hasattr(self, "_prev_share"):
            self._prev_share = {}
        demand_dollars = {l: 0.0 for l in serving}
        self.segment_state = {}
        sector_month = self._sector_spend(m)

        for seg_key, seg in D.SEGMENTS.items():
            # Regulation raises the bar on products that act in the world,
            # and a lab that caused a severe incident is barred from them.
            agentic = seg_key in ("enterprise_agents", "robotics", "coding")
            lift = (K.REGULATION_GATE_LIFT * self.regulation) if agentic else 0.0
            eligible = [l for l in serving
                        if all(l.perceived_caps().get(dd, 0.0) >= th + lift
                               for dd, th in D.SEGMENTS[seg_key]["gates"].items())
                        and not (agentic and m < getattr(l, "deploy_restricted_until", -1))]
            if not eligible:
                self.segment_state[seg_key] = (0.0, [])
                continue
            # buyers price the published numbers, not the private truth
            qual = {l: l.model.quality_for(seg_key, l.perceived_caps())
                    for l in eligible}
            best = max(qual.values())

            # a segment barely past its gate captures only part of its budget;
            # buyers pay for capability they can actually use
            gate = max(seg["gates"].values())
            fill = 1.0 / (1.0 + math.exp(-(best - gate) / 0.75))
            tam = D.segment_tam(seg_key, sector_month) * fill

            scores = []
            for l in eligible:
                gap = max(-K.CAPABILITY_PERCEPTION_OOM, min(0.0, qual[l] - best))
                # Price sensitivity is the mirror of differentiation: where
                # buyers cannot tell two models apart they buy the cheaper
                # one, and where taste matters they largely do not. Without
                # this an efficiency strategy is strictly dominated, which is
                # both wrong and boring.
                diff = seg.get("differentiation", 0.0)
                scores.append(
                    2.2 * (1.0 - diff) * gap
                    - (0.35 + 1.55 * (1.0 - diff))
                      * math.log10(max(l.price_per_mtok, 0.01) / max(avg_price, 0.01))
                    + 0.9 * seg["brand_weight"] * math.log10(max(l.trust, 5) / 50.0)
                    # open weights buy developer mindshare rather than revenue:
                    # people build on what they can run themselves
                    + (0.85 * l.actions.openness
                       if seg_key in ("api_general", "coding") else 0.0))
            shares = E.logit_share(scores, temperature=seg["temperature"])
            shares = [max(sh, K.MIN_VIABLE_SHARE) for sh in shares]
            tot = sum(shares)
            shares = [sh / tot for sh in shares]

            # Some markets re-decide every month and some do not. A consumer
            # default is a habit; an enterprise deployment is a contract and
            # a migration. Stickiness is why a land grab is a strategy at all.
            stick = seg.get("stickiness", 0.0)
            if stick > 0:
                prev = self._prev_share.setdefault(seg_key, {})
                blended = []
                for l, sh in zip(eligible, shares):
                    # A lab sitting on a better model than it sells forfeits
                    # some of the incumbency it is not defending: people
                    # notice who has the best thing you can actually use.
                    k = stick
                    if getattr(l, "hoarding", False):
                        k *= (1.0 - K.WITHHOLD_STICKINESS_LOSS)
                    blended.append(prev.get(l.name, sh) * k + sh * (1.0 - k))
                shares = blended
                tot2 = sum(shares) or 1.0
                shares = [sh / tot2 for sh in shares]
                for l, sh in zip(eligible, shares):
                    prev[l.name] = sh

            for l, sh in zip(eligible, shares):
                demand_dollars[l] += tam * sh
                l.seg_revenue[seg_key] = tam * sh
            self.segment_state[seg_key] = (tam, [(l.name, sh) for l, sh in
                                                 zip(eligible, shares)])

        # ---- can you actually serve what you sold?
        for lab in serving:
            want_dollars = demand_dollars[lab]
            price = max(lab.price_per_mtok, 0.01)
            # consumer subscriptions are flat-rate, so those customers consume
            # far more tokens per dollar than an API buyer does. This is where
            # a loss-making consumer business comes from.
            consumer_frac = (lab.seg_revenue.get("consumer_chat", 0.0)
                             / want_dollars if want_dollars > 0 else 0.0)
            usage_mult = 1.0 + consumer_frac * (K.CONSUMER_USAGE_MULT - 1.0)
            want_mtok = want_dollars / price * usage_mult

            cap_mtok = E.serving_capacity_mtok(
                lab.fleet, lab.model.active_params,
                getattr(lab, "serve_frac", lab.actions.serve))
            served = min(want_mtok, cap_mtok)
            lab.served_mtok = served
            lab.unmet = max(0.0, want_mtok - served)
            fulfilled = served / want_mtok if want_mtok > 0 else 0.0
            lab.revenue_m = want_dollars * fulfilled
            lab.seg_revenue = {k: v * fulfilled for k, v in lab.seg_revenue.items()}
            lab.share = (lab.revenue_m
                         / max(sum(demand_dollars.values()), 1.0))
            lab.accrue_telemetry(m)

    def _finance(self, m):
        for lab in self.labs:
            fleet_cost = lab.fleet.monthly_cost(m)
            staff = (lab.researchers * lab.comp_offer
                     + lab.engineers * K.ENGINEER_COST_PER_YEAR) / 12.0
            other = 0.25 * staff
            lease = getattr(lab, "leased_mw", 0.0) * K.LEASE_OPEX_PER_MW_MONTH
            fleet_cost += lease
            data_annual = getattr(lab, "annual_data_cost", 0.0) / 12.0
            compliance = (lab.revenue_m * K.REGULATION_COMPLIANCE_COST
                          * self.regulation)
            other += data_annual + compliance
            net = lab.revenue_m - fleet_cost - staff - other
            lab.cash += net
            for seg, rev in lab.seg_revenue.items():
                lab.book(m, "revenue:" + seg, rev)
            lab.book(m, "staff", -staff)
            lab.book(m, "overhead", -0.25 * staff)
            lab.book(m, "compute", -(fleet_cost - lease))
            lab.book(m, "leased_power", -lease)
            lab.book(m, "data_annual", -data_annual)
            lab.book(m, "compliance", -compliance)
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
                "researchers": lab.researchers, "stars": lab.stars,
                "shelved": lab.shelved, "postgen": lab.post_gen,
                "debt": lab.safety_debt, "trust": lab.trust,
                "nincidents": len(lab.incidents),
                "shipped_this_month": bool(lab.ships and lab.ships[-1][0] == m),
                "ship_kind": lab.ships[-1][1] if lab.ships and lab.ships[-1][0] == m else "",
                "ship_tag": lab.ships[-1][2] if lab.ships and lab.ships[-1][0] == m else "",
            })

    def _observe(self, m):
        """
        Every lab looks at every rival and forms a view. Nothing downstream
        of here is allowed to read a rival's true state - decisions run on
        these beliefs, which is what makes misrepresentation worth doing.
        """
        for lab in self.labs:
            lab.beliefs = [INTEL.observe(lab, t, self, m)
                           for t in self.labs if t is not lab]
            own = 0.0
            if lab.model and lab.model.caps:
                own = max(lab.model.caps.values())
            if lab.internal and lab.internal.caps:
                own = max(own, max(lab.internal.caps.values()))
            lab.own_best = own
            lab.threat, lab.feared = INTEL.threat(lab, lab.beliefs, own)
            lab.perceived_frontier = INTEL.perceived_frontier(
                lab.beliefs, lab.doctrine.get("paranoia", K.PARANOIA_DEFAULT))

    def _talent_market(self, m):
        """
        Hiring, compensation, and where the exceptional people go.

        Researchers are a genuinely scarce global stock. When every lab
        hires against the same pool, compensation rises for all of them;
        stars move toward whoever offers the most compute per head, the best
        package and the most credible mission.
        """
        supply = T.global_researcher_pool(m)
        demand = sum(l.researchers for l in self.labs)
        rate = self.market_comp            # priced in _decide, this month

        for lab in self.labs:
            target = lab.actions.headcount_ambition
            # you can only hire what you can pay for and what exists
            want = lab.researchers * (1.0 + 0.035 * target)
            scarcity = max(0.0, supply - demand) / max(supply, 1.0)
            afford = lab.cash > lab.researchers * rate * 1.5
            if afford and scarcity > 0.02:
                lab.researchers = want
                lab.engineers = lab.researchers * 2.2
            # pay to keep people, or lose them - the offer is the policy's
            lab.comp_offer = lab.actions.comp_offer
            if lab.comp_offer < rate * 0.85:
                lab.researchers *= 0.985
                lab.mission_alignment = max(5.0, lab.mission_alignment - 0.3)

        # Stars: a small global pool. New entrants pick a lab by attraction;
        # people already placed drift toward better-supported work. Nobody
        # corners the market, because attraction falls as a lab's compute is
        # spread over more heads.
        pool = T.global_star_pool(m)
        held = sum(l.stars for l in self.labs)
        scores = [T.attraction(l, m, rate) for l in self.labs]
        weights = E.logit_share(scores, temperature=0.9)
        entrants = max(0.0, pool - held) * 0.09
        for lab, wt in zip(self.labs, weights):
            lab.stars += entrants * wt
        # churn: a fraction of everyone's stars is up for grabs each month
        loose = 0.0
        for lab in self.labs:
            leaving = lab.stars * K.STAR_MOVE_RATE
            lab.stars -= leaving
            loose += leaving
        for lab, wt in zip(self.labs, weights):
            lab.stars += loose * wt

    def _sector_spend(self, m):
        """
        What the world will pay this month. Driven by the best capability
        that actually exists, never by the date - if an assistant worth
        paying for existed in 2020, it would have been paid for in 2020.
        The only thing time does is limit how fast adoption catches up.
        """
        best_lang = max((l.model.caps.get("LANG", 0.0)
                         for l in self.labs if l.model), default=0.0)
        if best_lang <= 0:
            return 0.0
        unlocked = K.SPEND_AT_REFERENCE * 10 ** (
            K.SPEND_PER_OOM * (best_lang - K.SPEND_REFERENCE_CAPABILITY))
        stock = getattr(self, "spend_stock", 0.0)
        k = 1 - 0.5 ** (1.0 / K.DIFFUSION_HALFLIFE_M)
        stock += (unlocked - stock) * k
        self.spend_stock = stock
        self.spend_unlocked = unlocked
        return stock / 12.0

    def published_scores(self, lab):
        """This lab's published numbers, as the world sees them."""
        if not lab.model:
            return {}
        out = {}
        pc = lab.perceived_caps()
        for suite, spec in TASKS.SUITES.items():
            dom = spec["domain"]
            f = pc.get(dom, 0.0)
            if f <= 0:
                continue
            sc = self.suites.score(suite, f, softness=lab.elicitation)
            out[dom] = max(0.0, min(100.0, sc + lab.model.eval_noise.get(suite, 0.0)))
        return out

    def aa(self, lab):
        """The headline index for one lab: (AA, coverage, blind share)."""
        return TASKS.aggregate_index(self.suites, self.published_scores(lab),
                                     softness=lab.elicitation)

    def _safety(self, m):
        """
        Buy down debt, then roll for trouble. Severity is drawn from what the
        lab's models can do, not from how careless it has been - carelessness
        only changes the odds and tilts the draw.
        """
        self.regulation *= K.REGULATION_DECAY
        for lab in self.labs:
            if not lab.model:
                continue
            # safety work: a deliberate spend that buys down debt
            want = lab.actions.safety_spend
            if want > 0 and lab.safety_debt > 0 and lab.cash > 0:
                budget = min(lab.cash * 0.02,
                             want * K.SAFETY_SPEND_PER_POINT * 2.0)
                retired = budget / K.SAFETY_SPEND_PER_POINT
                lab.safety_debt = max(0.0, lab.safety_debt - retired)
                lab.cash -= budget
                lab.book(m, "safety", -budget)
                lab.safety_cost = getattr(lab, "safety_cost", 0.0) + budget
            # debt accrues just from operating a deployed system
            lab.safety_debt += K.SAFETY_DEBT_DRIFT

            # Reputation heals toward a baseline, slower the worse your
            # record is. A clean lab recovers from a bad quarter; a lab with
            # a history of incidents does not get the benefit of the doubt.
            scar = 1.0 / (1.0 + K.TRUST_SCAR * len(lab.incidents))
            gap = K.TRUST_BASELINE - lab.trust
            lab.trust += gap * K.TRUST_RECOVERY * scar

            p = SAFE.incident_probability(lab, m)
            if lab.rng_safety.random() < p:
                sev = SAFE.draw_severity(lab.rng_safety, lab)
                SAFE.apply_incident(lab, self, sev, m, lab.rng_safety)

    def _score_suites(self, m):
        """
        Publish this month's benchmark table, and retire any suite the field
        has exhausted. A retiring suite takes the chasers' padding with it:
        a new distribution of tasks is not the one you optimised for.
        """
        self.scores = {}
        for suite, spec in TASKS.SUITES.items():
            dom = spec["domain"]
            best = 0.0
            for lab in self.labs:
                if not lab.model:
                    continue
                f = lab.perceived_caps().get(dom, 0.0)
                if f <= 0:
                    continue
                sc = self.suites.score(suite, f, softness=lab.elicitation)
                sc = max(0.0, min(100.0, sc + lab.model.eval_noise.get(suite, 0.0)))
                self.scores.setdefault(suite, {})[lab.name] = sc
                best = max(best, sc)
            if best > 0 and self.suites.maybe_retire(suite, best, m):
                for lab in self.labs:
                    lab.chase[dom] = lab.chase.get(dom, 0.0) * 0.25

    def _data_auction(self, m):
        """
        Exclusive corpora go to whoever values them most, not to whoever is
        biggest. A rights holder takes the higher bid, and a specialist's bid
        for the corpus its whole business depends on beats a generalist's
        bid for something it would weight at seven per cent.
        """
        for key, src in D.DATA_SOURCES.items():
            if not src["exclusive"] or key in self.claimed_exclusives:
                continue
            bids = []
            for lab in self.labs:
                b = lab.actions.data_bids.get(key)
                if b and key not in lab.data.sources:
                    bids.append((b, lab))
            if not bids:
                continue
            bids.sort(key=lambda x: -x[0])
            price = bids[0][0] if len(bids) == 1 else bids[1][0] * 1.05
            winner = bids[0][1]
            winner.take_data(key, m, min(price, bids[0][0]))
            self.claimed_exclusives.add(key)
            winner.won_data = getattr(winner, "won_data", []) + [key]

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
            lab.researchers = max(1.0, lab.researchers)
            # story value: being at or near the frontier is worth something
            own = lab.model.capability if lab.model else 0.0
            behind = max(0.0, fcap - own)
            # A lab at the frontier with no revenue is still worth funding -
            # that is what the whole 2020-2023 period was. Capability-led
            # strategies raise on the story; earnings-led ones do not.
            narrative = 10 ** (lab.doctrine.get("story_cap_gain", 0.35)
                               * max(0.0, own - 24.0))
            story = (lab.doctrine.get("story_value", 2.0e9) * narrative
                     * (10 ** (-0.55 * behind)))
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
                annual = min(parent * growth,
                             lab.doctrine.get("parent_cap", 1.5e11))
                lab.cash += annual / 12.0
                lab.book(m, "parent", annual / 12.0)

            # ---- raise, if the market will have you. Either the standing
            # rule (runway trigger) or an explicit one-shot from the policy.
            runway = lab.cash / max(lab.last_costs, 1.0)
            can = lab.doctrine.get("can_raise", True)
            since = m - getattr(lab, "last_raise", -99)
            dilution = 0.0
            if lab.actions.auto_raise:
                if runway < lab.actions.raise_runway and can and since >= 11:
                    dilution = lab.actions.raise_fraction
            elif lab.actions.raise_now > 0 and can and since >= 3:
                dilution = lab.actions.raise_now
            if (not lab.actions.auto_raise and lab.actions.raise_now > 0
                    and dilution == 0):
                why = ("your backer does not sell equity" if not can
                       else f"only {since} months since the last round (3 needed)")
                lab.notices.append((m, f"round not raised: {why}"))
            if dilution > 0:
                amount = lab.valuation * dilution
                lab.cash += amount
                lab.last_raise = m
                lab.raised = getattr(lab, "raised", 0.0) + amount
                lab.book(m, "equity_raised", amount)

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
                    lab.book(m, "debt_drawn", draw)

            # ---- contract power ahead of need
            planned = lab.fleet.megawatts() + sum(
                a.megawatts(c) for a, c, _m, _p in lab.orders)
            pipeline = sum(mw for mw, _a in lab.mw_pipeline)
            target = max(planned, 5.0) * lab.actions.power_lookahead
            lease_market = K.LEASE_MARKET_MW.get(year, 52_000)
            lease_cap = lease_market * lab.doctrine.get("supply_share", 0.2)
            lab.lease_cap_mw = lease_cap
            need = 0.0
            if lab.actions.auto_power:
                if lab.contracted_mw + pipeline < target:
                    need = min(target - lab.contracted_mw - pipeline, lease_cap)
            elif lab.actions.contract_mw > 0:
                need = min(lab.actions.contract_mw, lease_cap)
                if need < lab.actions.contract_mw:
                    lab.notices.append((m, f"power contract clipped to {need:,.0f} MW: "
                                           f"that is all the market will lease you this year"))
            if need > 0:
                share = lab.actions.lease_share
                cost = need * (1 - share) * K.DC_CAPEX_PER_MW
                if cost < lab.cash * 0.45:
                    lab.cash -= cost
                    lab.contract_power(need, m, share)
                    lab.capex_by_year[year] = lab.capex_by_year.get(year, 0.0) + cost
                    lab.book(m, "capex_datacentre", -cost)
                elif not lab.actions.auto_power:
                    lab.notices.append((m, f"power contract refused: building {need*(1-share):,.0f} MW "
                                           f"costs ${cost/1e6:,.0f}M, over 45% of cash. Lease a bigger share, or contract less"))

            # ---- buy accelerators
            # capex posture is the policy's call - including the spiral,
            # where perceived deficit raises aggression and the over-building
            # is itself the signal that worries everyone else
            aggression = lab.actions.capex_aggression
            lab.effective_aggression = aggression
            lab.fab_cap = int(supply * lab.doctrine.get("supply_share", 0.2))
            if lab.actions.auto_capex:
                budget = max(0.0, lab.cash * aggression)
                count = int(budget / accel.capex)
            else:
                count = int(lab.actions.buy_accels)
            asked = count
            count = min(count, lab.fab_cap)
            if not lab.actions.auto_capex and count < asked:
                lab.notices.append((m, f"accelerator order clipped to {count:,} by fab supply "
                                       f"(your share of this year's output)"))
            asked = count
            count = min(count, lab.headroom_accels(accel))
            if not lab.actions.auto_capex and count < asked:
                lab.notices.append((m, f"accelerator order clipped to {count:,}: no contracted power "
                                       f"for more (each {accel.name} needs {accel.watts*K.PUE/1e3:.2f} kW)"))
            if count > 0:
                bought = lab.order(accel, count, m, lead_months=5)
                if not lab.actions.auto_capex and bought < count:
                    lab.notices.append((m, f"accelerator order clipped to {bought:,} by cash"))
                lab.capex_by_year[year] = (lab.capex_by_year.get(year, 0.0)
                                           + bought * accel.capex)
                lab.book(m, "capex_accelerators", -bought * accel.capex)
