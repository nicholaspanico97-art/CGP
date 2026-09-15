"""
The world outside the labs: blocs, supply, capital, mood.

v1.9: OBSERVED, NOT ACTING. This state exists, steps every month on the
record to 2025 and a projection after, and is shown on the dashboard's
World tab. Nothing here changes a lab's outcome yet - see WORLD_STATE.md
for what it will act on, in what order, and the dated anchors it must
reproduce before it is allowed to.

Two kinds of quantity live here:
  exogenous   - the record: GDP, grids, rates, access; piecewise by year
  derived     - AI's footprint on the world, computed from the sector each
                month: spend as a share of GDP, load as a share of grids,
                the fab share the labs consume, who lives where
"""
from . import constants as K

BLOCS = ("US", "China", "EU", "Gulf", "RoW")

# ------------------------------------------------------------ the record
# Jan-2020 values and yearly tracks. See WORLD_STATE.md for the tags.
INITIAL = {
    "US":    dict(gdp=21.1e12, growth=0.020, wage_bill=6.3e12, grid_gw=1100, grid_growth=0.015,
                  power_price=70.0, queue_months=24, access=1.0, mood=0.10, regulation=0.10),
    "China": dict(gdp=14.7e12, growth=0.050, wage_bill=2.2e12, grid_gw=2200, grid_growth=0.080,
                  power_price=85.0, queue_months=8, access=1.0, mood=0.30, regulation=0.30),
    "EU":    dict(gdp=15.3e12, growth=0.013, wage_bill=4.1e12, grid_gw=1000, grid_growth=0.020,
                  power_price=120.0, queue_months=36, access=1.0, mood=-0.10, regulation=0.30),
    "Gulf":  dict(gdp=1.6e12, growth=0.030, wage_bill=0.3e12, grid_gw=200, grid_growth=0.050,
                  power_price=45.0, queue_months=12, access=1.0, mood=0.20, regulation=0.10),
    "RoW":   dict(gdp=32.0e12, growth=0.035, wage_bill=4.8e12, grid_gw=3000, grid_growth=0.040,
                  power_price=90.0, queue_months=24, access=0.8, mood=0.00, regulation=0.20),
}

# dated changes on the record: (year, month, bloc, field, value, headline)
EVENTS = [
    (2022, 10, "China", "access", 0.35, "WORLD: the US restricts exports of advanced accelerators to China; China-bloc labs can now buy only a third of what they could"),
    (2023, 10, "China", "access", 0.15, "WORLD: export controls tightened; China-bloc labs are down to domestic silicon and what slips through"),
    (2023, 1,  "Gulf",  "access", 0.50, "WORLD: a licence regime halves the Gulf's access to advanced accelerators"),
    (2024, 6,  "Gulf",  "access", 0.80, "WORLD: the Gulf compute deals - sovereign clusters get access back under conditions"),
    (2023, 8,  "China", "regulation", 0.50, "WORLD: China's generative-AI rules take effect"),
    (2023, 10, "US",    "regulation", 0.35, "WORLD: a US executive order on AI - reporting thresholds for large runs"),
    (2025, 1,  "US",    "regulation", 0.20, "WORLD: the US executive order on AI is rescinded"),
    (2024, 8,  "EU",    "regulation", 0.70, "WORLD: the EU AI Act is in force; agentic products face a higher bar there"),
    (2022, 12, "US",    "mood", 0.40, "WORLD: the assistant moment - the public discovers what these models can do; mood jumps"),
    (2022, 12, "EU",    "mood", 0.15, None),
    (2022, 12, "RoW",   "mood", 0.25, None),
]

# yearly tracks, 2020..2025 on the record, projected after
US_QUEUE_MONTHS = {2020: 24, 2021: 26, 2022: 30, 2023: 36, 2024: 44, 2025: 48}
POLICY_RATE = {2020: 0.001, 2021: 0.001, 2022: 0.043, 2023: 0.053, 2024: 0.044, 2025: 0.039}
VENTURE_APPETITE = {2020: 1.0, 2021: 1.6, 2022: 1.2, 2023: 2.5, 2024: 3.5, 2025: 4.0}
MARKET_SENTIMENT = {2020: 0.0, 2021: 0.3, 2022: -0.2, 2023: 0.6, 2024: 0.7, 2025: 0.5}
WAFERS_K_PER_MONTH = {2020: 120, 2021: 150, 2022: 180, 2023: 210, 2024: 240, 2025: 290}
COWOS_K_PER_MONTH = {2020: 4, 2021: 6, 2022: 8, 2023: 15, 2024: 35, 2025: 75}
AI_SHARE_OF_LEADING_EDGE = {2020: 0.08, 2021: 0.12, 2022: 0.18, 2023: 0.30, 2024: 0.45, 2025: 0.60}

