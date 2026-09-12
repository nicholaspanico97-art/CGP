"""
What each strategy is actually trying to do.

Revenue share is the wrong scoreboard for most of these. An open-weights
lab is not trying to out-earn an enterprise vendor; it is trying to keep the
field close and stay relevant to developers. A self-improvement racer does
not care about revenue at all beyond staying solvent. A vertical specialist
wants one segment and does not want the others.

So each strategy carries its own objectives, and success is measured against
those. A strategy is "balanced" when it reaches its own goals in a
reasonable fraction of games - not when its revenue matches everyone else's.
"""
from . import domains as D


def snapshot(world):
    """Everything the objectives might want to look at, computed once."""
    labs = world.labs
    arr = {l.name: sum(l.seg_revenue.values()) * 12 for l in labs}
    total_arr = sum(arr.values()) or 1.0
    # A lab's own goals are judged on what it has BUILT, not on what it has
    # released. A strategy whose plan is to sit on capability is not failing
    # at capability because it is succeeding at sitting on it. The market, by
    # contrast, still only ever sees what shipped.
    def built(l):
        best = max(l.model.caps.values()) if l.model and l.model.caps else 0.0
        if l.internal and l.internal.caps:
            best = max(best, max(l.internal.caps.values()))
        return best
    caps = {l.name: built(l) for l in labs}
    ranked = sorted(caps.values(), reverse=True)
    # how tightly bunched the field is, in OOM between 1st and 4th
    compression = (ranked[0] - ranked[min(3, len(ranked) - 1)]) if ranked else 0.0

    seg_share = {}
    for seg in D.SEGMENTS:
        tot = sum(l.seg_revenue.get(seg, 0.0) for l in labs) or 1.0
        seg_share[seg] = {l.name: l.seg_revenue.get(seg, 0.0) / tot for l in labs}

    prices = sorted(l.price_per_mtok for l in labs if l.model)
    return dict(arr=arr, total_arr=total_arr, caps=caps, compression=compression,
                seg_share=seg_share, cheapest=(prices[0] if prices else 0.0),
                openness=getattr(world, "openness", 0.0),
                cap_rank=sorted(caps, key=lambda n: -caps[n]))


def metrics(lab, world, snap):
    """This lab's numbers, in the terms its objectives are written in."""
    n = lab.name
    arr = snap["arr"][n]
    capex = sum(lab.capex_by_year.values()) or 1.0
    served = getattr(lab, "served_mtok", 0.0)
    cost = lab.serving_cost_per_mtok() if lab.model else 1e9
    margin = ((lab.price_per_mtok - cost) / lab.price_per_mtok
              if lab.model and lab.price_per_mtok > 0 else -1.0)
    focus = lab.doctrine.get("focus")
    focus_seg = {"robotics": "robotics", "media": "video_gen", "code": "coding",
                 "science": "science", "voice": "voice"}.get(focus)
    dev = (snap["seg_share"]["api_general"].get(n, 0.0)
           + snap["seg_share"]["coding"].get(n, 0.0)) / 2.0
    return dict(
        arr_b=arr / 1e9,
        rev_share=arr / snap["total_arr"],
        capability=snap["caps"][n],
        cap_rank=snap["cap_rank"].index(n) + 1,
        cap_lead=snap["caps"][n] - max(
            [v for k, v in snap["caps"].items() if k != n] or [0.0]),
        compression=snap["compression"],
        solvent=1.0 if lab.cash > 0 else 0.0,
        price=lab.price_per_mtok if lab.model else 1e9,
        price_is_cheapest=1.0 if (lab.model and
            abs(lab.price_per_mtok - snap["cheapest"]) < 1e-9) else 0.0,
        margin=margin,
        served_mtok=served,
        exclusives=len(lab.data.exclusives),
        openness=lab.doctrine.get("openness", 0.0),
        dev_share=dev,
        consumer_share=snap["seg_share"]["consumer_chat"].get(n, 0.0),
        enterprise_share=(snap["seg_share"]["enterprise_agents"].get(n, 0.0)
                          + snap["seg_share"]["science"].get(n, 0.0)) / 2.0,
        focus_share=(snap["seg_share"][focus_seg].get(n, 0.0) if focus_seg else 0.0),
        capital_efficiency=arr / capex,
        trust=lab.trust,
        withheld=lab.withheld_months,
        largest_run_oom=(__import__("math").log10(lab.largest_run)
                         if lab.largest_run > 0 else 0.0),
    )


