"""
The game as a window onto the simulation: one lab is yours.

Nothing here changes the world model. `Game` puts a `PlayerPolicy` in one
lab's seat, runs the world three months at a time, and between quarters
hands you a board letter and takes your orders. Everything you can change
is an `Actions` field; everything you can see is what `World.observe`
would show that lab. The AI labs keep their own policies and their own
secrets.

    g = Game(seed=7, player=2)          # you are the third lab
    print(g.letter())                   # the board letter: where you stand
    o = g.orders                        # your standing orders (an Actions)
    o.train, o.serve, o.experiment = 0.55, 0.30, 0.15
    events = g.commit()                 # three months pass on those orders
    for e in events: print(e)

When one of your runs lands mid-quarter the world stops and asks: ship it,
and evaluate it first? Pass `ask_release` to answer; the default ships and
evaluates. `python3 -m sim.play` is the terminal front end.

The whole game is `save()`: the seed and the action log. Replaying it
reproduces the run bit for bit (see `sim/replay.py`).
"""
import json
import math
from . import constants as K
from . import domains as D
from . import tasks as TASKS
from . import talent as T
from .world import World
from .scenarios import randomized_2020, historical_2020
from .policy import Policy, Actions, Release, RunPlan, DoctrinePolicy, validate
from . import explain as EXPL
from . import anchors as A
from . import economics as E
from . import release as REL

MONTHS_PER_TURN = 3


class PlayerPolicy(Policy):
    """
    Holds whatever orders the player gave last and hands them to the world
    every month until they change. `ask_release(obs, cap, held) -> Release`
    is called when a run lands; if none is given the model is shipped and
    evaluated, which is the cautious default.
    """

    def __init__(self, doctrine, ask_release=None, ask_run=None):
        self.defaults = DoctrinePolicy(doctrine)   # a sensible opening book
        self.orders = None
        self.ask = ask_release
        self.ask_run = ask_run
        self.interrupts = []                        # what was asked, and answered
        self.runs = []                              # (month, plan) started

    def decide(self, obs):
        if obs.month < 0:
            # the pre-game ask; nothing is for sale yet, so do not freeze it
            return self.defaults.decide(obs)
        if self.orders is None:
            # the first orders are the strategy's own, so a new player
            # starts from something coherent rather than from zero
            self.orders = self.defaults.decide(obs)
        out = self.orders.copy()
        # one-shots fire once - the first month they are in force - then clear
        self.orders.buy_accels, self.orders.contract_mw, self.orders.raise_now = 0, 0.0, 0.0
        self.orders.extend_run_months, self.orders.finish_run = 0.0, False
        # start_run is cleared when the question is actually asked
        return out

    def decide_run(self, obs, proposal):
        """Asked every month there is no run. The player is only interrupted
        when they pressed 'start a new run' (a one-shot); otherwise the lane
        keeps post-training, researching and serving."""
        first = obs.lab.largest_run <= 0 and not obs.lab.ships
        if self.ask_run is None:
            plan = proposal
        elif first or (self.orders is not None and self.orders.start_run):
            if self.orders is not None:
                self.orders.start_run = False
            plan = self.ask_run(obs, proposal)
        else:
            plan = proposal.copy()
            plan.target_flop = 0.0
        if plan.target_flop > 0:
            self.runs.append((obs.month, plan))
        return plan

    def decide_release(self, obs, candidate, held):
        if self.ask is None:
            rel = Release(ship=True, evaluate=True)
        else:
            rel = self.ask(obs, candidate, held)
        best = max(candidate.caps.values()) if candidate.caps else candidate.capability
        self.interrupts.append((obs.month, best, held, rel))
        return rel


def date(m):
    return f"{2020 + m // 12}-{m % 12 + 1:02d}"


def _b(x):
    """Dollars as $B, sensibly rounded."""
    return f"${x / 1e9:,.2f}B" if abs(x) < 1e11 else f"${x / 1e9:,.0f}B"


