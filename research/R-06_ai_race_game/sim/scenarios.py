"""Starting positions. Fictional labs, real archetypes, Jan 2020."""
from . import economics as E
from .world import Lab

_FIRST_RUN = 2.6e23  # where the sector actually stood in early 2020

V100 = [a for a in E.ACCELS if a.name == "V100"][0]

_PW = 6.5   # megawatts contracted per megawatt currently in use

DOCTRINES = {
    "scaler":      dict(train=0.62, serve=0.22, experiment=0.16,
                        tokens_per_param=20, moe_sparsity=1.0, first_run_flop=_FIRST_RUN, run_months=5.0, power_lookahead=_PW,
                        capex_aggression=0.66, supply_share=0.22, ship_cooldown=8, story_value=2.5e9, raise_fraction=0.18),
    "product":     dict(train=0.34, serve=0.52, experiment=0.14,
                        tokens_per_param=60, moe_sparsity=4.0, first_run_flop=_FIRST_RUN, run_months=3.0, power_lookahead=_PW,
                        capex_aggression=0.62, supply_share=0.18, ship_cooldown=6, debt_multiple=3.5, story_value=3.0e9, raise_fraction=0.16),
    "hyperscaler": dict(train=0.48, serve=0.38, experiment=0.14,
                        tokens_per_param=30, moe_sparsity=6.0, first_run_flop=_FIRST_RUN*2, run_months=4.0, power_lookahead=_PW,
                        capex_aggression=0.70, supply_share=0.30, story_value=9.0e9, raise_fraction=0.10, price_stance=0.85),
    "safety":      dict(train=0.44, serve=0.40, experiment=0.16,
                        tokens_per_param=40, moe_sparsity=3.0, first_run_flop=_FIRST_RUN*0.6, run_months=4.0, power_lookahead=_PW,
                        capex_aggression=0.55, supply_share=0.14, ship_cooldown=8, debt_multiple=3.0, story_value=1.8e9, raise_fraction=0.15),
    "open":        dict(train=0.50, serve=0.30, experiment=0.20,
                        tokens_per_param=80, moe_sparsity=1.0, first_run_flop=_FIRST_RUN*0.5, run_months=3.5, power_lookahead=_PW,
                        capex_aggression=0.45, supply_share=0.12, ship_cooldown=7, story_value=0.9e9, raise_fraction=0.14, price_stance=0.55),
    "champion":    dict(train=0.55, serve=0.33, experiment=0.12,
                        tokens_per_param=25, moe_sparsity=4.0, first_run_flop=_FIRST_RUN*0.7, run_months=4.5, power_lookahead=_PW,
                        capex_aggression=0.68, supply_share=0.10, ship_cooldown=9,
                        parent_cashflow_2020=1.5e9, parent_growth=1.45, story_value=4.0e9, raise_fraction=0.12),
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
    ]
