"""
Strategies.

A lab is not a parameter bundle, it is a set of intentions. Each strategy
below answers the same questions differently: what is compute for, when is a
model worth releasing, what is a fair price, whose data matters, and what
does winning even mean. Two labs with identical resources and different
strategies produce visibly different charts.

Every game draws a strategy per lab, with variation inside each strategy, so
the same archetype is never quite the same twice. The player is not told who
is running what - it has to be inferred from what they ship, what they
charge, and what they are visibly not doing.

The load-bearing idea is that some of these deliberately decline to ship.
A lab racing for self-improving research does not want to hand rivals a
target to distill, so it sits on capability until it needs the money - and
while it sits, the open-weights lab it is racing cannot catch up by copying.
"""
import math


def _u(rng, lo, hi):
    return lo + (hi - lo) * rng.random()


# Each entry: base parameters, per-game variation ranges, and an `openness`
# contribution - how much this lab's existence speeds everyone else up.
STRATEGIES = {
    "SCALE": dict(
        name="Scale maximalist",
        blurb="Compute above all. Biggest runs in the field, ships when it has "
              "something, terrible margins, terrifying by the late game.",
        base=dict(train=0.60, serve=0.24, experiment=0.16, tokens_per_param=20,
                  moe_sparsity=2.0, run_months=5.0, ship_cooldown=7,
                  capex_aggression=0.70, supply_share=0.24, price_stance=1.0,
                  power_lookahead=7.5, comp_stance=1.05, openness=0.10,
                  story_cap_gain=0.62,
                  elicitation=0.52, chase_rate=0.35,
                  paranoia=1.15, intel_spend=0.3,
                  safety_spend=0.15, eval_rate=0.35),
        vary=dict(train=(0.54, 0.66), run_months=(4.0, 6.5),
                  capex_aggression=(0.62, 0.80), ship_cooldown=(5, 9)),
        mixture={"LANG": .52, "REASON": .20, "CODE": .21, "AGENT": .07},
        data=["web_crawl", "code_repos", "books_papers", "expert_annotation"]),

    "RSI": dict(
        name="Self-improvement racer",
        blurb="Points compute at its own research and hoards what it learns. "
              "Ships rarely and late - releasing only hands rivals something "
              "to copy. Quiet for years, then not quiet.",
        base=dict(train=0.44, serve=0.18, experiment=0.38, tokens_per_param=25,
                  moe_sparsity=4.0, run_months=5.5, ship_cooldown=9,
                  capex_aggression=0.72, supply_share=0.22, price_stance=1.35,
                  power_lookahead=8.0, comp_stance=1.25, openness=0.02,
                  story_cap_gain=0.66,
                  hoard_runway=9.0, hoard_lead=0.25, raise_runway=30.0,
                  elicitation=0.48, chase_rate=0.0,
                  paranoia=1.3, intel_spend=0.15,
                  safety_spend=0.45, eval_rate=0.55),
        vary=dict(experiment=(0.30, 0.46), hoard_runway=(6.0, 14.0),
                  hoard_lead=(0.12, 0.45), ship_cooldown=(7, 12)),
        mixture={"LANG": .34, "REASON": .30, "CODE": .24, "AGENT": .12},
        data=["web_crawl", "code_repos", "books_papers", "expert_annotation"]),

    "COST": dict(
        name="Efficiency leader",
        blurb="Wins on dollars per million tokens, not on benchmarks. "
              "Overtrains small sparse models that are cheap forever after, "
              "and prices where nobody else can follow.",
        base=dict(train=0.36, serve=0.50, experiment=0.14, tokens_per_param=140,
                  moe_sparsity=8.0, run_months=3.0, ship_cooldown=5,
                  capex_aggression=0.52, supply_share=0.14, price_stance=0.45,
                  power_lookahead=5.5, comp_stance=0.90, openness=0.15,
                  story_cap_gain=0.12,
                  elicitation=0.3, chase_rate=0.55,
                  paranoia=0.55, intel_spend=0.3,
                  safety_spend=0.25, eval_rate=0.45),
        vary=dict(tokens_per_param=(90, 200), price_stance=(0.35, 0.58),
                  serve=(0.44, 0.56)),
        mixture={"LANG": .55, "REASON": .14, "CODE": .26, "AGENT": .05},
        data=["web_crawl", "code_repos", "books_papers"]),

    "OPEN": dict(
        name="Open weights",
        blurb="Publishes everything. Collapses the price floor, lifts the "
              "whole field's efficiency, and monetises attention and "
              "services rather than access.",
        base=dict(train=0.50, serve=0.30, experiment=0.20, tokens_per_param=90,
                  moe_sparsity=3.0, run_months=3.5, ship_cooldown=5,
                  capex_aggression=0.48, supply_share=0.12, price_stance=0.55,
                  power_lookahead=5.0, comp_stance=0.85, openness=1.00,
                  elicitation=0.32, chase_rate=0.3,
                  paranoia=0.45, intel_spend=0.2,
                  safety_spend=0.4, eval_rate=0.6),
        vary=dict(openness=(0.75, 1.25), train=(0.44, 0.56),
                  price_stance=(0.42, 0.70)),
        mixture={"LANG": .48, "REASON": .16, "CODE": .30, "AGENT": .06},
        data=["web_crawl", "code_repos", "books_papers", "simulation"]),

    "VERTICAL": dict(
        name="Vertical specialist",
        blurb="Picks one thing and is the best in the world at it. Invisible "
              "in every other market, and untouchable in its own.",
        base=dict(train=0.42, serve=0.44, experiment=0.14, tokens_per_param=55,
                  moe_sparsity=2.5, run_months=3.5, ship_cooldown=6,
                  capex_aggression=0.50, supply_share=0.09, price_stance=1.1,
                  power_lookahead=5.0, comp_stance=0.95, openness=0.08,
                  elicitation=0.3, chase_rate=0.25,
                  paranoia=0.6, intel_spend=0.25,
                  safety_spend=0.35, eval_rate=0.55),
        vary=dict(serve=(0.38, 0.50), price_stance=(0.9, 1.35)),
        mixture=None,      # drawn from FOCUS below
        data=None),

    "ENTERPRISE": dict(
        name="Enterprise & trust",
        blurb="Slow, careful, expensive, and the one everyone's compliance "
              "department will actually sign off on. Always evaluates.",
        base=dict(train=0.42, serve=0.42, experiment=0.16, tokens_per_param=40,
                  moe_sparsity=3.0, run_months=4.0, ship_cooldown=8,
                  capex_aggression=0.54, supply_share=0.14, price_stance=1.30,
                  power_lookahead=6.0, comp_stance=1.10, openness=0.20,
                  always_eval=True,
                  elicitation=0.28, chase_rate=0.1,
                  paranoia=0.5, intel_spend=0.35,
                  safety_spend=0.85, eval_rate=0.95),
        vary=dict(price_stance=(1.15, 1.50), ship_cooldown=(7, 11)),
        mixture={"LANG": .42, "REASON": .28, "CODE": .22, "AGENT": .08},
        data=["web_crawl", "books_papers", "code_repos", "expert_annotation",
              "news_archive"]),

    "CONSUMER": dict(
        name="Consumer land grab",
        blurb="Distribution first, economics later. Prices below cost to own "
              "the default, and bets the losses are worth the habit.",
        base=dict(train=0.32, serve=0.56, experiment=0.12, tokens_per_param=70,
                  moe_sparsity=5.0, run_months=3.0, ship_cooldown=5,
                  capex_aggression=0.60, supply_share=0.18, price_stance=0.60,
                  power_lookahead=6.5, comp_stance=1.0, openness=0.12,
                  loss_leader=0.72, story_cap_gain=0.45,
                  elicitation=0.36, chase_rate=0.75,
                  paranoia=0.95, intel_spend=0.4,
                  safety_spend=0.2, eval_rate=0.4),
        vary=dict(serve=(0.50, 0.62), loss_leader=(0.62, 0.86),
                  capex_aggression=(0.52, 0.70)),
        mixture={"LANG": .58, "REASON": .12, "CODE": .16, "AGENT": .06,
                 "IMAGE": .05, "AUDIO": .03},
        data=["web_crawl", "code_repos", "forums_social", "speech_corpus"]),

    "DATA": dict(
        name="Data monopolist",
        blurb="Believes the moat is the corpus, not the cluster. Signs every "
              "exclusive it can reach, partly to have it and partly so that "
              "nobody else does.",
        base=dict(train=0.44, serve=0.40, experiment=0.16, tokens_per_param=45,
                  moe_sparsity=4.0, run_months=4.0, ship_cooldown=7,
                  capex_aggression=0.58, supply_share=0.18, price_stance=1.05,
                  power_lookahead=6.0, comp_stance=1.05, openness=0.05,
                  data_hunger=2.4,
                  elicitation=0.38, chase_rate=0.4,
                  paranoia=0.85, intel_spend=0.65,
                  safety_spend=0.35, eval_rate=0.55),
        vary=dict(data_hunger=(1.8, 3.2), train=(0.40, 0.50)),
        mixture={"LANG": .40, "REASON": .18, "CODE": .18, "AGENT": .08,
                 "IMAGE": .08, "VIDEO": .05, "AUDIO": .03},
        data=["web_crawl", "code_repos", "books_papers", "forums_social",
              "news_archive", "video_platform", "speech_corpus", "stock_media",
              "expert_annotation"]),

    "FOLLOWER": dict(
        name="Fast follower",
        blurb="Lets everyone else pay for discovery. Spends almost nothing on "
              "research, copies what worked, and undercuts on price.",
        base=dict(train=0.46, serve=0.48, experiment=0.06, tokens_per_param=80,
                  moe_sparsity=5.0, run_months=3.0, ship_cooldown=4,
                  capex_aggression=0.34, supply_share=0.09, price_stance=0.70,
                  power_lookahead=4.0, comp_stance=0.80, openness=0.10,
                  follow_bonus=2.2, story_cap_gain=0.10,
                  elicitation=0.34, chase_rate=0.8,
                  paranoia=1.0, intel_spend=0.8,
                  safety_spend=0.15, eval_rate=0.3),
        vary=dict(experiment=(0.04, 0.10), follow_bonus=(1.6, 3.0),
                  price_stance=(0.6, 0.85)),
        mixture={"LANG": .52, "REASON": .15, "CODE": .26, "AGENT": .07},
        data=["web_crawl", "code_repos", "books_papers"]),

    "SOVEREIGN": dict(
        name="Sovereign champion",
        blurb="State capital, state priorities, and a hard ceiling on what "
              "silicon it can buy. Indifferent to public opinion.",
        base=dict(train=0.54, serve=0.34, experiment=0.12, tokens_per_param=30,
                  moe_sparsity=4.0, run_months=4.5, ship_cooldown=9,
                  capex_aggression=0.68, supply_share=0.09, price_stance=0.95,
                  power_lookahead=7.0, comp_stance=1.0, openness=0.06,
                  parent_cashflow_2020=1.6e9, parent_growth=1.64,
                  parent_cap=4.9e10,
                  elicitation=0.46, chase_rate=0.45,
                  paranoia=1.25, intel_spend=0.45,
                  safety_spend=0.2, eval_rate=0.35),
        vary=dict(supply_share=(0.06, 0.13), capex_aggression=(0.60, 0.76)),
        mixture={"LANG": .40, "REASON": .18, "CODE": .15, "AGENT": .09,
                 "ROBOT": .10, "VIDEO": .08},
        data=["web_crawl", "code_repos", "books_papers", "simulation",
              "speech_corpus"]),

    "HYPERSCALER": dict(
        name="Platform incumbent",
        blurb="Funds itself from a business that already prints money. Slow "
              "to decide, impossible to starve, and it owns the datacentres "
              "everyone else is renting.",
        base=dict(train=0.46, serve=0.40, experiment=0.14, tokens_per_param=35,
                  moe_sparsity=6.0, run_months=4.0, ship_cooldown=8,
                  capex_aggression=0.74, supply_share=0.28, price_stance=0.85,
                  power_lookahead=7.0, comp_stance=1.15, openness=0.10,
                  parent_cashflow_2020=4.0e9, parent_growth=1.68,
                  parent_cap=1.4e11, can_raise=False, debt_multiple=4.0,
                  elicitation=0.34, chase_rate=0.5,
                  paranoia=0.75, intel_spend=0.6,
                  safety_spend=0.55, eval_rate=0.7),
        vary=dict(parent_growth=(1.58, 1.76), capex_aggression=(0.66, 0.82)),
        mixture={"LANG": .38, "REASON": .16, "CODE": .18, "AGENT": .10,
                 "IMAGE": .08, "VIDEO": .06, "AUDIO": .04},
        data=["web_crawl", "code_repos", "books_papers", "video_platform",
              "speech_corpus", "stock_media"]),
}

