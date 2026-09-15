"""
A local web dashboard for playing Frontier. Zero dependencies.

    python3 -m sim.serve                 # then open http://localhost:8765
    python3 -m sim.serve --seed 11 --lab 3 --port 8000
    python3 -m sim.serve --no-browser     # don't auto-open a browser tab

The page is `viewer/play.html`; this module runs the game and answers JSON.
The world runs in a worker thread so that the release interrupt can block
mid-quarter while the browser shows the question; the page polls `/api/state`.

  GET  /api/state    everything the page shows: report, orders, events,
                     history, the pending question if any
  POST /api/orders   {field: value, ...}  -> validated on a copy; refused
                     with a reason if illegal
  POST /api/end      {"months": 1|3}  run the next turn (ignored while one runs)
  POST /api/answer   {"ship": bool, "evaluate": bool}  -> answers a release question
                     {"run": {...}} or {"wait": true}   -> answers a run question
  POST /api/preview  a run shape -> expected capability per domain, risk
  POST /api/buy      {"kind": "accels"|"power"|"raise"|"data", "amount": ...}
                     -> buys now; cash moves immediately
  POST /api/new      {"seed": int, "lab": int}  -> a fresh game
  POST /api/auto     hand the seat to the strategy AI
"""
import json
import os
import queue
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .game import Game, date
from .policy import Release, RunPlan, IllegalAction, validate, validate_plan, _BOUNDS, _FLAGS
from . import domains as D

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = os.path.join(HERE, "..", "viewer", "play.html")

# one line per order, for the page - what it is, in plain words
EXPLAIN = {
    "train": "Share of your accelerators pouring compute into the next model.",
    "serve": "Share answering paying customers. Too little and you turn business away.",
    "experiment": "Share on research: buys algorithmic efficiency that compounds for years.",
    "run_months": "How long the next training run should take. Shorter = smaller run.",
    "tokens_per_param": "Data per parameter. Higher = smaller, cheaper-to-serve model from the same compute.",
    "moe_sparsity": "Mixture-of-experts factor. Higher = cheaper to serve, same size.",
    "test_time_oom": "Extra compute spent per answer at inference (orders of magnitude). Better answers, worse margins.",
    "chase_rate": "Effort spent optimising for the published benchmarks rather than real capability. Inflates your scores; occasionally you get caught.",
    "price_stance": "1 = cost-plus at the going markup. Lower = thinner margin, more share where buyers can't tell models apart.",
    "loss_leader": "Below 1 = deliberately selling below cost to own a market.",
    "headcount_ambition": "Hiring appetite. You can only hire people who exist and whom you can pay.",
    "comp_offer": "What you pay a researcher per year, in $k. Below ~85% of market and people leave.",
    "safety_spend": "Safety effort. Buys down safety debt; costs cash.",
    "capex_aggression": "Share of cash spent on accelerators each month. Capped by power, fab supply and cash.",
    "power_lookahead": "Megawatts contracted per megawatt in use. Power takes years to arrive; contract ahead.",
    "lease_share": "Of new power, the fraction leased (fast, pay forever) vs built (slow, cheap to run).",
    "raise_runway": "Raise money when runway (months of cash) drops below this.",
    "raise_fraction": "Fraction of the company sold in a round.",
    "intel_spend": "Effort spent reading rivals. Narrows the error bars on what you believe about them.",
    "openness": "How much you publish. Open weights speed the whole field up and buy developer mindshare, not revenue.",
    "data_share": "Fraction of a corpus you take when you license it.",
    "data_buy": "The one non-exclusive corpus to license this quarter.",
    "data_bids": "Your ceiling, in $M, at each exclusive-corpus auction.",
    "mixture": "What the next model trains on. Decides which markets it can even enter.",
    "extend_run_months": "Grow the run in progress by this many months of your fleet's training output. A bigger run, later.",
    "finish_run": "Land the run in progress on what it has banked so far. Smaller than planned, but now.",
    "start_run": "Plan a new training run at the start of the next turn. Until then the training lane post-trains, researches and serves.",
    "synth_domain": "Generate training data in this domain with the model you have. Amplifies a stock you hold; a domain with no data yields nothing. Known from mid-2023.",
    "synth_share": "Share of the training lane's compute spent generating data each month. Comes straight out of the run in progress.",
    "auto_capex": "Auto: spend `capex aggression` x cash on accelerators every month. Manual: only what you order below.",
    "buy_accels": "Order this many accelerators now. Arrive in ~5 months. Capped by fab supply and your contracted power.",
    "auto_power": "Auto: keep contracted power at `power lookahead` x what you use. Manual: only what you order below.",
    "contract_mw": "Contract this many megawatts now. Leased power arrives in months; built power in years. Capped by the market.",
    "auto_raise": "Auto: raise a round whenever runway drops below `raise runway`. Manual: only when you say so.",
    "raise_now": "Raise a round now, selling this fraction of the company at the current valuation. At least 3 months between rounds.",
}

