"""
Economics: iron, tokens, and money. All real units.

The two questions this module answers are the two that decide the game:

    what does it cost to put one million tokens in front of a customer,
    and how many million tokens will anyone buy at that price?
"""
import math
from . import constants as K
from . import anchors as A


# ------------------------------------------------------------------ hardware
class Accelerator:
    def __init__(self, row):
        (self.name, avail, self.peak_tflops, self.watts,
         self.capex, self.train_mfu, self.infer_util) = row
        self.avail_month = A.month_index(avail)

    @property
    def peak_flops(self):
        return self.peak_tflops * 1e12

    def train_flops(self):
        return self.peak_flops * self.train_mfu

    def serve_flops(self):
        return self.peak_flops * self.infer_util

    def monthly_cost(self):
        """Depreciation + power + datacenter opex, per accelerator."""
        depreciation = self.capex / K.DEPRECIATION_MONTHS
        kwh = self.watts / 1000.0 * K.PUE * K.HOURS_PER_MONTH
        power = kwh * K.ELECTRICITY_PER_KWH
        return depreciation + power * (1 + K.DC_OPEX_FRAC_OF_POWER)

    def megawatts(self, count):
        return count * self.watts * K.PUE / 1e6


ACCELS = [Accelerator(r) for r in K.ACCELERATORS]


def best_available(month):
    avail = [a for a in ACCELS if a.avail_month <= month]
    return avail[-1] if avail else ACCELS[0]


class Fleet:
    """A lab's accelerators, by generation, with straight-line retirement."""

    def __init__(self):
        self.holdings = []          # [accel, count, bought_month]

    def add(self, accel, count, month):
        self.holdings.append([accel, count, month])

    def retire(self, month):
        self.holdings = [h for h in self.holdings
                         if month - h[2] < K.DEPRECIATION_MONTHS + 12]

    def count(self):
        return sum(h[1] for h in self.holdings)

    def train_flops(self):
        return sum(h[0].train_flops() * h[1] for h in self.holdings)

    def serve_flops(self):
        return sum(h[0].serve_flops() * h[1] for h in self.holdings)

    def monthly_cost(self, month):
        total = 0.0
        for accel, count, bought in self.holdings:
            age = month - bought
            dep = accel.capex / K.DEPRECIATION_MONTHS if age < K.DEPRECIATION_MONTHS else 0.0
            kwh = accel.watts / 1000.0 * K.PUE * K.HOURS_PER_MONTH
            power = kwh * K.ELECTRICITY_PER_KWH * (1 + K.DC_OPEX_FRAC_OF_POWER)
            total += (dep + power) * count
        return total

    def megawatts(self):
        return sum(h[0].megawatts(h[1]) for h in self.holdings)

    def newest(self):
        return max((h[0] for h in self.holdings),
                   key=lambda a: a.avail_month, default=ACCELS[0])


# ------------------------------------------------------------------ training
def run_shape(total_flop, tokens_per_param, moe_sparsity=1.0):
    """
    Given a compute budget, pick the model.  C = 6ND with D = r*N, so
    N = sqrt(C / 6r).  Overtraining (large r) costs training compute for a
    smaller model that is cheaper to serve forever after - a real and
    load-bearing tradeoff, not a game invention.
    """
    n = math.sqrt(total_flop / (6.0 * tokens_per_param))
    d = tokens_per_param * n
    return {"params": n, "tokens": d, "active_params": n / max(moe_sparsity, 1.0)}


def run_duration_months(total_flop, train_flops_per_s, overhead=1.18):
    """Wall-clock. Overhead covers restarts, stragglers, evals, and loss spikes."""
    if train_flops_per_s <= 0:
        return 1e9
    return total_flop * overhead / train_flops_per_s / K.SECONDS_PER_MONTH


# ----------------------------------------------------------------- inference
def tokens_per_second(accel, active_params):
    """Serving throughput for one accelerator, under a latency SLO."""
    flop_per_token = K.FLOP_PER_TOKEN_PER_ACTIVE_PARAM * max(active_params, 1e6)
    return accel.serve_flops() / flop_per_token


def cost_per_mtok(accel, active_params, utilization=None):
    """
    Marginal-ish cost of serving a million tokens: the accelerator's monthly
    all-in cost divided by the tokens it can actually sell in a month.
    """
    util = K.SERVING_UTILIZATION if utilization is None else utilization
    tok_month = tokens_per_second(accel, active_params) * K.SECONDS_PER_MONTH * util
    if tok_month <= 0:
        return 1e9
    return accel.monthly_cost() / (tok_month / 1e6)


def serving_capacity_mtok(fleet, active_params, fraction, utilization=None):
    """Million tokens per month a fleet fraction can deliver."""
    util = K.SERVING_UTILIZATION if utilization is None else utilization
    flop_per_token = K.FLOP_PER_TOKEN_PER_ACTIVE_PARAM * active_params
    tok = fleet.serve_flops() * fraction / flop_per_token * K.SECONDS_PER_MONTH * util
    return tok / 1e6


# -------------------------------------------------------------------- demand
def consumer_tam(month):
    f = month / K.MONTHS
    lo, hi = K.CONSUMER_TAM_2020, K.CONSUMER_TAM_2030
    return lo * (hi / lo) ** f


def adoption_potential(frontier_capability):
    """Fraction of the addressable market that would pay, at this capability."""
    if frontier_capability < K.CONSUMER_PRODUCT_CAPABILITY:
        return 0.0      # no conversational product exists yet
    x = (frontier_capability - K.CONSUMER_ADOPT_MIDPOINT) / K.CONSUMER_ADOPT_WIDTH
    return 1.0 / (1.0 + math.exp(-x))


def era_recipe(month, table):
    """Best sector-known value of a training recipe parameter at a date."""
    best = None
    for ym, val in sorted(table.items()):
        if A.month_index(ym) <= month:
            best = val
    return best if best is not None else list(table.values())[0]


def api_demand_mtok(month, price_per_mtok, capability, ref_price=30.0,
                    ref_cap=26.8, scale=3.5e4):
    """
    Monthly API token demand for the sector, in million tokens.
    Elastic in price and strongly increasing in capability: cheaper and
    smarter both unlock whole categories of use that did not exist before.
    """
    if price_per_mtok <= 0:
        price_per_mtok = 0.01
    price_term = (ref_price / price_per_mtok) ** K.API_PRICE_ELASTICITY
    cap_term = 10 ** (K.QUALITY_ELASTICITY * (capability - ref_cap) / 4.0)
    return scale * price_term * cap_term


def logit_share(scores, temperature=1.0):
    """Softmax share over per-lab attractiveness scores."""
    if not scores:
        return []
    mx = max(scores)
    ex = [math.exp((s - mx) / temperature) for s in scores]
    tot = sum(ex)
    return [e / tot for e in ex]
