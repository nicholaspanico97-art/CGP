"""
Domains, data, and markets.

A model is not one number. It is a profile across capability domains, and
each domain is bought with a different mixture of compute and DATA. Data is
the scarce input the compute story leaves out: you can always buy another
accelerator, but there is only one internet, the good corpora are licensed
or litigated, and the highest-value tokens - expert annotation, real product
telemetry - cannot be bought in bulk at any price.

Markets are segmented and each segment is gated on a domain. This is the
structural reason a niche leader survives a frontier leap somewhere else:
if you own image generation, AGI-grade coding does not take your customers,
because your customers were never buying coding.
"""
import math
from . import constants as K
from . import anchors as A

# --------------------------------------------------------------- domains
# benchmark: which fitted curve reads this domain's capability.
# anchored: whether we have real public scores to calibrate against.
DOMAINS = {
    "LANG":   dict(name="Language & conversation", benchmark="MMLU", anchored=True),
    "REASON": dict(name="Reasoning, maths, science", benchmark="GPQA", anchored=True),
    "CODE":   dict(name="Code", benchmark="SWE", anchored=True),
    "AGENT":  dict(name="Long-horizon agency", benchmark="SWE", anchored=False),
    "IMAGE":  dict(name="Image generation", benchmark="IMAGE", anchored=False),
    "VIDEO":  dict(name="Video generation", benchmark="VIDEO", anchored=False),
    "AUDIO":  dict(name="Speech & audio", benchmark="AUDIO", anchored=False),
    "ROBOT":  dict(name="Embodied control", benchmark="ROBOT", anchored=False),
}
DOMAIN_KEYS = list(DOMAINS)


# ----------------------------------------------------------- data sources
# volume:   token-equivalents available to the whole sector, for that source
# quality:  multiplier on effective tokens; expert data is worth many web tokens
# cost:     $ per year for a licence, or $ per billion tokens for one-off
# mix:      how the source's tokens distribute across domains
# exclusive: whether a licence can lock rivals out
# risk:     legal exposure per unit used (copyright, privacy, terms of service)
DATA_SOURCES = {
    "web_crawl": dict(
        name="Open web crawl", volume=3.2e13, quality=0.70, annual_cost=0.0,
        one_off_cost_per_btok=0.0, lead=0, exclusive=False, risk=0.45,
        available=(2020, 1),
        mix={"LANG": 0.62, "REASON": 0.16, "CODE": 0.12, "AGENT": 0.05,
             "IMAGE": 0.05}),
    "books_papers": dict(
        name="Books, papers, reference", volume=1.6e12, quality=1.35,
        annual_cost=0.0, one_off_cost_per_btok=180_000, lead=3,
        exclusive=False, risk=0.60, available=(2020, 1),
        mix={"LANG": 0.32, "REASON": 0.55, "CODE": 0.13}),
    "code_repos": dict(
        name="Public code repositories", volume=2.1e12, quality=1.15,
        annual_cost=0.0, one_off_cost_per_btok=20_000, lead=1,
        exclusive=False, risk=0.35, available=(2020, 1),
        mix={"CODE": 0.86, "REASON": 0.09, "AGENT": 0.05}),
    "forums_social": dict(
        name="Forum & social archive licence", volume=1.3e12, quality=0.90,
        annual_cost=6.0e7, one_off_cost_per_btok=0.0, lead=4,
        exclusive=True, risk=0.12, available=(2023, 6),
        mix={"LANG": 0.78, "REASON": 0.10, "CODE": 0.12}),
    "news_archive": dict(
        name="News & periodical licence", volume=2.6e11, quality=1.45,
        annual_cost=1.6e8, one_off_cost_per_btok=0.0, lead=5,
        exclusive=True, risk=0.08, available=(2023, 9),
        mix={"LANG": 0.55, "REASON": 0.35, "AGENT": 0.10}),
    "stock_media": dict(
        name="Licensed image & footage library", volume=6.0e11, quality=1.30,
        annual_cost=9.0e7, one_off_cost_per_btok=0.0, lead=4,
        exclusive=True, risk=0.10, available=(2022, 6),
        mix={"IMAGE": 0.72, "VIDEO": 0.28}),
    "video_platform": dict(
        name="Video platform corpus", volume=2.4e13, quality=0.85,
        annual_cost=4.0e8, one_off_cost_per_btok=0.0, lead=7,
        exclusive=True, risk=0.30, available=(2023, 1),
        # video tokens are expensive to extract: see PROCESSING_FLOP_PER_TOKEN
        mix={"VIDEO": 0.62, "AUDIO": 0.22, "IMAGE": 0.11, "ROBOT": 0.05}),
    "speech_corpus": dict(
        name="Speech & call-centre corpus", volume=2.0e11, quality=1.20,
        annual_cost=4.5e7, one_off_cost_per_btok=0.0, lead=4,
        exclusive=True, risk=0.18, available=(2021, 6),
        mix={"AUDIO": 0.88, "LANG": 0.12}),
    "expert_annotation": dict(
        name="Expert annotation programme", volume=3.0e10, quality=3.40,
        annual_cost=0.0, one_off_cost_per_btok=4.2e7, lead=6,
        exclusive=True, risk=0.02, available=(2021, 1),
        mix={"REASON": 0.44, "CODE": 0.28, "AGENT": 0.18, "LANG": 0.10}),
    "simulation": dict(
        name="Simulated environments", volume=1.0e13, quality=0.95,
        annual_cost=0.0, one_off_cost_per_btok=0.0, lead=2,
        exclusive=False, risk=0.0, available=(2022, 1),
        # costs FLOP rather than dollars: see SIM_FLOP_PER_TOKEN
        mix={"AGENT": 0.52, "ROBOT": 0.38, "CODE": 0.10}),
}

