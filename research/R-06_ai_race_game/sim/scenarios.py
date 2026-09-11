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


def historical_2020():
    """Six labs, sized to the sector as it actually stood in January 2020."""
    return [
        Lab("Helion",     DOCTRINES["product"],      1.0e9, 120, V100, 11_000),
        Lab("Vantor",     DOCTRINES["scaler"],       0.8e9,  90, V100,  9_000),
        Lab("Tessellate", DOCTRINES["hyperscaler"],  4.0e9, 210, V100, 26_000),
        Lab("Meridian",   DOCTRINES["safety"],       0.3e9,  45, V100,  3_000),
        Lab("Openwater",  DOCTRINES["open"],         0.5e9,  60, V100,  6_000),
        Lab("Redshift",   DOCTRINES["champion"],     1.5e9,  80, V100,  7_000),
        # A creative-media specialist. Included deliberately as the test of
        # whether a niche leader survives a frontier leap somewhere else.
        Lab("Lumen",      DOCTRINES["media"],        0.40e9, 40, V100,  3_500),
    ]
