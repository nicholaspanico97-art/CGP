"""
The decision seam: observe -> decide -> apply.

Until v1.4 a lab did not decide anything. The monthly tick reached into a
`doctrine` dict and read the lab's parameters inline, so policy and physics
were the same code and there was nowhere for a player to stand.

This module puts the boundary in. Every month, for every lab:

    obs     = world.observe(lab)          # what THIS lab can see
    actions = lab.policy.decide(obs)      # a strategy AI, or a human
    world.apply(lab, actions)             # validated, logged, then in force

and the tick reads `lab.actions`, never `lab.doctrine`, for anything that is
a choice. `doctrine` keeps only what a lab IS - its strategy, its quality,
its parent, its paranoia - which the policy reads and the world does not.

Two kinds of decision, because they happen at different moments:

  Standing decisions (`Actions`) are set once a month and stay in force:
  the compute split, the recipe, prices, hiring, capex posture, data deals,
  safety spend. A player turn is a quarter; a policy that wants to change
  nothing returns the same `Actions` again and the log stays quiet.

  The release decision (`decide_release`) is an interrupt. A training run
  lands mid-month with an outcome nobody knew in advance, and the question
  "ship this or sit on it?" is asked right then, with the result in hand.
  A game surfaces it as a modal; a strategy AI answers from a rule.

`DoctrinePolicy` reproduces the v1.3 behaviour of every strategy exactly,
including the competitive spiral - fear compressing the run window, bidding
up compensation, raising capex aggression - which is now visibly a thing a
lab DOES rather than a thing the world does to it. A player gets no
automatic panic. That is the point.
"""
import math
from . import constants as K
from . import anchors as A
from . import domains as D


class IllegalAction(ValueError):
    """An action the world refuses. Caught, not absorbed."""


# --------------------------------------------------------------- observation
class Observation:
    """
    What one lab can see this month. Its own books in full - it is the lab -
    plus beliefs about rivals with error bars, and whatever is public.

    Nothing here is a rival's true state. `beliefs` come from `intel.observe`
    and carry the chasing, the eval noise and the silence the rival chose.
    """

    __slots__ = ("month", "lab", "beliefs", "threat", "feared",
                 "perceived_frontier", "regulation", "openness",
                 "market_comp", "scores", "segment_state", "sector_incidents",
                 "rng")

    def __init__(self, month, lab, beliefs, threat, feared, perceived_frontier,
                 regulation, openness, market_comp, scores, segment_state,
                 sector_incidents, rng):
        self.month = month
        self.lab = lab                        # own state, in full
        self.beliefs = beliefs                # intel.Belief per rival
        self.threat = threat                  # perceived deficit, OOM
        self.feared = feared                  # who it thinks is ahead
        self.perceived_frontier = perceived_frontier
        self.regulation = regulation          # sector-wide, public
        self.openness = openness              # how open the field is
        self.market_comp = market_comp        # going rate, $/researcher/yr
        self.scores = scores                  # last month's published table
        self.segment_state = segment_state    # last month's market shares
        self.sector_incidents = sector_incidents
        self.rng = rng                        # this lab's decision stream


# ------------------------------------------------------------------ actions
# Every standing decision a lab makes, with the bounds the world enforces.
# (name, lower, upper). None means unchecked on that side.
_BOUNDS = {
    "train": (0.0, 1.0), "serve": (0.0, 1.0), "experiment": (0.0, 1.0),
    "run_months": (0.5, 36.0),
    "tokens_per_param": (1.0, 2000.0), "moe_sparsity": (1.0, 64.0),
    "test_time_oom": (0.0, 3.0),
    "ship_cooldown": (None, 36.0),    # the world floors it at one month
    "chase_rate": (0.0, 1.0),
    "data_share": (0.0, 1.0),
    "price_stance": (0.0, 5.0), "loss_leader": (0.1, 1.0),
    "headcount_ambition": (-1.0, 5.0), "comp_offer": (0.0, None),
    "safety_spend": (0.0, 5.0),
    "capex_aggression": (0.0, 0.94), "power_lookahead": (1.0, 20.0),
    "lease_share": (0.0, 1.0),
    "raise_runway": (0.0, 120.0), "raise_fraction": (0.0, 0.5),
    "intel_spend": (0.0, 2.0),
    "openness": (0.0, 1.5),
}

