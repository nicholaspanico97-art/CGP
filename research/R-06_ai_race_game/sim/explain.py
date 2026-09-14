"""
Why a model is what it is - the capability arithmetic, itemised.

The same function serves two purposes: at landing it records what actually
happened (with the run's real luck multiplier), and in the run planner it
predicts what a proposed run would give (with luck set to 1). So the number
the planner promises and the number the model reports are computed by one
piece of code, and a difference between them is the dice, nothing else.

Nothing here changes a result: `domain_capability` is called with the same
arguments the world uses; this only asks it to show its working.
"""
import math
from . import constants as K
from . import economics as E
from . import domains as D
from .capability import (capability_index, domain_capability,
                         reasoning_multiplier)


def run_rate_flop_per_month(lab, train_share):
    """FLOP the current fleet pours into a run each month at this share."""
    return lab.fleet.train_flops() * train_share * K.SECONDS_PER_MONTH / 1.18


def explain(lab, world, month, flop, tokens_per_param, moe_sparsity,
            test_time_oom, mixture, mult=1.0, tag=""):
    """
    The full chain from a run of `flop` to a capability profile, for this
    lab, this month. Returns a dict the page can render.
    """
    # the recipe the sector knows how to use this month caps the recipe
    edge = max(0.0, math.log10(max(lab.algo_mult, 1e-6))) * 6.0
    era_r = E.era_recipe(month + int(edge), K.RECIPE_ERA_TOKENS_PER_PARAM)
    era_moe = E.era_recipe(month + int(edge), K.RECIPE_ERA_MOE)
    r = min(tokens_per_param, era_r)
    moe = min(moe_sparsity, era_moe)
    shape = E.run_shape(flop, r, moe)

    sector = world.algo_frontier
    reason = reasoning_multiplier(month, lab.rl_investment, test_time_oom)
    eff_flop = flop * mult
    headline = capability_index(eff_flop, month, lab.algo_mult,
                                lab.rl_investment, test_time_oom,
                                sector_algo=sector)
    detail = {}
    caps = domain_capability(10 ** headline, mixture, shape["tokens"],
                             lab.data, D.DOMAIN_KEYS, detail=detail)

    domains = []
    for d in D.DOMAIN_KEYS:
        w = mixture.get(d, 0.0)
        dd = detail.get(d, {})
        have = lab.data.effective(d)
        wanted = shape["tokens"] * w
        domains.append(dict(
            domain=d, weight=w, wanted=wanted, have=have,
            sufficiency=dd.get("suff", 0.0), quality=dd.get("qual", 1.0),
            direct=dd.get("direct", 0.0), transferred=dd.get("trans", 0.0),
            gate=dd.get("gate", 0.0), cap=caps.get(d, 0.0),
            data_limited=(w > 0 and dd.get("suff", 1.0) < 0.999),
        ))

    return dict(
        flop=flop, mult=mult, tag=tag,
        log_flop=math.log10(max(flop, 1.0)),
        sector_algo=sector, lab_edge=lab.algo_mult, reasoning=reason,
        test_time_oom=test_time_oom,
        tokens_per_param=r, tokens_per_param_asked=tokens_per_param,
        era_tokens_per_param=era_r,
        moe=moe, moe_asked=moe_sparsity, era_moe=era_moe,
        params=shape["params"], active_params=shape["active_params"],
        tokens=shape["tokens"],
        headline=headline, best=max(caps.values()) if caps else 0.0,
        caps=caps, domains=domains,
        # serving economics of the model this run would make
        cost_per_mtok=E.cost_per_mtok(lab.fleet.newest(), shape["active_params"]),
    )


def risk(lab, flop, frontier):
    """
    How this run's dice are loaded: the same inputs `outcome_multiplier`
    uses, reported rather than rolled. `frontier` is the capability the
    lab measures itself against; before it has shipped anything it is not
    behind anyone.
    """
    ambition = flop / lab.largest_run if lab.largest_run > 0 else 1.0
    own = max(lab.model.caps.values()) if lab.model and lab.model.caps else 0.0
    behind = max(0.0, frontier - own) if own > 0 else 0.0
    behind *= (1.0 + K.SPIRAL * K.THREAT_RISK_GAIN)
    skill = min(1.0, (lab.researcher_quality * (1.0 + 0.06 * lab.stars) - 1.0))
    damp = 1.0 - K.TALENT_VARIANCE_DAMP * max(0.0, skill)
    risk_ = 1.0 + K.BEHIND_RISK_APPETITE * max(0.0, min(2.0, behind))
    over = max(0.0, math.log2(max(ambition, 1e-6) / K.AMBITION_COMFORT))
    sigma = (K.RUN_SIGMA_LOG10 + K.AMBITION_SIGMA * over) * damp * risk_ * K.COMPETITIVENESS
    p_break = K.RUN_BREAKTHROUGH_P * risk_ * K.COMPETITIVENESS
    p_dud = min(0.75, (K.RUN_DUD_P + K.AMBITION_RISK * over) * risk_ * (2.0 - damp) / 1.6)
    return dict(ambition=ambition, comfort=K.AMBITION_COMFORT, over=over,
                sigma_oom=sigma, p_breakthrough=p_break, p_dud=p_dud,
                behind=behind)


def data_holdings(lab):
    """What the lab holds, by domain and by source, in tokens."""
    by_source = {}
    for key in lab.data.sources:
        src = D.DATA_SOURCES[key]
        # a lab took a share of the sector volume; reconstruct from the mix
        by_source[key] = dict(name=src["name"], quality=src["quality"],
                              exclusive=src["exclusive"],
                              mix={d: w for d, w in src["mix"].items()})
    per_domain = {d: dict(tokens=lab.data.tokens[d],
                          effective=lab.data.effective(d),
                          quality=lab.data.quality(d))
                  for d in D.DOMAIN_KEYS}
    return dict(sources=by_source, domains=per_domain,
                legal_exposure=lab.data.legal_exposure)
