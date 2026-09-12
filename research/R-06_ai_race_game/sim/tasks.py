"""
Benchmarks as samples of tasks.

The old model said `score = sigmoid(capability)`, which made a benchmark a
readout of one number rather than a measurement of anything. This module
replaces that with a structure that has room for the things that make real
benchmarks interesting.

    A model has a DIFFICULTY FRONTIER F, in OOM of effective compute.
    A task of difficulty d is solved with probability
        p(d) = sigmoid((F - d) / s)
    where s is elicitation softness - how well the lab gets its own model to
    actually perform, through scaffolding, prompting and tooling.

    A BENCHMARK is a distribution over task difficulty, N(mu, sigma), plus
    a fraction of items that are simply BROKEN - mislabelled, ambiguous, or
    unsolvable as graded. Its score is the expected fraction solved of the
    rest, plus a guessing floor. MMLU tops out near 92 not because models
    cannot do the tasks but because some of the answer key is wrong, and
    that is a property of the benchmark, so it lives in the benchmark.

Everything the old version hand-set now falls out:

- Saturation is automatic and per-suite. A suite runs out of hard tasks at
  its own point; no ceilings are configured anywhere.
- A harder suite is just a distribution with a higher mu. Retiring one and
  introducing another is a data change.
- Two labs at the same frontier can score differently, because elicitation
  differs. Scaffolding is worth something.
- Optimising for a suite raises the measured score without moving the
  frontier, which is a strategy the old model could not express.
"""
import math
from . import anchors as A

# Gauss-Hermite nodes and weights, 7-point, for E[f(d)] with d ~ N(mu, sigma).
_GH_X = [-2.651961356835233, -1.673551628767471, -0.8162878828589647, 0.0,
         0.8162878828589647, 1.673551628767471, 2.651961356835233]
_GH_W = [0.0009717812450995, 0.0545155828191270, 0.4256072526101278,
         0.8102646175568073, 0.4256072526101278, 0.0545155828191270,
         0.0009717812450995]
_SQRT_PI = math.sqrt(math.pi)


def _sig(x):
    if x < -40:
        return 0.0
    if x > 40:
        return 1.0
    return 1.0 / (1.0 + math.exp(-x))


def solved_fraction(frontier, mu, sigma, softness):
    """Expected fraction of a suite's tasks solved, by quadrature."""
    if sigma <= 1e-6:
        return _sig((frontier - mu) / max(softness, 1e-6))
    total = 0.0
    for x, w in zip(_GH_X, _GH_W):
        d = mu + math.sqrt(2.0) * sigma * x
        total += w * _sig((frontier - d) / max(softness, 1e-6))
    return total / _SQRT_PI


# ---------------------------------------------------------------- the suites
# mu/sigma are in OOM of effective compute. floor is the score a model that
# solves nothing still gets (multiple choice guessing).
# anchored: fitted to real reported scores. The rest are stated guesses.
SUITES = {
    # broken: fraction of items unsolvable as graded (label noise, ambiguity)
    "MMLU":  dict(domain="LANG",   floor=25.0, broken=0.080, anchored=True,
                  retired_when=0.90, label="Broad knowledge"),
    "GPQA":  dict(domain="REASON", floor=25.0, broken=0.050, anchored=True,
                  retired_when=0.90, label="Graduate science"),
    "SWE":   dict(domain="CODE",   floor=0.0,  broken=0.070, anchored=True,
                  retired_when=0.90, label="Real software issues"),
    "AGENT": dict(domain="AGENT",  floor=0.0,  broken=0.090, anchored=False,
                  mu=29.6, sigma=1.15, retired_when=0.90,
                  label="Long-horizon tasks"),
    "IMAGE": dict(domain="IMAGE",  floor=0.0,  broken=0.060, anchored=False,
                  mu=26.1, sigma=1.00, retired_when=0.90,
                  label="Image generation"),
    "VIDEO": dict(domain="VIDEO",  floor=0.0,  broken=0.080, anchored=False,
                  mu=28.0, sigma=0.95, retired_when=0.90,
                  label="Video generation"),
    "AUDIO": dict(domain="AUDIO",  floor=0.0,  broken=0.050, anchored=False,
                  mu=26.6, sigma=0.90, retired_when=0.90,
                  label="Speech & audio"),
    "ROBOT": dict(domain="ROBOT",  floor=0.0,  broken=0.110, anchored=False,
                  mu=29.8, sigma=1.20, retired_when=0.90,
                  label="Embodied control"),
}

