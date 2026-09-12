"""
Talent.

The claim this module encodes: in 2020 ideas were the bottleneck and a
handful of people held them, while by 2030 progress comes from industrial-
scale systematic experimentation that a large organisation runs whether or
not any individual is present. So the elasticity of algorithmic progress
shifts from people to compute across the decade.

That is a modelling claim, not a measurement. It is stated here as two
numbers you can argue with rather than buried in a coefficient.
"""
import math
from . import constants as K


def talent_elasticity(month):
    """Exponent on researcher-years in the research production function."""
    f = min(max(month / K.MONTHS, 0.0), 1.0)
    return K.TALENT_ELASTICITY_2020 + (
        K.TALENT_ELASTICITY_2030 - K.TALENT_ELASTICITY_2020) * f


def compute_elasticity(month):
    """Exponent on experiment FLOP in the research production function."""
    f = min(max(month / K.MONTHS, 0.0), 1.0)
    return K.COMPUTE_ELASTICITY_2020 + (
        K.COMPUTE_ELASTICITY_2030 - K.COMPUTE_ELASTICITY_2020) * f


def star_exponent(month):
    """
    How much individual exceptional researchers matter. Early, enormously:
    one team with the right idea moved the whole field. Late, much less:
    the idea is known and the constraint is how many experiments you can run.
    """
    f = min(max(month / K.MONTHS, 0.0), 1.0)
    return K.STAR_EXPONENT_2020 + (K.STAR_EXPONENT_2030 - K.STAR_EXPONENT_2020) * f


def global_star_pool(month):
    """Frontier-caliber researchers in the world. Grows slowly; can't be bought."""
    yrs = month / 12.0
    return K.STAR_POOL_2020 * (K.STAR_POOL_GROWTH ** yrs)


def global_researcher_pool(month):
    yrs = month / 12.0
    return K.RESEARCHER_POOL_2020 * (K.RESEARCHER_POOL_GROWTH ** yrs)


def market_comp(month, demand, supply):
    """
    What a researcher costs. Scarcity is real: when every lab is hiring
    against the same small pool, compensation goes up for everyone.
    """
    tightness = max(0.2, demand / max(supply, 1.0))
    return K.RESEARCHER_COST_PER_YEAR * (tightness ** K.COMP_SCARCITY_EXPONENT)


def attraction(lab, month, market_rate):
    """
    Why a researcher picks one lab over another. Compute per head leads,
    because you cannot run the experiment you cannot run; money and mission
    follow. This is the loop that makes the rich get richer - and the reason
    a lab that hoards compute without shipping still bleeds people, because
    prestige is part of it.
    """
    flops_per_head = lab.fleet.train_flops() / max(lab.researchers, 1)
    comp_ratio = lab.comp_offer / max(market_rate, 1.0)
    prestige = (lab.model.capability - 20.0) if lab.model else 0.0
    return (K.ATTRACT_COMPUTE * math.log10(max(flops_per_head, 1e6))
            + K.ATTRACT_COMP * math.log10(max(comp_ratio, 0.1))
            + K.ATTRACT_MISSION * (lab.mission_alignment / 50.0)
            + K.ATTRACT_PRESTIGE * prestige / 10.0)


def research_output(lab, month, exp_flop, months=1.0):
    """
    Algorithmic progress produced this month, as a relative gain.

    Cobb-Douglas in people and experiment compute, with the exponents
    shifting from people to compute across the decade, multiplied by a
    star term that starts dominant and fades.
    """
    r_years = lab.researchers * lab.researcher_quality * months / 12.0
    if r_years <= 0 or exp_flop <= 0:
        return 0.0
    a_t = talent_elasticity(month)
    a_c = compute_elasticity(month)
    stars = (1.0 + lab.stars) ** star_exponent(month)
    return (K.RESEARCH_SCALE * (r_years ** a_t)
            * ((exp_flop / 1e21) ** a_c) * stars)