# Product telemetry is not purchasable. It accrues to whoever has users, in
# the domains those users actually use. This is the real data flywheel and
# the only source a competitor cannot buy their way into.
TELEMETRY_TOKENS_PER_MTOK_SERVED = 9_000     # usable tokens per Mtok served
TELEMETRY_QUALITY = 1.25

# Synthetic data: unlimited volume, costs compute, and its quality is capped
# by the capability of the model generating it. You cannot bootstrap past
# yourself, but you can cheaply amplify what you already have.
SYNTH_FLOP_PER_TOKEN = 9.0e11
SYNTH_QUALITY_CAP = 0.92                     # of the generating model's level

# Extraction cost: video and audio are not free to turn into training tokens.
PROCESSING_FLOP_PER_TOKEN = {"video_platform": 4.0e11, "speech_corpus": 6.0e10}

# Repetition: re-reading a corpus works for a few epochs, then stops.
MAX_USEFUL_EPOCHS = 4.2


# ---------------------------------------------------------- market segments
# differentiation: how much of a segment is decided by something other than
#   raw capability - taste, style, brand, workflow, ecosystem. Near 0 the
#   best benchmark wins the market; near 1 a smaller specialist holds its
#   ground against a rival an order of magnitude ahead on compute. Creative
#   work sits high, price-per-token API sits at zero.
# stickiness: how much of last month's share carries over regardless. A
#   consumer default is a habit and an enterprise deployment is a contract;
#   an API call is a config change. This is why a land grab is a strategy.
# gate:  minimum domain capability to have a sellable product at all.
#        Calibrated so each segment opens in the quarter its real product
#        category actually appeared - the assistant in late 2022, video
#        generation in 2024, and so on.
# tam:   $/yr the segment can absorb, as a fraction of the sector ceiling
# elasticity/temperature govern how contested the segment is
SEGMENTS = {
    "consumer_chat": dict(
        name="Consumer assistant", gates={"LANG": 25.20},
        weight_domains={"LANG": 0.75, "REASON": 0.15, "AGENT": 0.10},
        differentiation=0.3, stickiness=0.9, tam_share=0.30, temperature=0.85, brand_weight=1.4),
    "api_general": dict(
        name="General API", gates={"LANG": 23.20},
        weight_domains={"LANG": 0.55, "REASON": 0.25, "CODE": 0.20},
        differentiation=0.0, stickiness=0.45, tam_share=0.16, temperature=0.55, brand_weight=0.4),
    "coding": dict(
        name="Coding & software agents", gates={"CODE": 24.20},
        weight_domains={"CODE": 0.70, "AGENT": 0.20, "REASON": 0.10},
        differentiation=0.06, stickiness=0.7, tam_share=0.22, temperature=0.60, brand_weight=0.5),
    "enterprise_agents": dict(
        name="Enterprise agents", gates={"AGENT": 25.80, "REASON": 26.00},
        weight_domains={"AGENT": 0.50, "REASON": 0.30, "LANG": 0.20},
        differentiation=0.22, stickiness=0.88, tam_share=0.14, temperature=0.75, brand_weight=1.1),
    "science": dict(
        name="Scientific & technical", gates={"REASON": 26.30},
        weight_domains={"REASON": 0.85, "LANG": 0.15},
        differentiation=0.1, stickiness=0.75, tam_share=0.05, temperature=0.70, brand_weight=0.8),
    "image_gen": dict(
        name="Image generation", gates={"IMAGE": 24.40},
        weight_domains={"IMAGE": 1.0},
        differentiation=0.55, stickiness=0.72, tam_share=0.05, temperature=0.70, brand_weight=0.9),
    "video_gen": dict(
        name="Video generation", gates={"VIDEO": 25.70},
        weight_domains={"VIDEO": 0.82, "AUDIO": 0.18},
        differentiation=0.5, stickiness=0.7, tam_share=0.05, temperature=0.80, brand_weight=0.9),
    "voice": dict(
        name="Voice & audio", gates={"AUDIO": 24.70},
        weight_domains={"AUDIO": 0.80, "LANG": 0.20},
        differentiation=0.45, stickiness=0.7, tam_share=0.02, temperature=0.70, brand_weight=0.8),
    "robotics": dict(
        name="Embodied & robotics", gates={"ROBOT": 26.50, "AGENT": 26.80},
        weight_domains={"ROBOT": 0.65, "AGENT": 0.35},
        differentiation=0.15, stickiness=0.85, tam_share=0.01, temperature=0.90, brand_weight=0.7),
}