_FIELDS = tuple(_BOUNDS) + ("mixture", "data_buy", "data_bids")


class Actions:
    """
    A lab's standing decisions for the month. Plain data; the world checks
    it in `World.apply` and refuses anything illegal.

      train / serve / experiment   the compute split, fractions summing to 1
      run_months                   wall-clock window the next run is sized to
      tokens_per_param, moe_sparsity, test_time_oom   the recipe
      mixture                      training mixture by domain, sums to 1
      ship_cooldown                months between landing a run and starting
                                   the next (the world adds its own jitter)
      chase_rate                   effort spent on the published numbers
      data_share                   fraction of a corpus taken when licensed
      data_buy                     one non-exclusive source to license, or None
      data_bids                    {source: ceiling} for this month's auctions
      price_stance, loss_leader    margin compression; deliberate sub-cost
      headcount_ambition           hiring appetite
      comp_offer                   $/researcher/yr actually offered
      safety_spend                 safety effort, in points bought per month
      capex_aggression             share of cash put into accelerators
      power_lookahead              megawatts contracted per megawatt in use
      lease_share                  of new power, the fraction leased not built
      raise_runway, raise_fraction when to raise, and how much to sell
      intel_spend                  effort narrowing the read on rivals
      openness                     how much of the work is published
    """

    __slots__ = _FIELDS

    def __init__(self, **kw):
        for f in _FIELDS:
            setattr(self, f, kw.get(f))

    def to_dict(self):
        out = {}
        for f in _FIELDS:
            v = getattr(self, f)
            if isinstance(v, dict):
                v = dict(v)
            out[f] = v
        return out

    def diff(self, other):
        """Fields on which this differs from `other` (None = everything)."""
        if other is None:
            return self.to_dict()
        out = {}
        for f in _FIELDS:
            a, b = getattr(self, f), getattr(other, f)
            if a != b:
                out[f] = dict(a) if isinstance(a, dict) else a
        return out

    def copy(self):
        return Actions(**self.to_dict())


def validate(actions):
    """Raise IllegalAction on anything the world will not accept."""
    for f, (lo, hi) in _BOUNDS.items():
        v = getattr(actions, f)
        if v is None:
            raise IllegalAction(f"{f} not set")
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise IllegalAction(f"{f} must be a number, got {v!r}")
        if math.isnan(v) or math.isinf(v):
            raise IllegalAction(f"{f} is {v}")
        if lo is not None and v < lo - 1e-9:
            raise IllegalAction(f"{f}={v} below {lo}")
        if hi is not None and v > hi + 1e-9:
            raise IllegalAction(f"{f}={v} above {hi}")
    tot = actions.train + actions.serve + actions.experiment
    if abs(tot - 1.0) > 1e-6:
        raise IllegalAction(f"compute split sums to {tot:.6f}, not 1")
    mix = actions.mixture
    if not isinstance(mix, dict) or not mix:
        raise IllegalAction("mixture must be a non-empty dict")
    for d, w in mix.items():
        if d not in D.DOMAIN_KEYS:
            raise IllegalAction(f"mixture names unknown domain {d!r}")
        if w < 0:
            raise IllegalAction(f"mixture[{d}] negative")
    if abs(sum(mix.values()) - 1.0) > 1e-6:
        raise IllegalAction(f"mixture sums to {sum(mix.values()):.6f}, not 1")
    if actions.data_buy is not None and actions.data_buy not in D.DATA_SOURCES:
        raise IllegalAction(f"data_buy names unknown source {actions.data_buy!r}")
    for key, price in (actions.data_bids or {}).items():
        if key not in D.DATA_SOURCES:
            raise IllegalAction(f"data_bids names unknown source {key!r}")
        if not D.DATA_SOURCES[key]["exclusive"]:
            raise IllegalAction(f"{key} is not exclusive; license it with data_buy")
        if price is None or price <= 0:
            raise IllegalAction(f"bid for {key} must be positive")


