"""Starting positions. Fictional labs, real archetypes, Jan 2020."""
from . import economics as E
from .world import Lab

_FIRST_RUN = 2.6e23  # where the sector actually stood in early 2020

V100 = [a for a in E.ACCELS if a.name == "V100"][0]

_FREE = ["web_crawl", "code_repos", "books_papers"]

MIXTURES = {
    # How a lab splits its training mixture across domains. This is the
    # single most identity-defining choice a lab makes: it decides which
    # markets the resulting model is even allowed to compete in.
    "scaler":      {"LANG": .55, "REASON": .20, "CODE": .20, "AGENT": .05},
    "product":     {"LANG": .48, "REASON": .15, "CODE": .22, "AGENT": .08,
                    "IMAGE": .07},
    "hyperscaler": {"LANG": .38, "REASON": .15, "CODE": .18, "AGENT": .10,
                    "IMAGE": .08, "VIDEO": .07, "AUDIO": .04},
    "safety":      {"LANG": .44, "REASON": .28, "CODE": .21, "AGENT": .07},
    "open":        {"LANG": .50, "REASON": .15, "CODE": .30, "AGENT": .05},
    "champion":    {"LANG": .43, "REASON": .18, "CODE": .16, "AGENT": .09,
                    "ROBOT": .09, "VIDEO": .05},
    "media":       {"IMAGE": .40, "VIDEO": .32, "AUDIO": .18, "LANG": .10},
}

_PW = 6.5   # megawatts contracted per megawatt currently in use

DOCTRINES = {
    "scaler":      dict(train=0.62, serve=0.22, experiment=0.16,
                        tokens_per_param=20, moe_sparsity=1.0, first_run_flop=_FIRST_RUN, run_months=5.0, power_lookahead=_PW, mixture=MIXTURES["scaler"],
                        data_priority=_FREE + ["expert_annotation", "forums_social"],
                        capex_aggression=0.66, supply_share=0.22, ship_cooldown=8, story_value=2.5e9, raise_fraction=0.18),
    "product":     dict(train=0.34, serve=0.52, experiment=0.14,
                        tokens_per_param=60, moe_sparsity=4.0, first_run_flop=_FIRST_RUN, run_months=3.0, power_lookahead=_PW, mixture=MIXTURES["product"],
                        data_priority=_FREE + ["forums_social", "expert_annotation", "stock_media"],
                        capex_aggression=0.62, supply_share=0.18, ship_cooldown=6, debt_multiple=3.5, story_value=3.0e9, raise_fraction=0.16),
    "hyperscaler": dict(train=0.48, serve=0.38, experiment=0.14,
                        tokens_per_param=30, moe_sparsity=6.0,
                        first_run_flop=_FIRST_RUN * 2, run_months=4.0,
                        power_lookahead=_PW, mixture=MIXTURES["hyperscaler"],
                        data_priority=_FREE + ["video_platform", "speech_corpus",
                                               "stock_media", "expert_annotation"],
                        capex_aggression=0.75, supply_share=0.30, price_stance=0.85,
                        parent_cashflow_2020=4.0e9, parent_growth=1.62,
                        ship_cooldown=8, debt_multiple=2.0, can_raise=False,
                        story_value=9.0e9, raise_fraction=0.10),
    "safety":      dict(train=0.44, serve=0.40, experiment=0.16,
                        tokens_per_param=40, moe_sparsity=3.0, first_run_flop=_FIRST_RUN*0.6, run_months=4.0, power_lookahead=_PW, mixture=MIXTURES["safety"],
                        data_priority=_FREE + ["expert_annotation", "news_archive"],
                        capex_aggression=0.55, supply_share=0.14, ship_cooldown=8, debt_multiple=3.0, story_value=1.8e9, raise_fraction=0.15),
    "open":        dict(train=0.50, serve=0.30, experiment=0.20,
                        tokens_per_param=80, moe_sparsity=1.0, first_run_flop=_FIRST_RUN*0.5, run_months=3.5, power_lookahead=_PW, mixture=MIXTURES["open"],
                        data_priority=_FREE + ["simulation"],
                        capex_aggression=0.45, supply_share=0.12, ship_cooldown=7, story_value=0.9e9, raise_fraction=0.14, price_stance=0.55),
    "champion":    dict(train=0.55, serve=0.33, experiment=0.12,
                        tokens_per_param=25, moe_sparsity=4.0, first_run_flop=_FIRST_RUN*0.7, run_months=4.5, power_lookahead=_PW, mixture=MIXTURES["champion"],
                        data_priority=_FREE + ["simulation", "speech_corpus"],
                        capex_aggression=0.68, supply_share=0.10, ship_cooldown=9,
                        parent_cashflow_2020=1.5e9, parent_growth=1.45, story_value=4.0e9, raise_fraction=0.12),
    "media":       dict(train=0.40, serve=0.46, experiment=0.14,
                        tokens_per_param=50, moe_sparsity=2.0, first_run_flop=_FIRST_RUN*0.4,
                        run_months=3.5, power_lookahead=_PW, mixture=MIXTURES["media"],
                        data_priority=["stock_media", "video_platform", "speech_corpus", "web_crawl"],
                        capex_aggression=0.50, supply_share=0.08, ship_cooldown=6,
                        story_value=0.7e9, raise_fraction=0.15),
}


