"""
What a lab can see, and what it does about what it cannot.

Until now every actor read the world's true state. That made half the
mechanics decorative: benchmark-chasing only matters if rivals cannot see
your real frontier, and hoarding only works if nobody knows what you have.
The AI opponents were implicitly cheating.

This module puts a boundary in. A lab observes SIGNALS and forms BELIEFS
with error bars, and its decisions read the beliefs.

The reason this matters beyond bookkeeping is the thing it produces.
Private information plus an incentive to misrepresent is the classic
bargaining-failure setup: you cannot see a rival's true position, you know
they benefit from you misjudging it, so you price in the bad case. Pricing
in the bad case means over-building. Your over-building is a signal to them,
and they price in their bad case. Nobody is irrational and the whole field
ends up spending more than any of them would choose against known rivals.

So the model needs two things that are not the same:

    what is true            - lab.model.caps, lab.internal, lab.cash
    what O believes about T  - a point estimate and a sigma, per domain

and a third that is neither: THREAT, which is what a lab acts on. Threat is
deliberately biased pessimistic, by a per-strategy paranoia, because that is
how decisions actually get made under this kind of uncertainty.

## What is visible

    Public          published benchmark scores and AA, prices, announced
                    products, funding rounds and valuations
    Inferable       fleet scale and power siting (noisy, lagged), headcount,
                    how long it has been since they shipped anything
    Private         true difficulty frontier, unreleased models, cash and
                    runway, training mixture, research pipeline

The cross-check is the interesting part. A hoarder looks weak on the
scoreboard and its power footprint says otherwise. A chaser looks strong on
the scoreboard and its footprint does not justify it. A lab that reads both
signals is harder to fool than one reading either.
"""
import math
from . import constants as K
from . import tasks as TASKS


class Belief:
    """One lab's read on one rival, this month."""

    __slots__ = ("target", "pub_cap", "scale", "compute", "months_silent",
                 "latent_est", "sigma", "aa", "price")

    def __init__(self, target):
        self.target = target
        self.pub_cap = {}        # per-domain frontier implied by published scores
        self.scale = 0.0         # estimated accelerators
        self.compute = 0.0       # estimated training FLOP/s of that fleet
        self.months_silent = 0
        self.latent_est = 0.0    # best guess at their true best, released or not
        self.sigma = K.INTEL_BASE_SIGMA
        self.aa = None
        self.price = 0.0

    def upper(self, paranoia):
        """The number a worried competitor actually plans against."""
        return self.latent_est + paranoia * self.sigma


def observe(observer, target, world, month):
    """Build observer's belief about target from what is actually visible."""
    b = Belief(target.name)
    if not target.model:
        return b

    # --- public: the scoreboard. Carries their chasing and eval noise, which
    # is the point: you are reading a number they had reasons to inflate.
    scores = world.published_scores(target)
    for dom, sc in scores.items():
        suite = TASKS.DOMAIN_SUITE.get(dom)
        if suite is None:
            continue
        f = TASKS.implied_frontier(world.suites, suite, sc,
                                   softness=TASKS.BASE_SOFTNESS)
        if f is not None:
            b.pub_cap[dom] = f
    b.aa = world.aa(target)[0]
    b.price = target.price_per_mtok

    # --- inferable: iron and power are hard to hide, but not easy to count
    intel = observer.actions.intel_spend
    obs_noise = K.SCALE_OBS_NOISE / (1.0 + K.INTEL_SPEND_EFFECT * intel * 3.0)
    true_scale = max(target.fleet.count(), 1)
    seen = 10 ** observer.rng_intel.gauss(0.0, obs_noise)
    b.scale = true_scale * seen
    # power siting and shipments tell you the generation as well as the
    # count; the same read, in FLOP/s
    b.compute = target.fleet.train_flops() * seen

    b.months_silent = month - (target.model.shipped if target.model else 0)

    # --- the inference: what might they have that they have not shown?
    # Silence plus growing compute is the signature of a lab sitting on
    # something. It is also the signature of a lab that is simply stuck,
    # and from outside those look identical - which is the whole problem.
    pub_best = max(b.pub_cap.values()) if b.pub_cap else 0.0
    silence_yrs = b.months_silent / 12.0
    scale_growth = math.log10(max(b.scale, 1) / max(target.scale_at_release, 1))
    hidden = min(K.LATENT_MAX,
                 K.LATENT_FROM_SILENCE * silence_yrs
                 + K.LATENT_FROM_SCALE * min(1.0, max(0.0, scale_growth)))
    b.latent_est = pub_best + hidden

    # --- how sure are we? Less, the longer they have been quiet.
    b.sigma = (K.INTEL_BASE_SIGMA + K.INTEL_STALENESS * silence_yrs) \
        / (1.0 + K.INTEL_SPEND_EFFECT * intel * 2.0)
    return b


def threat(observer, beliefs, own_best):
    """
    How far behind this lab believes it is, planning against the bad case.

    Returns (perceived_deficit, who_they_fear). Deficit is in OOM and is
    clamped at zero below - a lab that believes it leads feels no threat,
    even if it is wrong about leading.
    """
    par = observer.doctrine.get("paranoia", K.PARANOIA_DEFAULT)
    worst, who = 0.0, None
    # a lab that has not landed anything yet is not behind anyone - it has
    # not entered. (Before v1.14 own_best = 0 read as 23 OOM behind, which
    # compressed its first run to the minimum window and inflated its
    # capex and comp - masked while every lab started on day one.)
    if own_best <= 0:
        return 0.0, None
    for b in beliefs:
        d = b.upper(par) - own_best
        if d > worst:
            worst, who = d, b.target
    return worst, who


def perceived_frontier(beliefs, paranoia):
    """The frontier as this lab believes it to be, pessimistically."""
    if not beliefs:
        return 0.0
    return max(b.upper(paranoia) for b in beliefs)


def believed_frontier(beliefs):
    """The frontier as this lab's best guess has it - the central estimate,
    no paranoia. What a lab measures a finished run against."""
    if not beliefs:
        return 0.0
    return max(b.latent_est for b in beliefs)