# ------------------------------------------------------------------- policy
class Policy:
    """
    Something that decides for a lab. Subclass and implement `decide`;
    override `decide_release` if the default (always ship) is wrong.
    """

    def decide(self, obs):
        raise NotImplementedError

    def decide_release(self, obs, candidate_cap, held):
        """
        A run has landed at `candidate_cap` (or a held model is being
        reconsidered, `held=True`). Return True to ship, False to sit on it.
        """
        return True


class DoctrinePolicy(Policy):
    """
    The eleven strategies, as policies. Reads the strategy's parameters and
    the lab's beliefs; writes actions. Reproduces the v1.3 inline behaviour
    exactly, spiral included.
    """

    def __init__(self, params):
        self.p = params

    # ---- helpers that used to live in world.py
    def _strategic_value(self, lab, source_key):
        """
        How much this corpus is worth to THIS lab: the overlap between what
        the source contains and what the lab is actually training for. A
        catalogue of stock footage is worth far more to a media specialist
        than to a generalist who would spend 7% of a run on it.
        """
        src = D.DATA_SOURCES[source_key]
        overlap = sum(lab.mixture.get(dom, 0.0) * w
                      for dom, w in src["mix"].items())
        return 1.0 + 7.0 * overlap

    def _data_buy(self, lab, month, share):
        """The one non-exclusive source to license this month, if any.
        Returns (key, price) or (None, 0.0)."""
        for key in self.p.get("data_priority", []):
            if key in lab.data.sources:
                continue
            src = D.DATA_SOURCES[key]
            if src["exclusive"]:
                continue
            if A.month_index(src["available"]) > month:
                continue
            tokens = src["volume"] * share
            price = (src["annual_cost"]
                     + src["one_off_cost_per_btok"] * tokens / 1e9)
            if price > lab.cash * 0.18:
                continue
            return key, price   # one deal a month; these take negotiating
        return None, 0.0

    def _data_bid(self, lab, cash, source_key, month, threat, share):
        """
        What this lab will pay for an exclusive licence, or None. `cash` is
        what is left after this month's licence, so a lab does not bid the
        same dollars twice.
        """
        if source_key in lab.data.sources:
            return None
        if source_key not in self.p.get("data_priority", []):
            return None
        src = D.DATA_SOURCES[source_key]
        if A.month_index(src["available"]) > month:
            return None
        ask = (src["annual_cost"]
               + src["one_off_cost_per_btok"] * src["volume"]
               * share / 1e9)
        if ask <= 0:
            return None
        # a licence is an annual commitment, not a lump of cash, so revenue
        # matters as much as the balance sheet
        budget = max(cash * 0.20, lab.arr * 0.18)
        # fear widens the wallet: a corpus looks cheaper when you believe a
        # rival is pulling away with something you cannot see
        panic = 1.0 + K.SPIRAL * K.THREAT_BID_GAIN * threat
        ceiling = min(budget, ask * self._strategic_value(lab, source_key) * panic)
        return ceiling if ceiling >= ask else None

    def decide(self, obs):
        p, lab, threat = self.p, obs.lab, obs.threat
        a = Actions()
        a.train = p["train"]
        a.serve = p["serve"]
        a.experiment = p["experiment"]
        # Wall-clock a lab is willing to spend. Competitive fear compresses
        # it: real labs threw more accelerators at a run to finish sooner,
        # because time-to-market is what they are racing on.
        window = p.get("run_months", 4.0)
        a.run_months = max(1.2, window - 0.8 * K.SPIRAL * threat)
        a.tokens_per_param = p.get("tokens_per_param", 20.0)
        a.moe_sparsity = p.get("moe_sparsity", 1.0)
        a.test_time_oom = p.get("test_time_oom", 0.0)
        a.mixture = dict(lab.mixture)
        # a lab that BELIEVES it is behind does not take a leisurely
        # cooldown, whether or not it actually is
        a.ship_cooldown = (p.get("ship_cooldown", 3)
                           - K.SPIRAL * K.THREAT_COOLDOWN_CUT * threat)
        a.chase_rate = p.get("chase_rate", 0.0)
        share = p.get("data_share", 0.6)
        a.data_share = share
        a.data_buy, spent = self._data_buy(lab, obs.month, share)
        cash = lab.cash - spent if a.data_buy else lab.cash
        bids = {}
        for key, src in D.DATA_SOURCES.items():
            if not src["exclusive"]:
                continue
            b = self._data_bid(lab, cash, key, obs.month, threat, share)
            if b:
                bids[key] = b
        a.data_bids = bids
        a.price_stance = p.get("price_stance", 1.0)
        a.loss_leader = p.get("loss_leader", 1.0)
        a.headcount_ambition = p.get("headcount_ambition", 1.0)
        # a lab that believes it is losing bids up for people
        a.comp_offer = obs.market_comp * p.get("comp_stance", 1.0) * (
            1.0 + K.SPIRAL * K.THREAT_COMP_GAIN * threat)
        a.safety_spend = p.get("safety_spend", 0.3)
        # Perceived deficit raises capex aggression. This is the spiral:
        # planning against the bad case means over-building, and the
        # over-building is itself the signal that worries everyone else.
        a.capex_aggression = min(0.94, p.get("capex_aggression", 0.5)
                                 * (1.0 + K.SPIRAL * K.THREAT_CAPEX_GAIN * threat))
        a.power_lookahead = p.get("power_lookahead", 5.0)
        a.lease_share = p.get("lease_share", 0.6)
        a.raise_runway = p.get("raise_runway", 14)
        a.raise_fraction = p.get("raise_fraction", 0.16)
        a.intel_spend = p.get("intel_spend", 0.25)
        a.openness = p.get("openness", 0.1)
        return a

    def decide_release(self, obs, candidate_cap, held):
        """
        Only the self-improvement racer declines to release on purpose:
        shipping hands rivals something to measure themselves against and to
        distill from, and the whole plan is to compound privately. It
        releases when the money runs short, or when it is behind and needs
        the revenue anyway.
        """
        p, lab = self.p, obs.lab
        if p.get("strategy") != "RSI":
            return True
        costs = max(getattr(lab, "last_costs", 1.0), 1.0)
        runway = lab.cash / costs
        if runway < p.get("hoard_runway", 20.0):
            return True                   # needs the revenue more than the secrecy
        # against what the lab BELIEVES the frontier is. A hoarder that thinks
        # a rival is closer than it really is releases earlier than it needed to.
        lead = candidate_cap - obs.perceived_frontier
        return not (lead > -p.get("hoard_lead", 0.25))