# Strategy assignment for the calibration roster: the archetypes that were
# actually on the board in 2020, fixed so the calibration score stays
# comparable across changes.
CALIBRATION_ROSTER = [
    ("Helion",     "CONSUMER",    1.0e9, 120, 11_000),
    ("Vantor",     "SCALE",       0.8e9,  90,  9_000),
    ("Tessellate", "HYPERSCALER", 4.0e9, 210, 26_000),
    ("Meridian",   "ENTERPRISE",  0.3e9,  45,  3_000),
    ("Openwater",  "OPEN",        0.5e9,  60,  6_000),
    ("Redshift",   "SOVEREIGN",   1.5e9,  80,  7_000),
    ("Lumen",      "VERTICAL",    0.4e9,  40,  3_500),
]

# Names a randomized game draws from.
NAMES = ["Helion", "Vantor", "Tessellate", "Meridian", "Openwater", "Redshift",
         "Lumen", "Corvid", "Aleph", "Northwind", "Sable", "Kestrel"]

STARTS = [(4.0e9, 210, 26_000), (1.5e9, 110, 11_000), (1.0e9, 95, 9_000),
          (0.8e9, 80, 7_000), (0.6e9, 60, 5_000), (0.45e9, 48, 3_500),
          (0.3e9, 40, 2_500)]


def randomized_2020(seed=0, n=7):
    """
    A fresh game. Every lab draws a strategy, with variation inside it, and
    nobody is told who drew what.
    """
    import random
    from . import strategy as STRAT
    rng = random.Random(seed * 7717 + 101)
    keys = list(STRAT.STRATEGIES)
    rng.shuffle(keys)
    picks = keys[:n] if n <= len(keys) else [rng.choice(keys) for _ in range(n)]
    names = NAMES[:]
    rng.shuffle(names)
    starts = STARTS[:n]
    rng.shuffle(starts)
    labs = []
    for i in range(n):
        params = STRAT.draw(picks[i], rng)
        cash, res, accels = starts[i]
        params["first_run_flop"] = _FIRST_RUN * (0.5 + 1.5 * (accels / 26_000))
        params["story_value"] = cash * 2.5
        params["raise_fraction"] = 0.10 + 0.08 * rng.random()
        params["researcher_quality"] = 0.85 + 0.35 * rng.random()
        labs.append(Lab(names[i], params, cash, res, V100, accels))
    return labs


def historical_2020():
    """
    The calibration roster: seven labs sized to the sector as it stood in
    January 2020, each running the strategy its real-world archetype ran.
    Fixed on purpose - the calibration score has to stay comparable.
    """
    import random
    from . import strategy as STRAT
    rng = random.Random(4242)
    labs = []
    for name, key, cash, res, accels in CALIBRATION_ROSTER:
        params = STRAT.draw(key, rng)
        if key == "VERTICAL":                       # Lumen is the media house
            mix, data = STRAT.FOCUS["media"]
            params["mixture"] = dict(mix)
            params["data_priority"] = list(data)
            params["strategy_name"] = "Vertical specialist (media)"
            params["focus"] = "media"
        params["first_run_flop"] = _FIRST_RUN * (0.5 + 1.5 * (accels / 26_000))
        params["story_value"] = cash * 2.5
        params["raise_fraction"] = 0.14
        params["researcher_quality"] = 1.0
        labs.append(Lab(name, params, cash, res, V100, accels))
    return labs
