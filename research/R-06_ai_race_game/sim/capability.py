"""
Capability: from FLOP to benchmark scores.

The chain is deliberately explicit, because each link is a place where a
player can spend money and get something different back:

    pretraining FLOP          bought with accelerators and time
      x algorithmic efficiency  bought with researchers and experiments
      x reasoning multiplier    bought with post-training RL and, at
                                serve time, with FLOP per query
    = effective compute
    -> capability index C = log10(effective compute)
    -> benchmark scores, one saturating curve per suite

Nothing here is a game abstraction. C is just the base-10 log of a FLOP
count, so a capability of 26.5 means 3.2e26 effective FLOP and the
difference between 26.5 and 27.5 is exactly one order of magnitude.
"""
import math
from . import constants as K
from . import anchors as A

CONF_WEIGHT = {"HIGH": 1.0, "MED": 0.6, "LOW": 0.3}


# ------------------------------------------------------ algorithmic efficiency
def algo_rate(month):
    """Frontier pretraining-efficiency growth, x per year, decaying."""
    f = min(max(month / K.MONTHS, 0.0), 1.0)
    return K.ALGO_EFF_RATE_2020 + (K.ALGO_EFF_RATE_2030 - K.ALGO_EFF_RATE_2020) * f


_ALGO_CACHE = None


def algo_efficiency(month):
    """Cumulative frontier efficiency multiplier vs Jan 2020 = 1.0."""
    global _ALGO_CACHE
    if _ALGO_CACHE is None:
        acc, out = 0.0, []
        for m in range(K.MONTHS + 1):
            out.append(10 ** acc)
            acc += math.log10(algo_rate(m)) / 12.0
        _ALGO_CACHE = out
    return _ALGO_CACHE[max(0, min(month, K.MONTHS))]


# -------------------------------------------------------- reasoning multiplier
# Post-training (RLHF, then large-scale RL on verifiable rewards) and
# inference-time search both convert into effective compute. Modelled as one
# multiplier with two eras, because the public record does not separate them.
def reasoning_multiplier(month, rl_investment=1.0, test_time_oom=0.0):
    m_rlhf = A.month_index(K.POST_TRAIN_ERA_START)
    m_rl = A.month_index(K.POST_TRAIN_RL_ERA_START)
    if month < m_rlhf:
        base = 1.0
    elif month < m_rl:
        base = K.RLHF_ERA_TOTAL_GAIN ** ((month - m_rlhf) / (m_rl - m_rlhf))
    else:
        # RL era: fast, then decelerating as the easy verifiable-reward
        # domains get used up
        yrs = (month - m_rl) / 12.0
        eff_yrs = K.REASONING_DECAY_YEARS * (1 - 0.5 ** (yrs / K.REASONING_DECAY_YEARS)) * 2
        base = K.RLHF_ERA_TOTAL_GAIN * 10 ** (K.REASONING_OOM_PER_YEAR * eff_yrs)
    base *= rl_investment
    # test-time compute, in OOMs above a single forward pass, with saturation
    oom = min(test_time_oom, K.TEST_TIME_SATURATION_OOM)
    return base * (10 ** (K.TEST_TIME_KAPPA * oom))


def capability_index(pretrain_flop, month, lab_algo_mult=1.0,
                     rl_investment=1.0, test_time_oom=0.0):
    eff = (pretrain_flop
           * algo_efficiency(month) * lab_algo_mult
           * reasoning_multiplier(month, rl_investment, test_time_oom))
    return math.log10(max(eff, 1.0))


# ------------------------------------------------------------------ benchmarks
def _sigmoid(x):
    if x < -40:
        return 0.0
    if x > 40:
        return 1.0
    return 1.0 / (1.0 + math.exp(-x))


class BenchmarkModel:
    """One saturating curve per suite, fitted to the historical anchors."""

    def __init__(self):
        self.params = {}

    def fit(self, verbose=False):
        frontier = FrontierHistory()
        for suite in ("MMLU", "GPQA", "SWE"):
            pts = []
            for date, s, score, _model, conf in A.BENCHMARKS:
                if s != suite:
                    continue
                m = A.month_index(date)
                c = frontier.capability_at(m)
                pts.append((c, score, CONF_WEIGHT[conf]))
            lo, hi = A.BENCHMARK_FLOOR[suite], A.BENCHMARK_CEILING[suite]
            best, bestp = None, None
            # coarse-to-fine grid search; two free parameters, few points
            c50_lo, c50_hi, w_lo, w_hi = 22.0, 34.0, 0.15, 4.0
            for _ in range(4):
                step_c = (c50_hi - c50_lo) / 60.0
                step_w = (w_hi - w_lo) / 60.0
                for i in range(61):
                    c50 = c50_lo + i * step_c
                    for j in range(61):
                        w = w_lo + j * step_w
                        if w <= 0.02:
                            continue
                        sse = sum(wt * (lo + (hi - lo) * _sigmoid((c - c50) / w) - y) ** 2
                                  for c, y, wt in pts)
                        if best is None or sse < best:
                            best, bestp = sse, (c50, w)
                c50, w = bestp
                c50_lo, c50_hi = c50 - 6 * step_c, c50 + 6 * step_c
                w_lo, w_hi = max(0.05, w - 6 * step_w), w + 6 * step_w
            self.params[suite] = bestp
            if verbose:
                rmse = math.sqrt(best / sum(p[2] for p in pts))
                print(f"  {suite:5s} c50={bestp[0]:6.3f}  w={bestp[1]:5.3f}  "
                      f"weighted RMSE={rmse:5.2f} pts  (n={len(pts)})")
        return self

    def score(self, suite, capability):
        c50, w = self.params[suite]
        lo, hi = A.BENCHMARK_FLOOR[suite], A.BENCHMARK_CEILING[suite]
        return lo + (hi - lo) * _sigmoid((capability - c50) / w)


class FrontierHistory:
    """Log-linear interpolation of the real frontier pretraining run."""

    def __init__(self):
        raw = sorted((A.month_index(d), math.log10(f))
                     for d, _l, f, *_ in A.TRAINING_RUNS)
        # the frontier is the largest run to date, so take a running max and
        # keep one point per month (Chinchilla and PaLM share a date)
        best, pts = -99.0, []
        for m, f in raw:
            best = max(best, f)
            if pts and pts[-1][0] == m:
                pts[-1] = (m, best)
            else:
                pts.append((m, best))
        self.pts = pts

    def flop_at(self, month):
        pts = self.pts
        if month <= pts[0][0]:
            return 10 ** pts[0][1]
        if month >= pts[-1][0]:
            # extrapolate on the trailing slope
            (m0, f0), (m1, f1) = pts[-2], pts[-1]
            slope = (f1 - f0) / max(1, m1 - m0)
            return 10 ** (f1 + slope * (month - m1))
        for (m0, f0), (m1, f1) in zip(pts, pts[1:]):
            if m0 <= month <= m1:
                if m1 == m0:
                    return 10 ** f1
                t = (month - m0) / (m1 - m0)
                return 10 ** (f0 + t * (f1 - f0))
        return 10 ** pts[-1][1]

    def capability_at(self, month):
        # the frontier model of that date, with frontier-era reasoning
        tt = 0.0
        m_rl = A.month_index(K.POST_TRAIN_RL_ERA_START)
        if month > m_rl:
            tt = min(2.5, (month - m_rl) / 12.0)   # test-time compute ramp
        return capability_index(self.flop_at(month), month, 1.0, 1.0, tt)
