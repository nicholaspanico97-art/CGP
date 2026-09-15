"""
The world economy: four blocs, and demand as a labour market.

v1.11: OBSERVED, NOT ACTING. Each bloc's economy steps monthly on its
trend, reads the AI sector (the best capability on sale, realised
revenue, incidents) and computes what the labour-market demand model
would say - automatable share, value unlocked, realised spend with
adoption friction, displacement, productivity - beside the capability
curve that still sets sector spend (World._sector_spend). ECONOMY.md.

Nothing here draws randomness. Nothing here changes a lab's outcome.
"""
import math
from . import constants as K

BLOCS = ("US", "EU", "China", "RoW")

# ------------------------------------------------------------ the record
INITIAL = {
    "US":    dict(gdp=21.1e12, trend=0.020, workforce=160e6, knowledge_share=0.38,
                  wage_bill=6.3e12, software_spend=1.2e12, unemployment=0.035,
                  ent_halflife=14.0, con_halflife=3.0),
    "EU":    dict(gdp=15.3e12, trend=0.013, workforce=200e6, knowledge_share=0.35,
                  wage_bill=4.1e12, software_spend=0.6e12, unemployment=0.075,
                  ent_halflife=20.0, con_halflife=4.0),
    "China": dict(gdp=14.7e12, trend=0.050, workforce=780e6, knowledge_share=0.18,
                  wage_bill=2.2e12, software_spend=0.4e12, unemployment=0.052,
                  ent_halflife=12.0, con_halflife=3.0),
    "RoW":   dict(gdp=34.0e12, trend=0.035, workforce=2300e6, knowledge_share=0.15,
                  wage_bill=5.1e12, software_spend=0.8e12, unemployment=0.060,
                  ent_halflife=24.0, con_halflife=5.0),
}

# task tiers of knowledge work: share, half-point on the score scale, width
TIERS = [
    ("routine",  0.30, 105.0,  8.0),
    ("analysis", 0.30, 118.0,  9.0),
    ("agentic",  0.25, 130.0, 10.0),
    ("expert",   0.15, 150.0, 12.0),
]
CAPTURE_0, CAPTURE_1, CAPTURE_HALFLIFE_M = 0.06, 0.20, 36.0   # of value saved
# a task the model can do acceptably is not a task a firm has deployed:
# reliability, integration and liability gate it. Sigmoid in the score.
DEPLOY_HALF, DEPLOY_WIDTH = 135.0, 10.0
PRODUCTIVITY_MULT = 2.0            # value created per dollar of AI bought;
                                   # growth comes from the INCREASE in it
REEMPLOYMENT = 0.85                # share of displaced hours re-absorbed
DISPLACEMENT_LAG_M = 12
EXPANSION_PER_OOM_CHEAPER = 0.35   # addressable work grows as $/task falls

CAP_REF = 26.5                     # GPT-4-class in log-FLOP; score 100


def score(c):
    return (c - CAP_REF) * 10.0 + 100.0


def deployable(c_score):
    x = (c_score - DEPLOY_HALF) / DEPLOY_WIDTH
    return 1.0 / (1.0 + math.exp(-x)) if -40 < x < 40 else (0.0 if x <= -40 else 1.0)


def automatable(c_score):
    """Fraction of knowledge-work tasks a model at this score can do."""
    tot = 0.0
    for _n, share, half, width in TIERS:
        x = (c_score - half) / width
        s = 1.0 / (1.0 + math.exp(-x)) if -40 < x < 40 else (0.0 if x <= -40 else 1.0)
        tot += share * s
    return tot


def tier_shares(c_score):
    out = {}
    for n, share, half, width in TIERS:
        x = (c_score - half) / width
        out[n] = 1.0 / (1.0 + math.exp(-x)) if -40 < x < 40 else (0.0 if x <= -40 else 1.0)
    return out


