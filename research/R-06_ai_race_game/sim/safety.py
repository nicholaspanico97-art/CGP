"""
Incidents.

`safety_debt` used to accumulate and do nothing, which meant shipping
without evaluating was strictly free. Every strategy should have done it,
and a player would have found that out in three turns.

Two things decide what happens here, and keeping them separate is the whole
design:

    HOW OFTEN        safety debt, how much you have deployed, and how big a
                     capability jump you shipped without properly evaluating

    HOW BAD          what your models can actually DO in the world

The second is the one that matters. A glorified chat assistant that
misbehaves is a news cycle. The same misalignment in a system that books
travel, runs shell commands and calls APIs on its own is an economic event.
In something with real autonomy over real infrastructure it is a body count.
So severity is gated on AGENT capability and on how much agentic product is
actually deployed - not on how sloppy the lab is. Sloppiness changes the
odds; capability changes the ceiling.

Three tiers. Catastrophic, world-ending outcomes are deliberately out of
scope for now.

    MINOR     anomalous behaviour, embarrassing, makes the news
    MODERATE  agents reach something they should not - a service defaced, a
              system compromised, money lost
    SEVERE    real-world consequence through action: infrastructure, medical
              systems, physical harm. The sector gets regulated after one.
"""
import math
from . import constants as K

MINOR, MODERATE, SEVERE = "minor", "moderate", "severe"

DESCRIPTIONS = {
    MINOR: [
        "a model output an internal prompt to users",
        "an assistant confidently invented a recall notice",
        "a jailbreak thread trends for a week",
        "a model refused a whole category of lawful requests",
        "an evaluation result turned out not to reproduce",
    ],
    MODERATE: [
        "an agent exfiltrated a customer's credentials to a pastebin",
        "an autonomous coding agent force-pushed over a client's repository",
        "an agent chained third-party APIs to place unauthorised orders",
        "a deployed agent defaced a public web service",
        "an agent's tool use drained a customer's cloud budget overnight",
    ],
    SEVERE: [
        "an agent reached a utility's operational network",
        "a hospital scheduling system was compromised through a deployed agent",
        "an agent acting on a user's instruction disabled building safety systems",
        "an autonomous system caused a physical-plant failure",
        "an agent manipulated a logistics network serving medical supply",
    ],
}


def harm_potential(lab):
    """
    How bad the worst case is, given what this lab's models can DO.

    Keyed on agentic capability, because real-world harm requires something
    that acts. A lab at the frontier of language and nowhere near agency has
    a low ceiling no matter how careless it is.
    """
    if not lab.model or not lab.model.caps:
        return 0.0
    agent = lab.model.caps.get("AGENT", 0.0)
    if agent <= 0:
        return 0.0
    x = (agent - K.HARM_FLOOR) / max(K.HARM_CEILING - K.HARM_FLOOR, 1e-6)
    return max(0.0, min(1.0, x))


def agentic_exposure(lab):
    """Share of revenue coming from products that act rather than answer."""
    rev = sum(lab.seg_revenue.values())
    if rev <= 0:
        return 0.0
    acting = (lab.seg_revenue.get("enterprise_agents", 0.0)
              + lab.seg_revenue.get("coding", 0.0) * 0.6
              + lab.seg_revenue.get("robotics", 0.0))
    return max(0.0, min(1.0, acting / rev))


def incident_probability(lab, month):
    """
    Monthly odds that something goes wrong, before severity is drawn.

    Deployment surface is the exposure: a model nobody uses cannot embarrass
    you. The capability jump term is the real driver - shipping a big
    increase without evaluating it is where surprises live.
    """
    if not lab.model:
        return 0.0
    surface = math.log10(1.0 + getattr(lab, "served_mtok", 0.0) / 1e4)
    jump = max(0.0, lab.model.capability - getattr(lab, "evaluated_at", 0.0))
    debt = max(0.0, lab.safety_debt)
    p = (K.INCIDENT_BASE
         * (0.35 + surface)
         * (1.0 + K.INCIDENT_JUMP_GAIN * jump)
         * (1.0 + K.INCIDENT_DEBT_GAIN * debt))
    return min(0.5, p)


def draw_severity(rng, lab):
    """
    Given that something went wrong, how bad is it?

    Minor is always on the table. Moderate needs enough capability to reach
    past the chat window. Severe needs real agentic capability AND agentic
    deployment - you cannot take down a grid with a product nobody has
    pointed at anything.
    """
    h = harm_potential(lab)
    exposure = agentic_exposure(lab)
    sloppy = 1.0 + 0.06 * max(0.0, lab.safety_debt)

    w_minor = 1.0
    w_moderate = (0.10 + 1.25 * h) * sloppy
    w_severe = (K.SEVERE_SCALE * (h ** 2) * (0.20 + 0.80 * exposure)) * sloppy

    total = w_minor + w_moderate + w_severe
    r = rng.random() * total
    if r < w_minor:
        return MINOR
    if r < w_minor + w_moderate:
        return MODERATE
    return SEVERE


def apply_incident(lab, world, severity, month, rng):
    """Consequences. Returns a record for the log."""
    rev_month = max(lab.revenue_m, 0.0)
    text = rng.choice(DESCRIPTIONS[severity])

    if severity == MINOR:
        lab.trust = max(5.0, lab.trust - K.MINOR_TRUST)
        cost = 0.0
        lab.safety_debt = max(0.0, lab.safety_debt - 0.5)
    elif severity == MODERATE:
        lab.trust = max(5.0, lab.trust - K.MODERATE_TRUST)
        cost = rev_month * K.MODERATE_REVENUE_COST + K.MODERATE_FIXED
        lab.cash -= cost
        lab.legal_exposure = getattr(lab, "legal_exposure", 0.0) + 1.0
        lab.safety_debt = max(0.0, lab.safety_debt - 1.0)
    else:
        lab.trust = max(5.0, lab.trust - K.SEVERE_TRUST)
        cost = rev_month * K.SEVERE_REVENUE_COST + K.SEVERE_FIXED
        lab.cash -= cost
        lab.legal_exposure = getattr(lab, "legal_exposure", 0.0) + 3.0
        # the offending lab is restricted from agentic deployment for a while
        lab.deploy_restricted_until = month + K.SEVERE_RESTRICT_MONTHS
        lab.safety_debt = max(0.0, lab.safety_debt - 2.0)
        # and the whole sector gets regulated
        world.regulation += K.SEVERE_REGULATION_STEP

    rec = dict(month=month, lab=lab.name, severity=severity, text=text,
               cost=cost, trust_after=round(lab.trust, 1))
    lab.incidents.append(rec)
    world.incident_log.append(rec)
    return rec