# A vertical specialist has to be a specialist in something.
FOCUS = {
    "robotics": (dict(ROBOT=.40, AGENT=.30, REASON=.16, LANG=.14),
                 ["simulation", "web_crawl", "code_repos"]),
    "media":    (dict(IMAGE=.40, VIDEO=.32, AUDIO=.18, LANG=.10),
                 ["stock_media", "video_platform", "speech_corpus", "web_crawl"]),
    "code":     (dict(CODE=.56, AGENT=.20, REASON=.14, LANG=.10),
                 ["code_repos", "web_crawl", "expert_annotation", "books_papers"]),
    "science":  (dict(REASON=.58, LANG=.18, CODE=.18, AGENT=.06),
                 ["books_papers", "expert_annotation", "web_crawl", "news_archive"]),
    "voice":    (dict(AUDIO=.52, LANG=.30, VIDEO=.10, REASON=.08),
                 ["speech_corpus", "web_crawl", "video_platform", "books_papers"]),
}


def draw(key, rng):
    """One instance of a strategy, with this game's variation rolled in."""
    spec = STRATEGIES[key]
    p = dict(spec["base"])
    for field, (lo, hi) in spec.get("vary", {}).items():
        p[field] = (rng.randint(int(lo), int(hi))
                    if isinstance(spec["base"].get(field), int) else _u(rng, lo, hi))
    p["strategy"] = key
    p["strategy_name"] = spec["name"]

    if spec["mixture"] is None:                      # vertical specialist
        focus = rng.choice(sorted(FOCUS))
        mix, data = FOCUS[focus]
        p["mixture"] = dict(mix)
        p["data_priority"] = list(data)
        p["focus"] = focus
        p["strategy_name"] = spec["name"] + " (" + focus + ")"
    else:
        p["mixture"] = dict(spec["mixture"])
        p["data_priority"] = list(spec["data"])

    # jitter the mixture a little so no two runs of a strategy are identical
    mix = p["mixture"]
    for d in list(mix):
        mix[d] = max(0.01, mix[d] * _u(rng, 0.82, 1.18))
    tot = sum(mix.values())
    for d in mix:
        mix[d] /= tot

    # renormalise the compute split after variation
    tot = p["train"] + p["serve"] + p["experiment"]
    for lane in ("train", "serve", "experiment"):
        p[lane] /= tot
    return p


# --------------------------------------------------------------- behaviour
def withholds(params, lab, world, month, candidate_cap):
    """
    Does this lab choose NOT to release a model it could release?

    Only the self-improvement racer does this on purpose: shipping hands
    rivals something to measure themselves against and to distill from, and
    the whole plan is to compound privately. It releases when the money runs
    short, or when it is behind and needs the revenue anyway.
    """
    if params.get("strategy") != "RSI":
        return False
    costs = max(getattr(lab, "last_costs", 1.0), 1.0)
    runway = lab.cash / costs
    if runway < params.get("hoard_runway", 20.0):
        return False                      # needs the revenue more than the secrecy
    # against what the lab BELIEVES the frontier is. A hoarder that thinks
    # a rival is closer than it really is releases earlier than it needed to.
    frontier = getattr(lab, "perceived_frontier", 0.0)
    lead = candidate_cap - frontier
    return lead > -params.get("hoard_lead", 0.25)


def openness(params):
    """How much this lab's behaviour speeds the whole field up."""
    return params.get("openness", 0.1)