class Bloc:
    def __init__(self, name, p):
        self.name = name
        self.gdp = p["gdp"]
        self.trend = p["trend"]
        self.workforce = p["workforce"]
        self.knowledge_share = p["knowledge_share"]
        self.wage_bill = p["wage_bill"]
        self.software_spend = p["software_spend"]
        self.unemployment = p["unemployment"]
        self.unemployment_0 = p["unemployment"]
        self.ent_halflife = p["ent_halflife"]
        self.con_halflife = p["con_halflife"]
        self.realised_con = 0.0        # $/yr realised, consumer-type
        self.realised_ent = 0.0        # $/yr realised, enterprise-type
        self.displaced_hours = 0.0     # share of knowledge hours automated (lagged)
        self.displaced_queue = []
        self.productivity_lift = 0.0   # extra growth this year, from AI
        self.growth = self.trend
        self.realised_hist = []

    def step(self, m, c_score, price_per_task_rel):
        year = 2020 + m // 12
        if self.name == "China" and year >= 2023:
            self.trend = 0.040
        # what AI could do, and what buyers would pay for it
        auto = automatable(c_score)
        expansion = 1.0 + EXPANSION_PER_OOM_CHEAPER * max(0.0, -math.log10(max(price_per_task_rel, 1e-6)))
        capture = CAPTURE_1 + (CAPTURE_0 - CAPTURE_1) * 0.5 ** (m / CAPTURE_HALFLIFE_M)
        dep = deployable(c_score)
        unlocked = auto * dep * self.wage_bill * capture * expansion
        # split: routine tier is consumer-and-API-like, the rest enterprise
        ts = tier_shares(c_score)
        con_w = 0.30 * ts["routine"]
        ent_w = 0.30 * ts["analysis"] + 0.25 * ts["agentic"] + 0.15 * ts["expert"]
        tot_w = max(con_w + ent_w, 1e-9)
        unl_con, unl_ent = unlocked * con_w / tot_w, unlocked * ent_w / tot_w
        kc = 1 - 0.5 ** (1.0 / self.con_halflife)
        ke = 1 - 0.5 ** (1.0 / self.ent_halflife)
        self.realised_con += (unl_con - self.realised_con) * kc
        self.realised_ent += (unl_ent - self.realised_ent) * ke
        realised = self.realised_con + self.realised_ent
        # feedback: productivity (from the year-on-year increase in value
        # bought - a level of spend adds a level of output once),
        # displacement (lagged), the economy's trend
        self.realised_hist.append(realised)
        prev = self.realised_hist[-13] if len(self.realised_hist) > 12 else 0.0
        self.productivity_lift = PRODUCTIVITY_MULT * max(0.0, realised - prev) / self.gdp
        hours_now = auto * dep * capture * 2.0    # hours automated, as a share of knowledge hours
        self.displaced_queue.append(hours_now)
        if len(self.displaced_queue) > DISPLACEMENT_LAG_M:
            self.displaced_hours = self.displaced_queue.pop(0)
        knowledge_jobs = self.workforce * self.knowledge_share
        displaced_jobs = self.displaced_hours * (1 - REEMPLOYMENT) * knowledge_jobs
        self.unemployment = self.unemployment_0 + displaced_jobs / self.workforce
        self.growth = self.trend + self.productivity_lift
        g = (1 + self.growth) ** (1 / 12)
        self.gdp *= g
        self.wage_bill *= g
        self.software_spend *= (1 + self.trend + 0.03) ** (1 / 12)
        return dict(automatable=auto, deployable=dep, unlocked=unlocked, realised=realised,
                    realised_con=self.realised_con, realised_ent=self.realised_ent,
                    capture=capture, expansion=expansion)


class Economy:
    def __init__(self):
        self.blocs = {b: Bloc(b, p) for b, p in INITIAL.items()}
        self.month = 0
        self.last = {}
        self.history = []

    def step(self, world):
        m = world.month
        self.month = m
        best_lang = max((l.model.caps.get("LANG", 0.0) for l in world.labs if l.model), default=0.0)
        best_agent = max((l.model.caps.get("AGENT", 0.0) for l in world.labs if l.model), default=0.0)
        c = max(best_lang, 0.0)
        c_score = score(c) if c > 0 else 0.0
        # price per task relative to 2023 (cost per Mtok falls with hardware)
        prices = [l.price_per_mtok for l in world.labs if l.model and l.price_per_mtok > 0]
        p_rel = (min(prices) / 20.0) if prices else 1.0
        out = {}
        for b in self.blocs.values():
            out[b.name] = b.step(m, c_score, p_rel)
        self.last = dict(
            c_score=c_score, agent_score=score(best_agent) if best_agent > 0 else 0.0,
            tiers=tier_shares(c_score) if c_score > 0 else {n: 0.0 for n, *_ in TIERS},
            per_bloc=out,
            labour_spend=sum(o["realised"] for o in out.values()),
            capability_spend=getattr(world, "spend_stock", 0.0),
            sector_revenue=sum(getattr(l, "arr", 0.0) for l in world.labs),
        )
        self.history.append(self.snapshot())

    def snapshot(self):
        return dict(month=self.month, **self.last,
                    blocs={b.name: dict(gdp=b.gdp, growth=b.growth, trend=b.trend,
                                        wage_bill=b.wage_bill, software_spend=b.software_spend,
                                        unemployment=b.unemployment, unemployment_0=b.unemployment_0,
                                        displaced_hours=b.displaced_hours,
                                        productivity_lift=b.productivity_lift,
                                        realised=b.realised_con + b.realised_ent,
                                        ai_share_software=((b.realised_con + b.realised_ent) / b.software_spend))
                           for b in self.blocs.values()})
