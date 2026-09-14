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
  POST /api/end      run the next quarter (ignored while one is running)
  POST /api/answer   {"ship": bool, "evaluate": bool}  -> answers the interrupt
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
from .policy import Release, IllegalAction, validate, _BOUNDS
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
    "ship_cooldown": "Months between landing a run and starting the next (post-training, evals, launch prep).",
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
}

GROUPS = [
    ("Compute", ["train", "serve", "experiment", "capex_aggression", "power_lookahead", "lease_share"]),
    ("The next model", ["run_months", "tokens_per_param", "moe_sparsity", "test_time_oom",
                        "ship_cooldown", "mixture"]),
    ("Market", ["price_stance", "loss_leader", "chase_rate", "openness"]),
    ("People & safety", ["headcount_ambition", "comp_offer", "safety_spend", "intel_spend"]),
    ("Money", ["raise_runway", "raise_fraction"]),
    ("Data", ["data_share", "data_buy", "data_bids"]),
]


class Session:
    def __init__(self, seed=7, lab=0, randomized=True):
        self.lock = threading.Lock()
        self.new(seed, lab, randomized)

    def new(self, seed, lab, randomized=True):
        self.seed, self.lab_index = seed, lab
        self.game = Game(seed=seed, player=lab, randomized=randomized,
                         ask_release=self._ask)
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
            "month": obs.month, "date": date(obs.month), "held": held,
            "best_new": max(new.values()) if new else candidate.capability,
            "best_old": max(old.values()) if old else 0.0,
            "frontier": obs.perceived_frontier,
            "domains": [{"d": d, "new": new[d], "old": old.get(d)}
                        for d in sorted(new, key=lambda d: -new[d]) if new[d] > 0],
            "safety_debt": lab.safety_debt, "trust": lab.trust,
        }
        rel = self.answers.get()            # blocks until the browser answers
        self.pending = None
        return rel

    def _record(self):
        r = self.game.report()
        self.history.append({
            "q": self.game.turn, "date": r["date"], "cash": r["cash"], "arr": r["arr"],
            "own": r["own_best"], "feared": r["perceived_frontier"], "aa": r["aa"],
            "trust": r["trust"], "debt": r["safety_debt"], "accels": r["accels"],
            "researchers": r["researchers"], "valuation": r["valuation"],
        })
        self.snapshot = r

    def end_quarter(self):
        if self.busy or self.game.over:
            return
        self.busy = True
        self.error = None
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        try:
            ev = self.game.commit()
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
            elif f == "data_buy":
                setattr(o, f, v or None)
            elif f in _BOUNDS:
                v = float(v)
                if f == "comp_offer":
                    v *= 1e3
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
            "over": g.over, "error": self.error, "pending": self.pending,
            "report": self.snapshot, "orders": o, "history": self.history,
            "events": [{"q": q, "text": t} for q, t in self.events[-60:]],
            "explain": EXPLAIN, "groups": GROUPS, "bounds": _BOUNDS,
            "domains": D.DOMAIN_KEYS,
            "sources": {k: {"name": v["name"], "exclusive": v["exclusive"]}
                        for k, v in D.DATA_SOURCES.items()},
            "labs": [l.name for l in g.world.labs],
        }


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
                    SESSION.end_quarter()
                elif self.path == "/api/answer":
                    if SESSION.pending is None:
                        raise IllegalAction("nothing to answer")
                    SESSION.answers.put(Release(bool(body.get("ship", True)),
                                                bool(body.get("evaluate", True))))
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
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    except OSError as e:
        print(f"could not listen on port {port} ({e}); try --port 8000")
        return
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


if __name__ == "__main__":
    main(sys.argv[1:])