def g(metric, label, target, kind="atleast", weight=1.0):
    return dict(metric=metric, label=label, target=target, kind=kind, weight=weight)


# Each strategy's own definition of a good decade.
OBJECTIVES = {
    "SCALE": [
        g("cap_rank", "Hold the most capable model in the world", 1, "rank", 1.6),
        g("largest_run_oom", "Run the largest training run in the field", 27.5, "atleast", 1.0),
        g("solvent", "Survive it", 1, "atleast", 0.8),
    ],
    "RSI": [
        g("capability", "Reach a decisive capability level", 35.9, "atleast", 1.6),
        g("cap_lead", "Lead the field outright, not narrowly", 0.35, "atleast", 1.4),
        g("solvent", "Stay funded without selling out the plan", 1, "atleast", 0.9),
    ],
    "COST": [
        g("price_is_cheapest", "Be the cheapest tokens in the world", 1, "atleast", 1.5),
        g("margin", "And still make money doing it", 0.25, "atleast", 1.2),
        g("served_mtok", "Move serious volume", 2.5e7, "atleast", 1.0),
    ],
    "OPEN": [
        g("compression", "Keep the field within an order of magnitude", 0.75, "atmost", 1.5),
        g("dev_share", "Stay the developers' default", 0.18, "atleast", 1.2),
        g("solvent", "Still here in 2030", 1, "atleast", 0.8),
    ],
    "VERTICAL": [
        g("focus_share", "Own your segment outright", 0.40, "atleast", 1.7),
        g("solvent", "Without needing anyone else's market", 1, "atleast", 0.9),
        g("margin", "Profitably", 0.30, "atleast", 0.7),
    ],
    "ENTERPRISE": [
        g("enterprise_share", "Be the enterprise standard", 0.28, "atleast", 1.5),
        g("margin", "On enterprise margins", 0.45, "atleast", 1.1),
        g("trust", "With the reputation intact", 55, "atleast", 0.9),
    ],
    "CONSUMER": [
        g("consumer_share", "Own the consumer default", 0.35, "atleast", 1.6),
        g("solvent", "Survive the land grab", 1, "atleast", 1.2),
        g("arr_b", "Convert attention into a real business", 40.0, "atleast", 0.8),
    ],
    "DATA": [
        g("exclusives", "Lock up the corpora that matter", 3, "atleast", 1.5),
        g("cap_rank", "Turn that into a top-two model", 2, "rank", 1.0),
        g("arr_b", "And a real business", 30.0, "atleast", 0.9),
    ],
    "FOLLOWER": [
        g("capital_efficiency", "Earn more per dollar of iron than anyone", 0.38, "atleast", 1.5),
        g("margin", "On other people's research", 0.35, "atleast", 1.1),
        g("solvent", "Never bet the company", 1, "atleast", 0.9),
    ],
    "SOVEREIGN": [
        g("capability", "Reach the frontier without permission", 35.4, "atleast", 1.5),
        g("cap_rank", "Top two, independently", 2, "rank", 1.1),
        g("solvent", "Under an export ceiling", 1, "atleast", 0.8),
    ],
    "HYPERSCALER": [
        g("rev_share", "Take the largest share of the market", 0.30, "atleast", 1.4),
        g("cap_rank", "While staying at the frontier", 2, "rank", 1.1),
        g("arr_b", "At platform scale", 150.0, "atleast", 1.0),
    ],
}


def evaluate(lab, world, snap):
    """Score 0-1 against this lab's own objectives, plus per-goal detail."""
    m = metrics(lab, world, snap)
    goals = OBJECTIVES.get(lab.doctrine.get("strategy"), [])
    total_w, score, detail = 0.0, 0.0, []
    for goal in goals:
        v = m.get(goal["metric"], 0.0)
        t = goal["target"]
        if goal["kind"] == "atleast":
            frac = (v / t) if t else 1.0
        elif goal["kind"] == "atmost":
            frac = (t / v) if v > 0 else 1.0
        else:                                    # rank: 1 is best
            frac = 1.0 if v <= t else 1.0 - 0.34 * (v - t)
        frac = max(0.0, min(1.0, frac))
        score += frac * goal["weight"]
        total_w += goal["weight"]
        detail.append((goal["label"], round(frac, 2)))
    return (score / total_w if total_w else 0.0), detail, m
