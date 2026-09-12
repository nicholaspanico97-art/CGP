"""
Run outcomes and release decisions.

Two ideas carry this module.

**Runs are uncertain.** A completed run returns the scaling law's answer
multiplied by how it actually went. Most land near trend; some disappoint;
occasionally one lands far above. Good teams see fewer surprises in both
directions. A lab that is behind takes bigger swings, because matching the
leader is not good enough when you are losing.

**Labs do not ship backwards.** A model worse than the one already being
sold is shelved, not released. So run variance never appears as capability
going down - it appears as a flat stretch while the lab absorbs the loss and
tries again, and then as a jump when something lands. That asymmetry is what
makes the trajectory a ratchet with surprises in it rather than a smooth
curve with noise on it.
"""
import math
from . import constants as K


def outcome_multiplier(rng, researcher_quality, stars, behind_oom):
    """
    How this run actually went, as a multiplier on effective compute.
    Returns (multiplier, tag) where tag is 'breakthrough', 'dud' or ''.
    """
    comp = K.COMPETITIVENESS
    # A strong team narrows the distribution: they have seen these failure
    # modes before. It does not make them immune.
    skill = min(1.0, (researcher_quality * (1.0 + 0.06 * stars) - 1.0))
    damp = 1.0 - K.TALENT_VARIANCE_DAMP * max(0.0, skill)
    # Falling behind widens it: you stop running the safe recipe.
    risk = 1.0 + K.BEHIND_RISK_APPETITE * max(0.0, min(2.0, behind_oom))

    sigma = K.RUN_SIGMA_LOG10 * damp * risk * comp
    oom = rng.gauss(0.0, sigma)
    tag = ""

    p_break = K.RUN_BREAKTHROUGH_P * risk * comp
    p_dud = K.RUN_DUD_P * risk * (2.0 - damp) / 1.6
    roll = rng.random()
    if roll < p_break:
        oom += K.RUN_BREAKTHROUGH_OOM * comp * rng.uniform(0.6, 1.35)
        tag = "breakthrough"
    elif roll < p_break + p_dud:
        oom += K.RUN_DUD_OOM * rng.uniform(0.5, 1.3)
        tag = "dud"
    return 10 ** oom, tag


def should_ship(candidate_caps, current_caps, behind_oom):
    """
    Ship only on an improvement. A lab that is badly behind will ship a
    smaller improvement than a comfortable leader will - it needs something
    on the board.
    """
    if not current_caps:
        return True
    best_new = max(candidate_caps.values()) if candidate_caps else 0.0
    best_old = max(current_caps.values()) if current_caps else 0.0
    threshold = K.SHIP_THRESHOLD_OOM
    if behind_oom > 0.5:
        threshold *= 0.4
    return best_new > best_old + threshold


def post_train_budget(rng, researcher_quality):
    """
    How many x.5 releases THIS base model has in it. Not every model has
    three: some post-train beautifully, some are a dead end after one. A
    strong team gets a little more out of a given base.
    """
    roll = rng.random() + 0.10 * min(1.0, researcher_quality - 1.0)
    if roll < 0.22:
        return 1
    if roll < 0.62:
        return 2
    return K.POST_TRAIN_MAX


def post_train_gain(generation):
    """
    Capability added by the n-th post-training release on one base model.
    Sharply diminishing: the second is worth about half the first.
    """
    if generation >= K.POST_TRAIN_MAX:
        return 0.0
    return K.POST_TRAIN_GAIN_OOM * (K.POST_TRAIN_DECAY ** generation)