GROUPS = [
    ("Compute", ["train", "serve", "experiment"]),
    ("Buying compute", ["auto_capex", "capex_aggression", "buy_accels",
                        "auto_power", "power_lookahead", "contract_mw", "lease_share"]),
    ("The next model", ["run_months", "tokens_per_param", "moe_sparsity", "test_time_oom",
                        "mixture"]),
    ("Market", ["price_stance", "loss_leader", "chase_rate", "openness"]),
    ("People & safety", ["headcount_ambition", "comp_offer", "safety_spend", "intel_spend"]),
    ("Money", ["auto_raise", "raise_runway", "raise_fraction", "raise_now"]),
    ("Data", ["data_share", "data_buy", "data_bids", "synth_domain", "synth_share"]),
]


class Session:
    def __init__(self, seed=7, lab=0, randomized=True):
        self.lock = threading.Lock()
        self.new(seed, lab, randomized)

    def new(self, seed, lab, randomized=True):
        self.seed, self.lab_index = seed, lab
        self.game = Game(seed=seed, player=lab, randomized=randomized,
                         ask_release=self._ask, ask_run=self._ask_run)
        self.busy = False
        self.pending = None                 # the question the browser must answer
        self.answers = queue.Queue()
        self.history = []                   # one point per quarter
        self.events = []                    # [(quarter, text)]
        self.error = None
        self._record()

    # --- the interrupt, from the worker thread
    def _ask(self, obs, candidate, held):
        lab = obs.lab
        new = candidate.caps
        old = lab.model.caps if lab.model else {}
        self.pending = {
            "kind": "release",
            "month": obs.month, "date": date(obs.month), "held": held,
            "best_new": max(new.values()) if new else candidate.capability,
            "best_old": max(old.values()) if old else 0.0,
            "frontier": obs.perceived_frontier,
            "domains": [{"d": d, "new": new[d], "old": old.get(d)}
                        for d in sorted(new, key=lambda d: -new[d]) if new[d] > 0],
            "safety_debt": lab.safety_debt, "trust": lab.trust,
            "improves": getattr(candidate, "improves", True),
            "tag": getattr(candidate, "tag", ""),
        }
        board, projected = self.game.leaderboard(candidate)
        self.pending["board"] = board
        self.pending["projected_aa"] = projected
        rel = self.answers.get()            # blocks until the browser answers
        self.pending = None
        return rel

    def _ask_run(self, obs, proposal):
        """The run interrupt, from the worker thread: show the proposal and
        wait for a plan (or 'wait')."""
        lab = obs.lab
        from . import explain as EXPL
        rate = EXPL.run_rate_flop_per_month(lab, lab.actions.train)
        self.pending = {
            "kind": "run",
            "month": obs.month, "date": date(obs.month),
            "proposal": proposal.to_dict(),
            "proposal_months": (proposal.target_flop / rate) if rate > 0 else None,
            "rate_per_month": rate,
            "largest_run": lab.largest_run,
            "current": dict(lab.model.caps) if lab.model else {},
            "feared": getattr(lab, "perceived_frontier", 0.0),
            "train_share": lab.actions.train,
        }
        ans = self.answers.get()
        self.pending = None
        if ans is None:                     # wait a month
            p = proposal.copy(); p.target_flop = 0.0
            return p
        return ans

    def _record(self):
        r = self.game.report()
        self.history.append({
            "q": self.game.turn, "date": r["date"], "cash": r["cash"], "arr": r["arr"],
            "own": r["own_best"], "feared": r["perceived_frontier"], "aa": r["aa"],
            "trust": r["trust"], "debt": r["safety_debt"], "accels": r["accels"],
            "researchers": r["researchers"], "valuation": r["valuation"],
            "board": {row["name"]: row["aa"] for row in r["board"]},
            "hw": {"lead": {d["name"]: d["lead_months"] for d in r["hardware"]["designers"]},
                   "share": {d["name"]: d["share"] for d in r["hardware"]["designers"]},
                   "price": {d["name"]: d["price"] for d in r["hardware"]["designers"]},
                   "hbm": r["hardware"]["hbm_price"], "demand": r["hardware"]["demand_chips"],
                   "pkg": r["hardware"]["foundries"][0]["packaging_k"]},
            "geo": {"spend_share_gdp": r["geo"]["spend_share_gdp"],
                    "load_share_grid": r["geo"]["load_share_grid"],
                    "rate": r["geo"]["rate"], "appetite": r["geo"]["appetite"],
                    "mood": {b: s["mood"] for b, s in r["geo"]["blocs"].items()},
                    "access": {b: s["access"] for b, s in r["geo"]["blocs"].items()}},
        })
        self.snapshot = r

    def end_quarter(self, months=3):
        if self.busy or self.game.over:
            return
        self.busy = True
        self.error = None
        self.months = max(1, min(12, int(months)))
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            ev = self.game.commit(months=self.months)
            self.events.extend((self.game.turn, e) for e in ev)
            self._record()
        except Exception as e:             # surface it rather than hang the page
            self.error = f"{type(e).__name__}: {e}"
        finally:
            self.busy = False

    def set_orders(self, patch):
        if self.busy:
            raise IllegalAction("a quarter is running; wait for it to finish")
        o = self.game.orders.copy()
        for f, v in patch.items():
            if f in ("mixture", "data_bids"):
                if not isinstance(v, dict):
                    raise IllegalAction(f"{f} must be an object")
                if f == "mixture":
                    mix = {k.upper(): float(x) for k, x in v.items() if float(x) > 0}
                    tot = sum(mix.values())
                    if tot <= 0:
                        raise IllegalAction("mixture must be positive")
                    v = {k: x / tot for k, x in mix.items()}
                else:
                    v = {k: float(x) * 1e6 for k, x in v.items() if float(x) > 0}
                setattr(o, f, v)
            elif f in ("data_buy", "synth_domain"):
                setattr(o, f, v or None)
            elif f in _FLAGS:
                setattr(o, f, bool(v))
            elif f in _BOUNDS:
                v = float(v)
                if f == "comp_offer":
                    v *= 1e3
                if f == "buy_accels":
                    v = int(v)
                setattr(o, f, v)
            else:
                raise IllegalAction(f"unknown order {f!r}")
        tot = o.train + o.serve + o.experiment
        if tot > 0:
            o.train, o.serve, o.experiment = o.train / tot, o.serve / tot, o.experiment / tot
        validate(o)
        self.game.policy.orders = o
        self.snapshot = self.game.report()

    def state(self):
        g = self.game
        o = g.orders.to_dict()
        o["comp_offer"] = o["comp_offer"] / 1e3
        o["data_bids"] = {k: v / 1e6 for k, v in (o["data_bids"] or {}).items()}
        return {
            "seed": self.seed, "lab": self.lab_index, "busy": self.busy,
            "progress": list(self.game.progress), "month": g.world.month,
            "over": g.over, "error": self.error, "pending": self.pending,
            "report": self.snapshot, "orders": o, "history": self.history,
            "events": [{"q": q, "text": t} for q, t in self.events[-60:]],
            "explain": EXPLAIN, "groups": GROUPS, "bounds": _BOUNDS,
            "domains": D.DOMAIN_KEYS,
            "sources": {k: {"name": v["name"], "exclusive": v["exclusive"]}
                        for k, v in D.DATA_SOURCES.items()},
            "labs": [l.name for l in g.world.labs],
        }