# Successor suites: when a suite saturates, the field moves to a harder one.
# A lab that over-optimised for the retiring suite takes a visible fall.
SUCCESSORS = {
    "MMLU":  dict(mu_step=2.6, sigma=1.05, floor=25.0, label="Expert knowledge"),
    "GPQA":  dict(mu_step=2.4, sigma=1.00, floor=25.0, label="Research science"),
    "SWE":   dict(mu_step=2.5, sigma=1.10, floor=0.0,  label="Whole-system tasks"),
    "AGENT": dict(mu_step=2.4, sigma=1.20, floor=0.0,  label="Multi-week autonomy"),
    "IMAGE": dict(mu_step=2.2, sigma=1.00, floor=0.0,  label="Directed imagery"),
    "VIDEO": dict(mu_step=2.3, sigma=1.00, floor=0.0,  label="Long-form video"),
    "AUDIO": dict(mu_step=2.2, sigma=0.95, floor=0.0,  label="Full-duplex audio"),
    "ROBOT": dict(mu_step=2.5, sigma=1.25, floor=0.0,  label="Open-world manipulation"),
}

BASE_SOFTNESS = 0.42   # elicitation softness for a lab with no particular edge

# ------------------------------------------------------------- the AA index
# One number for "where is the frontier". Every suite underneath it
# saturates, so averaging raw scores would saturate too and stop telling you
# anything by 2027. Instead AA inverts each suite's score back to the
# DIFFICULTY it implies, averages those, and rescales - so the index keeps
# climbing as long as some suite still discriminates, and goes briefly blind
# when they all saturate at once and before harder ones arrive.
#
# Anchored so that 50 is a GPT-4-class model and 100 is a 2030-ish frontier.
# It is not capped at 100; a decade that runs hot goes past it.
AA_WEIGHTS = {"LANG": 0.18, "REASON": 0.22, "CODE": 0.22, "AGENT": 0.18,
              "IMAGE": 0.07, "VIDEO": 0.06, "AUDIO": 0.04, "ROBOT": 0.03}
AA_ANCHOR_FRONTIER = 26.50   # reads 50
AA_SCALE = 5.88              # points per OOM of difficulty

# Benchmarks are run, not computed: a given model's published score carries
# sampling and harness noise. Drawn once per shipped model, not per month -
# the number does not wobble between releases, it wobbles between them.
EVAL_NOISE_PTS = 1.6


class SuiteSet:
    """
    The suites currently in use, and the harder ones that replace them.

    A generation is a live measurement regime. When the field's best score on
    a suite passes its retirement threshold, the suite stops discriminating
    and a harder successor takes over - which is exactly what happened to
    MMLU, and why the scoreboard keeps resetting.
    """

    def __init__(self, fitted):
        self.gen = {k: 0 for k in SUITES}
        self.mu = {}
        self.sigma = {}
        self.floor = {}
        self.broken = {}
        self.label = {}
        for k, spec in SUITES.items():
            if spec["anchored"]:
                self.mu[k], self.sigma[k], self.broken[k] = fitted[k]
            else:
                self.mu[k], self.sigma[k] = spec["mu"], spec["sigma"]
                self.broken[k] = spec["broken"]
            self.floor[k] = spec["floor"]
            self.label[k] = spec["label"]
        self.retirements = []

    def score(self, suite, frontier, softness=BASE_SOFTNESS, chase=0.0):
        """
        Published score on a suite. `chase` is suite-specific optimisation:
        it lifts the measured number without moving the frontier.
        """
        f = frontier + chase
        frac = solved_fraction(f, self.mu[suite], self.sigma[suite], softness)
        frac *= (1.0 - self.broken[suite])
        lo = self.floor[suite]
        return lo + (100.0 - lo) * frac

    def maybe_retire(self, suite, best_score, month):
        """Retire a saturated suite in favour of a harder one."""
        spec = SUITES[suite]
        # Measure against what is ACHIEVABLE, not against 100. A suite whose
        # answer key is 15% wrong tops out at 85% and would otherwise never
        # be declared saturated - which is exactly the mistake that keeps a
        # dead benchmark on the scoreboard for years.
        frac = (best_score - self.floor[suite]) / max(100.0 - self.floor[suite], 1e-6)
        achievable = max(1.0 - self.broken[suite], 1e-6)
        if frac / achievable < spec["retired_when"]:
            return None
        succ = SUCCESSORS[suite]
        self.gen[suite] += 1
        self.mu[suite] += succ["mu_step"]
        self.sigma[suite] = succ["sigma"]
        self.floor[suite] = succ["floor"]
        self.broken[suite] = SUITES[suite]["broken"]
        self.label[suite] = succ["label"] + (
            "" if self.gen[suite] == 1 else f" v{self.gen[suite]}")
        self.retirements.append((month, suite, self.label[suite]))
        return self.label[suite]