# Mood and regulation move on their own (v1.27, WORLD_STATE.md 4), on top
# of the dated events: incidents and displacement push mood down, cheaper
# and more capable services push it up; a bloc's regulatory stance
# follows its mood with a lag. Gains are modest - the record's events
# still dominate the 2020s.                                        (LOW)
MOOD_PER_SEVERE_INCIDENT = -0.06
MOOD_PER_MINOR_INCIDENT = -0.01
MOOD_PER_PT_UNEMPLOYMENT = -0.15     # per percentage point over trend
MOOD_PER_PT_AI_SPEND = 0.004         # per % of software spend that is AI
MOOD_DECAY_M = 24.0                  # half-life back toward neutral
REG_FOLLOWS_MOOD = 0.03              # per month, toward (0.3 - mood/2)

# where the world's AI inference is hosted
HOSTING_SHARE = {"US": 0.55, "China": 0.18, "EU": 0.10, "Gulf": 0.05, "RoW": 0.12}

# the strategy AIs' home blocs, until organisations carry their own
BLOC_OF_STRATEGY = {"SOVEREIGN": "Gulf", "COST": "China", "OPEN": "EU"}


def _track(table, year, growth=0.06):
    """A yearly table, projected past its last year at `growth`/yr."""
    last = max(table)
    if year <= last:
        return table.get(year, table[min(table)])
    return table[last] * (1 + growth) ** (year - last)