def segment_tam(seg_key, sector_spend_month):
    """This segment's share of the sector's realised monthly spend."""
    return sector_spend_month * SEGMENTS[seg_key]["tam_share"]


class DataStock:
    """A lab's holdings, in effective tokens per domain."""

    def __init__(self):
        self.tokens = {d: 0.0 for d in DOMAIN_KEYS}     # raw token-equivalents
        self.quality_num = {d: 0.0 for d in DOMAIN_KEYS}  # quality-weighted sum
        self.sources = set()
        self.legal_exposure = 0.0
        self.exclusives = set()

    def add(self, domain, tokens, quality):
        self.tokens[domain] += tokens
        self.quality_num[domain] += tokens * quality

    def quality(self, domain):
        t = self.tokens[domain]
        return (self.quality_num[domain] / t) if t > 0 else 1.0

    def effective(self, domain):
        """Quality-weighted tokens available in a domain."""
        return self.quality_num[domain]


def acquire(stock, source_key, month, fraction=1.0):
    """
    Take a source into a lab's stock. Returns (dollar_cost, flop_cost).
    Volume is what the SECTOR has; a lab takes a share of it.
    """
    s = DATA_SOURCES[source_key]
    if A.month_index(s["available"]) > month:
        return None
    tokens = s["volume"] * fraction
    dollars = s["annual_cost"] + s["one_off_cost_per_btok"] * tokens / 1e9
    flop = PROCESSING_FLOP_PER_TOKEN.get(source_key, 0.0) * tokens
    for dom, w in s["mix"].items():
        stock.add(dom, tokens * w, s["quality"])
    stock.sources.add(source_key)
    if s["exclusive"]:
        stock.exclusives.add(source_key)
    stock.legal_exposure += s["risk"] * math.log10(max(tokens, 10) / 1e9 + 1)
    return dollars, flop


def data_sufficiency(effective_tokens, tokens_wanted):
    """
    How well fed is this domain? Below 1.0 you are data-limited and the
    compute you pointed at it is partly wasted. Repetition buys a few epochs
    and then stops buying anything.
    """
    if tokens_wanted <= 0:
        return 1.0
    if effective_tokens <= 0:
        return 0.02
    raw = effective_tokens / tokens_wanted
    if raw >= 1.0:
        return 1.0
    # epochs of repetition, with the benefit tailing off
    epochs = min(MAX_USEFUL_EPOCHS, 1.0 / raw)
    return min(1.0, raw * (1.0 + math.log(epochs)))