def _plan_from(body, session, allow_partial=False):
    """A RunPlan from what the page sends: months or target_flop, plus the
    recipe; anything missing falls back to the standing orders."""
    from . import explain as EXPL
    g = session.game
    o = g.orders
    lab = g.player
    rate = EXPL.run_rate_flop_per_month(lab, o.train)
    if body.get("target_flop") is not None:
        target = float(body["target_flop"])
    elif body.get("months") is not None:
        target = rate * float(body["months"])
    else:
        target = rate * o.run_months
    mix = body.get("mixture")
    if mix:
        mix = {k.upper(): float(v) for k, v in mix.items() if float(v) > 0}
        tot = sum(mix.values())
        mix = {k: v / tot for k, v in mix.items()} if tot > 0 else dict(o.mixture)
    else:
        mix = dict(o.mixture)
    return RunPlan(target,
                   float(body.get("tokens_per_param", o.tokens_per_param)),
                   float(body.get("moe_sparsity", o.moe_sparsity)),
                   float(body.get("test_time_oom", o.test_time_oom)), mix)


def _finite(x):
    """Browsers' JSON.parse rejects Infinity/NaN; send null instead."""
    import math
    if isinstance(x, float):
        return x if math.isfinite(x) else None
    if isinstance(x, dict):
        return {k: _finite(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_finite(v) for v in x]
    return x


SESSION = None


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):            # quiet
        pass

    def _json(self, obj, code=200):
        body = json.dumps(_finite(obj)).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path.split("?")[0] in ("/", "/index.html"):
            with open(PAGE, "rb") as f:
                body = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.path.startswith("/api/state"):
            with SESSION.lock:
                self._json(SESSION.state())
        else:
            self._json({"error": "not found"}, 404)

    def do_POST(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        body = json.loads(raw) if raw else {}
        try:
            with SESSION.lock:
                if self.path == "/api/orders":
                    SESSION.set_orders(body)
                elif self.path == "/api/end":
                    SESSION.end_quarter(body.get("months", 3))
                elif self.path == "/api/answer":
                    if SESSION.pending is None:
                        raise IllegalAction("nothing to answer")
                    if SESSION.pending["kind"] == "run":
                        if body.get("wait"):
                            SESSION.answers.put(None)
                        else:
                            plan = _plan_from(body.get("run") or {}, SESSION)
                            validate_plan(plan)
                            SESSION.answers.put(plan)
                    else:
                        SESSION.answers.put(Release(bool(body.get("ship", True)),
                                                    bool(body.get("evaluate", True)),
                                                    shelve=bool(body.get("shelve", False))))
                elif self.path == "/api/buy":
                    if SESSION.busy:
                        raise IllegalAction("wait for the turn to finish")
                    res = SESSION.game.buy_now(str(body.get("kind")), body.get("amount"))
                    SESSION.snapshot = SESSION.game.report()
                    return self._json({"ok": True, "result": _finite(res)})
                elif self.path == "/api/preview":
                    if SESSION.busy and SESSION.pending is None:
                        raise IllegalAction("a turn is running")
                    p = _plan_from(body, SESSION, allow_partial=True)
                    return self._json(SESSION.game.preview(
                        target_flop=p.target_flop, tokens_per_param=p.tokens_per_param,
                        moe_sparsity=p.moe_sparsity, test_time_oom=p.test_time_oom,
                        mixture=p.mixture))
                elif self.path == "/api/new":
                    SESSION.new(int(body.get("seed", 7)), int(body.get("lab", 0)),
                                not body.get("historical", False))
                elif self.path == "/api/auto":
                    p = SESSION.game.policy
                    p.orders = None
                    p.decide = p.defaults.decide
                    p.ask = None
                else:
                    return self._json({"error": "not found"}, 404)
            self._json({"ok": True})
        except IllegalAction as e:
            self._json({"error": str(e)}, 400)
        except Exception as e:
            self._json({"error": f"{type(e).__name__}: {e}"}, 500)


def main(argv):
    global SESSION
    seed, lab, port, hist = 7, 0, 8765, False
    it = iter(argv)
    for a in it:
        if a == "--seed":
            seed = int(next(it))
        elif a == "--lab":
            lab = int(next(it))
        elif a == "--port":
            port = int(next(it))
        elif a == "--historical":
            hist = True
    SESSION = Session(seed, lab, not hist)
    import socket
    try:
        # two servers on one port would silently split requests between
        # them (SO_REUSEADDR); refuse instead
        ThreadingHTTPServer.allow_reuse_address = False
        srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError as e:
        print(f"could not listen on port {port} ({e}); is a game already running? "
              f"try --port 8000")
        return
    # Browsers try localhost over IPv6 first; without a listener there every
    # request waits for that attempt to fail. Listen on ::1 too.
    try:
        class V6(ThreadingHTTPServer):
            address_family = socket.AF_INET6
            allow_reuse_address = False
        srv6 = V6(("::1", port), Handler)
        threading.Thread(target=srv6.serve_forever, daemon=True).start()
    except OSError:
        srv6 = None
    url = f"http://localhost:{port}"
    print(f"Frontier: {url}   (seed {seed}, you are {SESSION.game.player.name}; "
          f"Ctrl-C to stop)")
    if "--no-browser" not in argv:
        import webbrowser
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
        if srv6:
            srv6.shutdown()
            srv6.server_close()


if __name__ == "__main__":
    main(sys.argv[1:])