class Geo:
    def __init__(self):
        self.blocs = {b: dict(v) for b, v in INITIAL.items()}
        self.month = 0
        self.rate = POLICY_RATE[2020]
        self.appetite = VENTURE_APPETITE[2020]
        self.sentiment = MARKET_SENTIMENT[2020]
        self.wafers_k = WAFERS_K_PER_MONTH[2020]
        self.cowos_k = COWOS_K_PER_MONTH[2020]
        self.ai_share_fab = AI_SHARE_OF_LEADING_EDGE[2020]
        self.derived = {}
        self.history = []                     # one row a month, for the tab

    # ------------------------------------------------------------ record
    def step(self, world):
        m = world.month
        year, mo = 2020 + m // 12, 1 + m % 12
        self.month = m
        for b, s in self.blocs.items():
            s["gdp"] *= (1 + s["growth"]) ** (1 / 12)
            s["wage_bill"] *= (1 + s["growth"]) ** (1 / 12)
            s["grid_gw"] *= (1 + s["grid_growth"]) ** (1 / 12)
            if b == "China" and year >= 2023:
                s["growth"] = 0.040
        self.blocs["US"]["queue_months"] = _track(US_QUEUE_MONTHS, year, 0.0)
        for (y, mm, b, field, v, headline) in EVENTS:
            if (y, mm) == (year, mo):
                self.blocs[b][field] = v
                if headline:
                    world.news.append((m, headline))
        self.rate = _track(POLICY_RATE, year, 0.0)
        self.appetite = _track(VENTURE_APPETITE, year, 0.05)
        self.sentiment = _track(MARKET_SENTIMENT, year, 0.0)
        self.wafers_k = _track(WAFERS_K_PER_MONTH, year, 0.12)
        self.cowos_k = _track(COWOS_K_PER_MONTH, year, 0.25)
        self.ai_share_fab = min(0.85, _track(AI_SHARE_OF_LEADING_EDGE, year, 0.08))
        self._endogenous(world)
        self._derive(world)
        self.history.append(self.snapshot())

    def _endogenous(self, world):
        """Mood and regulation drift with what happened this month."""
        m = world.month
        log = getattr(world, "incident_log", []) or []
        this = [x for x in log if x.get("month") == m]
        severe = sum(1 for x in this if x.get("severity") == "severe")
        minor = len(this) - severe
        econ = getattr(world, "economy", None)
        econ_blocs = econ.snapshot()["blocs"] if econ and econ.last else {}
        k = 1 - 0.5 ** (1.0 / MOOD_DECAY_M)
        for b, s in self.blocs.items():
            e = econ_blocs.get("China" if b == "China" else ("EU" if b == "EU" else ("US" if b == "US" else "RoW")), {})
            du = max(0.0, e.get("unemployment", 0.0) - e.get("unemployment_0", 0.0)) * 100.0
            ai_sw = e.get("ai_share_software", 0.0) * 100.0
            drift = (severe * MOOD_PER_SEVERE_INCIDENT + minor * MOOD_PER_MINOR_INCIDENT
                     + du * MOOD_PER_PT_UNEMPLOYMENT / 12.0 + ai_sw * MOOD_PER_PT_AI_SPEND / 12.0)
            s["mood"] = max(-1.0, min(1.0, s["mood"] + drift - s["mood"] * k * 0.5))
            target = 0.3 - 0.5 * s["mood"]
            # a ratchet: rules come quickly on a bad mood and ease slowly
            rate = REG_FOLLOWS_MOOD if target > s["regulation"] else REG_FOLLOWS_MOOD / 6.0
            s["regulation"] = max(0.0, min(1.0, s["regulation"] + (target - s["regulation"]) * rate))

    # ----------------------------------------------------------- derived
    def _derive(self, world):
        """AI's footprint on the world this month, from the sector."""
        labs = world.labs
        spend_yr = getattr(world, "spend_stock", 0.0)             # $/yr realised
        world_gdp = sum(s["gdp"] for s in self.blocs.values())
        load_by_bloc = {b: 0.0 for b in BLOCS}
        labs_by_bloc = {b: [] for b in BLOCS}
        for l in labs:
            b = bloc_of(l)
            load_by_bloc[b] += l.fleet.megawatts() / 1e3          # GW
            labs_by_bloc[b].append(l.name)
        # the rest of the world's inference load, split by where AI is
        # hosted (the US hosts over half of it; hosting follows cheap
        # power and cloud regions more than GDP)                     (MED)
        econ = getattr(world, "economy", None)
        rest_gw = (econ.last.get("rest_of_world_mw", 0.0) / 1e3) if econ and econ.last else 0.0
        for b in BLOCS:
            load_by_bloc[b] += rest_gw * HOSTING_SHARE[b]
        bought = sum(getattr(l, "accels_bought_month", 0) for l in labs)
        fab_month = K.FAB_OUTPUT_PER_MONTH.get(2020 + world.month // 12, 3_800_000)
        self.derived = dict(
            spend_yr=spend_yr, spend_share_gdp=spend_yr / world_gdp,
            world_gdp=world_gdp,
            load_gw={b: v for b, v in load_by_bloc.items()},
            load_share_grid={b: (load_by_bloc[b] / self.blocs[b]["grid_gw"]) for b in BLOCS},
            labs={b: v for b, v in labs_by_bloc.items()},
            frontier_by_bloc={b: max((max(l.model.caps.values()) for l in labs
                                       if bloc_of(l) == b and l.model and l.model.caps),
                                      default=0.0) for b in BLOCS},
            fab_month=fab_month, ai_accels_month=bought,
            ai_share_fab=self.ai_share_fab,
            sector_incidents=len(getattr(world, "incident_log", []) or []),
            regulation_scalar=getattr(world, "regulation", 0.0),
        )

    def snapshot(self):
        if not self.derived:                  # before the first tick
            return dict(month=self.month, blocs={b: dict(s) for b, s in self.blocs.items()},
                        rate=self.rate, appetite=self.appetite, sentiment=self.sentiment,
                        wafers_k=self.wafers_k, cowos_k=self.cowos_k,
                        spend_yr=0.0, spend_share_gdp=0.0,
                        world_gdp=sum(s["gdp"] for s in self.blocs.values()),
                        load_gw={b: 0.0 for b in BLOCS}, load_share_grid={b: 0.0 for b in BLOCS},
                        labs={b: [] for b in BLOCS}, frontier_by_bloc={b: 0.0 for b in BLOCS},
                        fab_month=0, ai_accels_month=0, ai_share_fab=self.ai_share_fab,
                        sector_incidents=0, regulation_scalar=0.0)
        return dict(month=self.month, blocs={b: dict(s) for b, s in self.blocs.items()},
                    rate=self.rate, appetite=self.appetite, sentiment=self.sentiment,
                    wafers_k=self.wafers_k, cowos_k=self.cowos_k, **self.derived)


def bloc_of(lab):
    b = getattr(lab, "bloc", None)
    if b:
        return b
    return BLOC_OF_STRATEGY.get(lab.doctrine.get("strategy", ""), "US")