def implied_frontier(suiteset, suite, score, softness=BASE_SOFTNESS):
    """
    Invert a published score back to the task difficulty it implies.
    Monotone in the frontier, so bisection. Returns None where the suite has
    stopped discriminating - at the floor or at its achievable ceiling there
    is no information left to invert.
    """
    lo_f = suiteset.floor[suite]
    achievable = max(1.0 - suiteset.broken[suite], 1e-6)
    frac = (score - lo_f) / max(100.0 - lo_f, 1e-6) / achievable
    if frac <= 0.03 or frac >= 0.97:
        return None
    lo, hi = 15.0, 45.0
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if solved_fraction(mid, suiteset.mu[suite], suiteset.sigma[suite],
                           softness) < frac:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def aggregate_index(suiteset, scores, softness=BASE_SOFTNESS):
    """
    The AA index for one lab, from its published scores.

    Returns (aa, coverage, blind) where coverage is the share of the index's
    weight this lab is actually measurable on - a media specialist scores
    well on the suites it enters and covers little of the index - and blind
    is the share of weight where the suite has saturated and carries no
    information.
    """
    tot_w, acc_w, blind_w, acc = 0.0, 0.0, 0.0, 0.0
    for dom, w in AA_WEIGHTS.items():
        tot_w += w
        suite = DOMAIN_SUITE.get(dom)
        sc = scores.get(dom)
        if sc is None or sc <= 0:
            continue
        f = implied_frontier(suiteset, suite, sc, softness)
        if f is None:
            blind_w += w
            continue
        acc += w * f
        acc_w += w
    if acc_w <= 0:
        return None, 0.0, blind_w / tot_w if tot_w else 0.0
    mean_f = acc / acc_w
    aa = 50.0 + (mean_f - AA_ANCHOR_FRONTIER) * AA_SCALE
    return aa, acc_w / tot_w, blind_w / tot_w


DOMAIN_SUITE = {spec["domain"]: k for k, spec in SUITES.items()}


def fit_anchored(frontier_history, verbose=False):
    """
    Fit mu, sigma and the broken fraction per anchored suite against the
    reported scores. Three parameters that mean something: where a suite's
    tasks sit, how spread out they are, and how much of it is unwinnable.

    CAVEAT, stated because it matters: the fitted broken fractions come out
    around 0.15-0.18, well above published label-noise estimates of roughly
    0.05-0.08. So the parameter is absorbing something besides broken items -
    most likely that the capability track runs a little hot in the late
    period, where the anchors are also weakest. Do not read the fitted value
    as a measurement of label noise.
    """
    from .capability import DOMAIN_OF_SUITE, CONF_WEIGHT
    out = {}
    for suite in ("MMLU", "GPQA", "SWE"):
        dom = DOMAIN_OF_SUITE[suite]
        pts = []
        for date, s, score, _model, conf in A.BENCHMARKS:
            if s != suite:
                continue
            m = A.month_index(date)
            pts.append((frontier_history.domain_capability_at(m, dom),
                        score, CONF_WEIGHT[conf]))
        lo = SUITES[suite]["floor"]
        best, bestp = None, None
        for i in range(61):
            mu = 22.0 + i * 0.2
            for j in range(41):
                sg = 0.3 + j * 0.08
                for k in range(26):
                    br = k * 0.012
                    sse = 0.0
                    for f, y, w in pts:
                        frac = solved_fraction(f, mu, sg, BASE_SOFTNESS) * (1 - br)
                        sse += w * (lo + (100.0 - lo) * frac - y) ** 2
                    if best is None or sse < best:
                        best, bestp = sse, (mu, sg, br)
        out[suite] = bestp
        if verbose:
            rmse = math.sqrt(best / sum(p[2] for p in pts))
            print(f"  {suite:6s} tasks at difficulty {bestp[0]:6.2f} OOM, "
                  f"spread {bestp[1]:4.2f}, {bestp[2]*100:4.1f}% unwinnable"
                  f"   weighted RMSE {rmse:4.2f} pts")
    return out