class ReplayPolicy(Policy):
    """
    Replays one lab's recorded decisions from a `World.action_log`. It never
    reads the doctrine and never looks at the observation, so a replayed
    game that matches the original bit for bit is proof that every decision
    went through the seam - nothing reached around it.

    Also what a saved game is: seed + log -> the same run.
    """

    def __init__(self, log, name):
        self.standing = []                  # [(month, diff)] in order
        self.releases = []                  # [ship: bool] in order
        for month, who, changed in log:
            if who != name:
                continue
            if "release" in changed:
                self.releases.append(changed["release"] == "ship")
            else:
                self.standing.append((month, changed))
        self._i = 0
        self._r = 0
        self._cur = None

    def decide(self, obs):
        while self._i < len(self.standing) and self.standing[self._i][0] <= obs.month:
            diff = self.standing[self._i][1]
            self._cur = Actions(**diff) if self._cur is None else self._cur.copy()
            for f, v in diff.items():
                setattr(self._cur, f, dict(v) if isinstance(v, dict) else v)
            self._i += 1
        if self._cur is None:
            raise IllegalAction(f"replay has no decisions by month {obs.month}")
        return self._cur.copy()

    def decide_release(self, obs, candidate_cap, held):
        if self._r >= len(self.releases):
            raise IllegalAction("replay ran out of release decisions")
        ship = self.releases[self._r]
        self._r += 1
        return ship