def _m(x):
    return f"${x / 1e6:,.0f}M"


class Game:
    def __init__(self, seed=7, player=0, randomized=True, ask_release=None,
                 ask_run=None):
        self.seed = seed
        self.randomized = randomized
        labs = randomized_2020(seed) if randomized else historical_2020()
        self.player_index = player
        self.player = labs[player]
        self.policy = PlayerPolicy(self.player.doctrine, ask_release, ask_run)
        self.player.policy = self.policy
        self.world = World(labs, seed=seed)
        self.turn = 0
        self.events = []                    # everything that happened, all turns
        self.progress = (0, 0)              # (months done, months in this turn)
        self.last_months = MONTHS_PER_TURN  # length of the last turn, for the books

    # ------------------------------------------------------------ the turn
    @property
    def month(self):
        return self.world.month

    @property
    def orders(self):
        """Your standing orders. Edit in place; they take effect on commit."""
        if self.policy.orders is None:
            self.policy.orders = self.policy.defaults.decide(self.world.observe(self.player))
        return self.policy.orders

    def commit(self, orders=None, months=MONTHS_PER_TURN):
        """
        End the turn: the world runs `months` on your orders. Returns the
        events of the quarter, in order, as short strings.
        """
        if orders is not None:
            validate(orders)
            self.policy.orders = orders.copy()
        w, me = self.world, self.player
        before = _Snapshot(w, me)
        self.progress = (0, months)
        for i in range(months):
            if w.month >= 132:
                break
            w.step()
            self.progress = (i + 1, months)
        self.last_months = months
        self.turn += 1
        events = before.events_since(w, me)
        self.events.extend(events)
        return events

    @property
    def over(self):
        return self.world.month >= 132

    # -------------------------------------------------------- the field
    def leaderboard(self, candidate=None):
        """
        Every lab's published AA index, yours included - the public table.
        Rivals are what your intel read off their published scores (a
        belief, refreshed monthly); you are your own published number. With
        `candidate`, adds what YOUR row would read if you shipped it.
        """
        w, me = self.world, self.player
        obs = w.observe(me)
        rows = [dict(name=b.target, aa=b.aa, you=False, silent=b.months_silent)
                for b in obs.beliefs]
        mine = w.aa(me)[0] if me.model else None
        rows.append(dict(name=me.name, aa=mine, you=True, silent=0))
        projected = None
        if candidate is not None:
            keep = me.model
            me.model = candidate
            try:
                projected = w.aa(me)[0]
            finally:
                me.model = keep
        rows.sort(key=lambda r: -(r["aa"] if r["aa"] is not None else -1))
        return rows, projected

    # ------------------------------------------------------- explanations
    def preview(self, months=None, target_flop=None, tokens_per_param=None,
                moe_sparsity=None, test_time_oom=None, mixture=None):
        """
        What a run of this shape would give, expected (luck = 1). Either
        `months` of the fleet's output at the current train share, or an
        explicit `target_flop`. Unset recipe fields take the standing orders.
        """
        w, me, o = self.world, self.player, self.orders
        rate = EXPL.run_rate_flop_per_month(me, o.train)
        if target_flop is None:
            target_flop = rate * (months if months is not None else o.run_months)
        tpp = o.tokens_per_param if tokens_per_param is None else tokens_per_param
        moe = o.moe_sparsity if moe_sparsity is None else moe_sparsity
        tt = o.test_time_oom if test_time_oom is None else test_time_oom
        mix = dict(o.mixture) if mixture is None else dict(mixture)
        ex = EXPL.explain(me, w, w.month, target_flop, tpp, moe, tt, mix)
        ex["months"] = target_flop / rate if rate > 0 else None
        ex["rate_per_month"] = rate
        ex["risk"] = EXPL.risk(me, target_flop, getattr(me, "believed_frontier", 0.0))
        ex["current"] = dict(me.model.caps) if me.model else {}
        ex["feared"] = getattr(me, "perceived_frontier", 0.0)
        return ex

    # ---------------------------------------------------------- the letter
    def report(self):
        """The board letter as data. `letter()` formats it."""
        w, me = self.world, self.player
        m = w.month
        h = me.history[-1] if me.history else None
        costs = max(getattr(me, "last_costs", 0.0), 1.0)
        runway = me.cash / costs if h else float("inf")
        obs = w.observe(me)

        # --- the run in progress
        run = None
        if me.run_target:
            rate = (me.fleet.train_flops() * me.actions.train
                    * K.SECONDS_PER_MONTH / 1.18)
            left = max(0.0, me.run_target - me.train_bank)
            run = dict(target=me.run_target, done=me.train_bank,
                       frac=me.train_bank / me.run_target,
                       months_left=(left / rate if rate > 0 else float("inf")),
                       vs_last=(me.run_target / me.largest_run if me.largest_run else None))

        # --- the model you sell, and what the world scores it at
        scores = w.published_scores(me) if me.model else {}
        aa = w.aa(me)[0] if me.model else None
        table = []
        for suite, spec in TASKS.SUITES.items():
            dom = spec["domain"]
            mine = scores.get(dom)
            best, who = None, None
            for name, sc in w.scores.get(suite, {}).items():
                if name != me.name and (best is None or sc > best):
                    best, who = sc, name
            if mine is None and best is None:
                continue
            table.append(dict(suite=suite, label=w.suites.label.get(suite, suite),
                              domain=dom, mine=mine, best=best, who=who))

        # --- the fleet, generation by generation
        h100 = next(a for a in E.ACCELS if a.name == "H100")
        h100e = lambda flops: flops / h100.train_flops()
        fleet_rows = []
        for accel, count, bought in me.fleet.holdings:
            fleet_rows.append(dict(
                name=accel.name, count=count, bought=date(bought),
                retires=date(bought + K.DEPRECIATION_MONTHS + 12),
                peak_tflops=accel.peak_tflops, mfu=accel.train_mfu,
                train_flops=accel.train_flops() * count,
                serve_flops=accel.serve_flops() * count,
                mw=accel.megawatts(count), watts=accel.watts,
                cost_month=accel.monthly_cost() * count,
                depreciated=(m - bought) >= K.DEPRECIATION_MONTHS))
        fleet_rows.sort(key=lambda r: -r["train_flops"])
        tot_train = me.fleet.train_flops()
        for r in fleet_rows:
            r["share"] = r["train_flops"] / tot_train if tot_train > 0 else 0.0
            r["h100e"] = h100e(r["train_flops"])
        best_now = E.best_available(m)
        fleet = dict(rows=fleet_rows, train_flops=tot_train,
                     serve_flops=me.fleet.serve_flops(), h100e=h100e(tot_train),
                     flop_per_month=tot_train * K.SECONDS_PER_MONTH / 1.18,
                     best_now=best_now.name, best_now_tflops=best_now.peak_tflops,
                     best_now_h100e=h100e(best_now.train_flops()))

        # --- rivals, as you believe them to be
        rivals = []
        for b in sorted(obs.beliefs, key=lambda b: -b.latent_est):
            rivals.append(dict(name=b.target, aa=b.aa, est=b.latent_est,
                               sigma=b.sigma, scale=b.scale,
                               compute=b.compute, h100e=h100e(b.compute),
                               silent=b.months_silent, price=b.price,
                               feared=(b.target == obs.feared)))

        # --- markets
        segs = []
        for key, (tam, rows) in w.segment_state.items():
            shares = dict(rows)
            leader = max(rows, key=lambda r: r[1]) if rows else (None, 0.0)
            segs.append(dict(key=key, name=D.SEGMENTS[key]["name"],
                             tam_yr=tam * 12, mine=shares.get(me.name, 0.0),
                             leader=leader[0], leader_share=leader[1],
                             eligible=me.name in shares,
                             gates=D.SEGMENTS[key]["gates"]))

        # --- data on the table
        owned = sorted(me.data.sources)
        offers, auctions = [], []
        share = me.actions.data_share
        for key, src in D.DATA_SOURCES.items():
            if key in me.data.sources:
                continue
            from .anchors import month_index
            if month_index(src["available"]) > m:
                continue
            price = (src["annual_cost"]
                     + src["one_off_cost_per_btok"] * src["volume"] * share / 1e9)
            row = dict(key=key, name=src["name"], price=price,
                       annual=src["annual_cost"], mix=src["mix"])
            if src["exclusive"]:
                if key not in w.claimed_exclusives:
                    row["bid"] = me.actions.data_bids.get(key)
                    auctions.append(row)
            else:
                row["chosen"] = (me.actions.data_buy == key)
                offers.append(row)

        # --- the books: this quarter and the whole game, by category
        def _sum(months):
            out = {}
            for mm in months:
                for k, v in me.ledger.get(mm, {}).items():
                    out[k] = out.get(k, 0.0) + v
            return out
        q0 = max(0, m - self.last_months)
        ledger_q = _sum(range(q0, m))
        ledger_all = _sum(range(0, m))

        # --- what is on its way, and when
        arriving = sorted(
            [dict(kind="accelerators", what=f"{c:,} x {a.name}", when=date(arr), month=arr)
             for a, c, arr, _p in me.orders]
            + [dict(kind="power", what=f"{mw:,.0f} MW", when=date(arr), month=arr)
               for mw, arr in me.mw_pipeline],
            key=lambda x: x["month"])
        run_eta = None
        if run and run["months_left"] is not None and run["months_left"] < 1e6:
            run_eta = date(m + int(math.ceil(run["months_left"])))

        # --- what a purchase costs right now, so manual orders can be sized
        accel = E.best_available(m)
        shopping = dict(
            accel=accel.name, accel_capex=accel.capex,
            accel_mw=accel.watts * K.PUE / 1e6,
            fab_cap=int(K.FAB_OUTPUT_PER_MONTH.get(2020 + m // 12, 3_800_000)
                        * me.doctrine.get("supply_share", 0.2)),
            power_headroom=me.headroom_accels(accel),
            lease_cap_mw=(K.LEASE_MARKET_MW.get(2020 + m // 12, 52_000)
                          * me.doctrine.get("supply_share", 0.2)),
            dc_capex_per_mw=K.DC_CAPEX_PER_MW,
            lease_opex_per_mw_month=K.LEASE_OPEX_PER_MW_MONTH,
            lease_lead_months=K.LEASE_LEAD_MONTHS,
            build_lead_months=(K.DC_LEAD_TIME_MONTHS
                               + (K.GRID_QUEUE_MONTHS if m >= 66 else 0)),
            accel_lead_months=5,
            cash_cap_power=me.cash * 0.45,
            months_since_raise=m - getattr(me, "last_raise", -99),
            can_raise=me.doctrine.get("can_raise", True),
        )

        board, _ = self.leaderboard()
        # --- between runs: what the training lane is doing instead
        o = self.orders
        lane = me.fleet.train_flops() * o.train * K.SECONDS_PER_MONTH / 1.18
        need = me.post_need()
        post = None
        if me.model and me.post_gen < getattr(me, "post_budget", 0):
            gain = REL.post_train_gain(me.post_gen)
            post = dict(
                gen=me.post_gen + 1, left=getattr(me, "post_budget", 0) - me.post_gen,
                need=need, bank=me.post_bank, frac=(me.post_bank / need if need > 0 else 1.0),
                months_compute=((need - me.post_bank) / lane if lane > 0 else None),
                months_min=max(0, me.post_timer),
                gain_by_domain={d: gain * w for d, w in me.POST_TRAIN_WEIGHT.items()
                                if me.model.caps.get(d, 0) > 0},
                gain=gain)
        idle = dict(lane_flops=me.fleet.train_flops() * o.train, lane_per_month=lane,
                    research_flop=getattr(me, "spare_research_flop", 0.0),
                    research_gain=getattr(me, "last_research", 0.0),
                    launch_prep=me.launch_prep, post=post,
                    start_queued=bool(o.start_run))
        why = getattr(me.model, "why", None) if me.model else None
        run_plan = me.run_plan.to_dict() if me.run_plan else None
        run_preview = None
        if me.run_target:
            run_preview = EXPL.explain(me, w, m, me.run_target, me.run_plan.tokens_per_param,
                                       me.run_plan.moe_sparsity, me.run_plan.test_time_oom,
                                       me.run_plan.mixture)
            run_preview["risk"] = EXPL.risk(me, me.run_target, getattr(me, "believed_frontier", 0.0))
        return dict(
            month=m, date=date(m), turn=self.turn, name=me.name,
            why=why, run_plan=run_plan, run_preview=run_preview, board=board, idle=idle,
            data=EXPL.data_holdings(me),
            ledger_q=ledger_q, ledger_all=ledger_all, shopping=shopping,
            arriving=arriving, run_eta=run_eta, turn_months=self.last_months,
            strategy=me.doctrine.get("strategy_name", "?"),
            cash=me.cash, runway=runway, arr=me.arr,
            net=getattr(me, "last_net", 0.0), costs=costs,
            valuation=me.valuation, raised=getattr(me, "raised", 0.0),
            debt=getattr(me, "debt_drawn", 0.0),
            accels=me.fleet.count(), mw=me.fleet.megawatts(), fleet=fleet,
            contracted_mw=me.contracted_mw,
            on_order=sum(c for _a, c, _m, _p in me.orders),
            mw_pipeline=sum(mw for mw, _a in me.mw_pipeline),
            newest=me.fleet.newest().name,
            researchers=me.researchers, stars=me.stars,
            comp_offer=me.comp_offer, market_comp=w.market_comp,
            model=(dict(name=me.model.name, cap=me.model.capability,
                        shipped=me.model.shipped, shipped_date=date(me.model.shipped),
                        age=m - me.model.shipped,
                        caps=dict(me.model.caps), gen=me.model.generation)
                   if me.model else None),
            internal=(me.internal.capability if me.internal else None),
            aa=aa, table=table, run=run, largest_run=me.largest_run,
            synth_tokens=getattr(me, "synth_tokens", 0.0), synth_domain=getattr(me, "synth_domain", None),
            synth_from=A.month_index(D.SYNTH_AVAILABLE), synth_from_date=date(A.month_index(D.SYNTH_AVAILABLE)),
            shelved=me.shelved, algo=me.algo_mult,
            price=me.price_per_mtok, cost_per_mtok=me.serving_cost_per_mtok(),
            served=getattr(me, "served_mtok", 0.0), unmet=getattr(me, "unmet", 0.0),
            segments=segs, rivals=rivals, threat=obs.threat, feared=obs.feared,
            perceived_frontier=obs.perceived_frontier,
            own_best=getattr(me, "own_best", 0.0),
            trust=me.trust, safety_debt=me.safety_debt,
            unevaluated=(max(0.0, me.model.capability - me.evaluated_at) if me.model else 0.0),
            incidents=len(me.incidents), regulation=w.regulation,
            restricted=(m < me.deploy_restricted_until),
            data_owned=owned, data_offers=offers, data_auctions=auctions,
            orders=self.orders.to_dict(),
        )

    def letter(self):
        r = self.report()
        o = r["orders"]
        L = []
        p = L.append
        p(f"=== {r['name']}  |  {r['date']}  |  quarter {r['turn']}  |  {r['strategy']} ===")
        p("")
        p("MONEY")
        if r["cash"] < 0:
            p("  ** INSOLVENT: cash is negative. The model lets you keep operating; "
              "a real board would not. **")
        p(f"  cash {_b(r['cash'])}   runway {r['runway']:.0f} months   "
          f"revenue {_b(r['arr'])}/yr   net {_m(r['net'])}/month   valuation {_b(r['valuation'])}")
        if r["debt"]:
            p(f"  infrastructure debt drawn {_b(r['debt'])}")
        p("")
        p("COMPUTE")
        p(f"  {r['accels']:,} accelerators ({r['newest']}), {r['mw']:,.0f} MW in use of "
          f"{r['contracted_mw']:,.0f} contracted; {r['on_order']:,} on order, "
          f"{r['mw_pipeline']:,.0f} MW in the pipeline")
        p(f"  split: train {o['train']:.0%}  serve {o['serve']:.0%}  experiment {o['experiment']:.0%}"
          f"   algorithmic edge vs field x{r['algo']:.2f}")
        if r["run"]:
            ru = r["run"]
            vs = f", {ru['vs_last']:.1f}x your last" if ru["vs_last"] else ""
            p(f"  training run: {ru['target']:.1e} FLOP{vs}, {ru['frac']:.0%} done, "
              f"~{ru['months_left']:.0f} months to go")
        else:
            p(f"  no run in progress (largest landed {r['largest_run']:.1e} FLOP, "
              f"{r['shelved']} shelved)")
        p("")
        p("THE MODEL")
        if r["model"]:
            md = r["model"]
            p(f"  {md['name']} shipped {date(md['shipped'])} ({md['age']} months ago), "
              f"x.{md['gen']} release; frontier {md['cap']:.2f}; AA {r['aa']:.1f}"
              if r["aa"] is not None else
              f"  {md['name']} shipped {date(md['shipped'])}; frontier {md['cap']:.2f}")
            if r["internal"]:
                p(f"  ** you are sitting on an unreleased model at {r['internal']:.2f} **")
            p(f"  price ${r['price']:.2f}/Mtok against a cost of ${r['cost_per_mtok']:.2f}; "
              f"served {r['served']:,.0f} Mtok/month" +
              (f", turned away {r['unmet']:,.0f}" if r["unmet"] > 0 else ""))
            p("  scoreboard (published, this month):")
            for t in r["table"]:
                mine = f"{t['mine']:5.1f}" if t["mine"] is not None else "   --"
                best = (f"{t['best']:5.1f} ({t['who']})" if t["best"] is not None else "   --")
                mark = " <" if (t["mine"] is not None and t["best"] is not None and t["mine"] < t["best"]) else ""
                p(f"    {t['label']:<24s} you {mine}   best rival {best}{mark}")
        else:
            p("  nothing shipped yet")
        p("")
        p("MARKETS")
        for s in r["segments"]:
            if s["tam_yr"] <= 0:
                continue
            if s["eligible"]:
                p(f"  {s['name']:<22s} {_b(s['tam_yr']):>9s}/yr   you {s['mine']:5.1%}   "
                  f"leader {s['leader']} {s['leader_share']:.0%}")
            else:
                gate = ", ".join(f"{d} >= {v:.1f}" for d, v in s["gates"].items())
                p(f"  {s['name']:<22s} {_b(s['tam_yr']):>9s}/yr   you: not eligible ({gate})")
        p("")
        p("RIVALS  (what you believe; nobody shows you their books)")
        p(f"  your best, built: {r['own_best']:.2f}    the frontier as you fear it: "
          f"{r['perceived_frontier']:.2f}    threat {r['threat']:+.2f} OOM"
          + (f" ({r['feared']})" if r["feared"] else ""))
        for rv in r["rivals"]:
            aa = f"AA {rv['aa']:5.1f}" if rv["aa"] is not None else "AA   --"
            flag = "  <- the one you fear" if rv["feared"] else ""
            p(f"  {rv['name']:<11s} {aa}   true best ~{rv['est']:.2f} +/-{rv['sigma']:.2f}   "
              f"~{rv['scale']:,.0f} accelerators   quiet {rv['silent']} mo   "
              f"${rv['price']:.2f}/Mtok{flag}")
        p("")
        p("PEOPLE")
        p(f"  {r['researchers']:,.0f} researchers, {r['stars']:.1f} stars; "
          f"you offer ${r['comp_offer']/1e3:,.0f}k against a market rate of "
          f"${r['market_comp']/1e3:,.0f}k" +
          ("  ** below market: people are leaving **" if r["comp_offer"] < r["market_comp"] * 0.85 else ""))
        p("")
        p("SAFETY")
        p(f"  trust {r['trust']:.0f}/100   safety debt {r['safety_debt']:.1f}   "
          f"unevaluated capability {r['unevaluated']:.2f}   incidents so far {r['incidents']}   "
          f"sector regulation {r['regulation']:.2f}" +
          ("   ** barred from agentic markets **" if r["restricted"] else ""))
        p("")
        p("DATA")
        p(f"  licensed: {', '.join(r['data_owned']) or 'nothing'}")
        for d in r["data_offers"]:
            tag = "  <- buying this quarter" if d["chosen"] else ""
            p(f"  for sale   {d['key']:<18s} {d['name']:<28s} {_m(d['price'])}"
              f" (+{_m(d['annual'])}/yr){tag}")
        for d in r["data_auctions"]:
            tag = f"  <- your ceiling {_m(d['bid'])}" if d["bid"] else ""
            p(f"  exclusive  {d['key']:<18s} {d['name']:<28s} ask {_m(d['price'])}"
              f" (+{_m(d['annual'])}/yr){tag}")
        return "\n".join(L)

    def orders_text(self):
        """Your standing orders, one per line, with units."""
        o = self.orders
        rows = [
            ("split", f"train {o.train:.2f} / serve {o.serve:.2f} / experiment {o.experiment:.2f}"),
            ("run_months", f"{o.run_months:.1f}  (size the next run to finish in this many months)"),
            ("tokens_per_param", f"{o.tokens_per_param:.0f}  (higher = smaller, cheaper-to-serve model)"),
            ("moe_sparsity", f"{o.moe_sparsity:.1f}"),
            ("test_time_oom", f"{o.test_time_oom:.2f}  (inference-time compute, in OOM)"),
            ("mixture", " ".join(f"{d} {w:.2f}" for d, w in sorted(o.mixture.items(), key=lambda x: -x[1]))),
            ("chase_rate", f"{o.chase_rate:.2f}  (0-1: effort on the published numbers)"),
            ("price_stance", f"{o.price_stance:.2f}  (1 = cost-plus at market markup; lower = thinner margin)"),
            ("loss_leader", f"{o.loss_leader:.2f}  (below 1 = deliberately below cost)"),
            ("headcount_ambition", f"{o.headcount_ambition:.2f}"),
            ("comp_offer", f"${o.comp_offer/1e3:,.0f}k per researcher per year"),
            ("safety_spend", f"{o.safety_spend:.2f}"),
            ("capex_aggression", f"{o.capex_aggression:.2f}  (share of cash spent on accelerators)"),
            ("power_lookahead", f"{o.power_lookahead:.1f}  (MW contracted per MW in use)"),
            ("lease_share", f"{o.lease_share:.2f}  (of new power, leased rather than built)"),
            ("raise_runway", f"{o.raise_runway:.0f} months  (raise when runway drops below this)"),
            ("raise_fraction", f"{o.raise_fraction:.2f}  (of the company sold per round)"),
            ("intel_spend", f"{o.intel_spend:.2f}"),
            ("openness", f"{o.openness:.2f}  (0 closed .. 1 open weights)"),
            ("data_share", f"{o.data_share:.2f}  (fraction of a corpus you take)"),
            ("data_buy", f"{o.data_buy or 'none'}"),
            ("data_bids", " ".join(f"{k} {_m(v)}" for k, v in o.data_bids.items()) or "none"),
        ]
        return "\n".join(f"  {k:<20s} {v}" for k, v in rows)

    # ------------------------------------------------------------- saving
    def save(self, path):
        with open(path, "w") as f:
            json.dump({"seed": self.seed, "randomized": self.randomized,
                       "player": self.player_index, "months": self.world.month,
                       "log": [[m, who, c] for m, who, c in self.world.action_log]},
                      f)


# ---------------------------------------------------------------- events
class _Snapshot:
    """What was true at the start of the turn, so the end can say what changed."""

    def __init__(self, w, me):
        self.month = w.month
        self.ships = {l.name: len(l.ships) for l in w.labs}
        self.incidents = len(w.incident_log)
        self.retire = len(w.suites.retirements)
        self.claimed = set(w.claimed_exclusives)
        self.interrupts = len(me.policy.interrupts)
        self.raised = getattr(me, "raised", 0.0)
        self.sources = set(me.data.sources)
        self.caught = me.caught
        self.shelved = me.shelved
        self.fleet = me.fleet.count()
        self.notices = len(me.notices)

    def events_since(self, w, me):
        ev = []
        for m, cap, held, rel in me.policy.interrupts[self.interrupts:]:
            what = "the model you were holding" if held else "your training run"
            if rel.ship:
                ev.append(f"{date(m)}  {what} shipped at {cap:.2f}"
                          + ("" if rel.evaluate else " -- WITHOUT a full evaluation"))
            else:
                ev.append(f"{date(m)}  {what} landed at {cap:.2f}; you held it back")
        for l in w.labs:
            for m, kind, tag, cap in l.ships[self.ships[l.name]:]:
                if l is me and kind == "pretrain":
                    continue           # already reported above
                who = "you" if l is me else l.name
                if kind == "post":
                    ev.append(f"{date(m)}  {who} released a point upgrade ({cap:.2f})")
                else:
                    t = f", a {tag}" if tag else ""
                    ev.append(f"{date(m)}  {who} shipped a new model ({cap:.2f}{t})")
        if me.shelved > self.shelved:
            ev.append(f"          a run of yours came in below what you already sell and was shelved")
        for x in w.incident_log[self.incidents:]:
            who = "YOUR" if x["lab"] == me.name else x["lab"] + "'s"
            ev.append(f"{date(x['month'])}  {x['severity'].upper()} incident, {who} model: {x['text']}"
                      + (f" (cost {_m(x['cost'])})" if x["lab"] == me.name else ""))
        for m, suite, lab in w.suites.retirements[self.retire:]:
            ev.append(f"{date(m)}  benchmark {suite} retired: saturated by {lab}")
        for key in w.claimed_exclusives - self.claimed:
            winner = next((l.name for l in w.labs if key in l.data.exclusives), "?")
            who = "you" if winner == me.name else winner
            ev.append(f"          exclusive licence for {D.DATA_SOURCES[key]['name']} went to {who}")
        for key in set(me.data.sources) - self.sources:
            if key not in w.claimed_exclusives:
                ev.append(f"          you licensed {D.DATA_SOURCES[key]['name']}")
        if getattr(me, "raised", 0.0) > self.raised:
            ev.append(f"          you raised {_b(getattr(me, 'raised', 0.0) - self.raised)} "
                      f"at a {_b(me.valuation)} valuation")
        if me.caught > self.caught:
            ev.append("          you were caught training on the test set; trust took a hit")
        if me.fleet.count() > self.fleet:
            ev.append(f"          {me.fleet.count() - self.fleet:,} accelerators arrived")
        for m, text in me.notices[self.notices:]:
            ev.append(f"{date(m)}  ORDER: {text}")
        if not ev:
            ev.append("          a quiet quarter")
        # dated lines in date order; undated summary lines after them
        ev.sort(key=lambda e: (0, e[:7]) if e[:2] == "20" else (1, ""))
        return ev
