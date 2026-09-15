# Changelog — broad strokes, for review

Newest first. Each entry: what changed, why, what was measured. Details
in the commit messages and the file each points to.

## v1.30 — the world layer's instrument (Sep 15 2026)
`sim/geo_checkpoints.py` scores WORLD_STATE.md 6: the controls'
effect on a China-bloc fleet, the assistant-moment mood jump, appetite
doubling, the EU stance after the Act, the US queue, AI's share of the
US grid, Gulf access, the rate cycle. 7 of 8 hold on the calibration
roster; AI load reaches 0.83% of the US grid against an anchor of 1%
(same shortfall as the 10 GW milestone at -9 months). The rest of the
world's AI load is now split by where it is hosted (US 55%) rather than
by GDP. *Files: `sim/geo_checkpoints.py`, `geo.HOSTING_SHARE`,
`results_world.txt`.*

## v1.29 — a higher bar for the next run (Sep 15 2026)
`NEXT_RUN_MIN_GROWTH` 1.5 -> 2.0 (effective compute over the last landed
run): swept 1.5 / 2.0 / 2.5. Timing median -4 / mean 5.2 (best yet) /
worst -15 / 16 of 16 / order 114; magnitude 1.96x; cadence 0.95 base
models per lab-year. The 2022 outlier (a hyperscaler running 1.4e25 in
April 2022, 6x PaLM) remains - it is one lab with 300k chips taking
allowed 4x steps from a large first run; the anchor compares the
world's largest run to the reported frontier, which was not always the
largest trained. Left for review.

## v1.28 — one generation at a time (Sep 15 2026)
The 2022 and 2024 frontier-run outliers were single labs jumping 7-10x
in one run - physically possible with their fleets, never done in the
record, where generations stepped 3-5x. The strategy AIs now plan no
more than 4x their last landed run (`MAX_RUN_JUMP`); the player may
still gamble. GPT-4-class lands at 2.11e25 against the record's 2.1e25.
Timing median -5 / mean 5.9 / worst -16 / 16 of 16 / order 113;
magnitude 2.09x (frontier 2.38x from 2.9x). *Files:
`DoctrinePolicy.decide_run`, `constants.MAX_RUN_JUMP`.*

## v1.27 — mood and regulation move on their own (Sep 15 2026)
WORLD_STATE.md 4. Each bloc's public mood drifts with the sector's
incidents (severe -0.06, minor -0.01), knowledge-work unemployment over
trend (-0.15 a point) and how much of software spend AI has become
(+0.004 a point), decaying toward neutral over two years; the dated
events still land on top. Regulatory stance follows mood as a ratchet -
quick to rise on a bad mood, six times slower to ease - so the EU holds
~0.6 after the Act instead of decaying. Regulation per bloc already
gates agentic products (v1.25), so this closes the loop the roadmap
called "the world reacts to AI": what the labs ship changes mood,
mood changes rules, rules change what the labs may sell. Sector
instrument unchanged (mean 7.3, 16 of 16, 2.21x). *File: `geo._endogenous`.*

## v1.26 — in-house silicon (Sep 15 2026)
HARDWARE.md 5 step 4. A lab can start a chip programme ($1.5B/yr for
three years; a button on the compute panel) and then owns a designer in
the tier: its chips at cost plus amortised R&D (about two thirds of the
incumbent's price), its own foundry bookings, new generations as long as
the money keeps coming, a generation behind to start. "Buy from: your
own" appears once it lands. The AI hyperscaler owns the in-house
designer that was already in the tier (Lattice, TPU-v4-class from
mid-2020, a parent's R&D budget). On the way, a serious bug: the story
valuation's cap was set in points, and the scale strategy's steeper
story gain compounded to 4,000x - Vantor raised $2.3T of equity in 2025,
built 3M chips, reached a 2028-class model, and the economy's spend and
the world's power load ran away with it. The multiplier is now capped at
150x. Sector instrument: timing median -7 / mean 7.3 / worst -18 / 16
of 16 / order 112; magnitude 2.21x (frontier runs 2.9x - the
hyperscaler's cheaper silicon buys a bigger fleet; worth a look).
Balance 58-94%, 5.5 of 7 viable, 4% runaways. Packaging forecast rule
tightened (80% for three months, two pending). *Files:
`Hardware.start_program / program_step / own_offer`, `World.buy_now`
(chip_program), `_capital_market` (the cap).*

## v1.25 — the world acts on the labs (Sep 15 2026)
WORLD_STATE.md 5, steps 1, 3 and 5. A lab's chip supply is the
industry's packaging capacity reaching its bloc at that bloc's access
share (a China-bloc lab under controls gets 15% of foreign output plus
the domestic fab; the table fallback is gone). A round raises more in a
hot venture market and less in a cold one (appetite index); the
infrastructure debt that funds gigawatt builds shrinks as the policy
rate rises. And a bloc's regulatory stance raises the bar on agentic
products for its own labs (the EU after the Act). Timing: median -6 /
mean 5.4 (best yet) / worst -16 / 16 of 16 / order 112; magnitude
2.05x; balance 51-95% of goals, 5.5 of 7 viable, 8% runaways, 87 lead
changes. *Files: `Hardware.sellable_per_month`, `_resolve_market`
(lift_for), `_procure` (rounds, debt), `constants` BLOC_REGULATION_WEIGHT,
APPETITE_ROUND_GAIN, RATE_DEBT_SENSITIVITY.*

## v1.24 — a market opens when it is worth something (Sep 15 2026)
Two "market opens" checkpoints fired the month a lab first cleared the
capability gate; they now ask for a market worth $250M/yr (the API
"exists" check is unchanged). And the pie's split between consumer-type
and enterprise-type segments follows the economy's realised
consumer/enterprise spend instead of fixed shares - so enterprise agents
get a market when firms have deployed, not when a model can. Enterprise
agents -18 (inside the band for the first time in the model's life),
consumer +1, 10 GW -2; timing mean 6.1 / worst -18 / 16 of 16 / order
112; magnitude 2.03x. *Files: `checkpoints._seg_open`,
`domains.segment_tam`, `World._enterprise_frac`.*

## v1.23 — the AI labs buy in the hardware market (Sep 15 2026)
HARDWARE.md 5 step 2, for the AIs: each lab's standing capex rule now
buys from the seller the market's own rule picks for its bloc (perf per
dollar, lead time, the incumbent's moat), at that seller's price and
lead - the year's-best table is used only when nobody may sell to it.
Strategies differ in price sensitivity (cost-led and open labs shop; the
rest pay for the ecosystem), so the challenger gets real customers. The
tier's unit economics were brought to the record on the way (yield on
reticle-sized dies, module cost, a 65% base margin: an A100-class at
$14k in 2020, a B200-class at $34k in 2025) and its generation cadence
tamed (24 months minimum, 2.0x / 2.8x steps). Incumbent 79-87%,
challenger ~20%. Sector instrument: timing mean 7.1 / worst -20 / 15 of
16 / order 114; magnitude 2.08x (power 1.30x). Hardware anchors 9 of
14 lines - the best yet. *Files: `Hardware.choose`, `World._procure`,
`constants.PRICE_SENSITIVITY`.*

## v1.22 — the rest of the world's AI load (Sep 15 2026)
The power anchors count all AI load; the sim's seven labs were the
sector, so power ran 1.5-2.4x under all along. The AI spend the labs do
not book (~88%) is now served on someone's chips: its load is derived
from that spend at $45B/yr per GW of inference capacity (LOW), counted
in the power instruments and split across blocs by GDP on the World
tab. Power family 1.24x (best ever); 10 GW at -9 months (was +15);
timing mean 6.4 / worst -16 / 16 of 16 / order 113; magnitude 2.06x.
*Files: `econ.REVENUE_PER_GW_YR`, `World.sector_mw`, the instruments.*

## v1.21 — demand comes from the labour markets (Sep 15 2026)
`DEMAND_MODEL = "labour"`. Sector spend is now the four blocs' realised
AI spend x the labs' share of what the world pays for AI, instead of the
fitted capability curve (kept behind the switch, shown on the World tab
for comparison). A pilots term - firms paying to try what they cannot
yet deploy - carries the 2021-22 API-era revenue the deployment model
had no source for. Timing: median -6 / mean 6.6 / worst -16 / 16 of 16
/ order 114 (revenue milestones +5 / -6 / +3). Magnitude 2.27x (revenue
2.6x: 2024 $17B vs $7B, 2026 $43B vs $62B; 2023 and 2025 on the
record). Economy anchors 10 of 14 lines. The world is now one system:
what the labs build changes what the world can automate, which changes
what the labs are paid. *Files: `World._sector_spend`, `econ.py`
(pilots), `constants.DEMAND_MODEL`.*

## v1.20 — the economy gets its instrument (Sep 15 2026)
`sim/econ_checkpoints.py` scores the labour-market demand model against
ECONOMY.md 5. Two of its parameters were wrong by the record and are
fixed: deployability (half at 150, width 12 - ~6% of tasks in
production at the 2025 frontier, per the adoption surveys) and the
productivity multiplier (2 -> 1). And one anchor was mis-specified: the
labour model measures what the world pays for AI, the fitted curve what
seven labs book - about a tenth of it in 2025 (`LAB_SHARE_2025` =
0.12). On the calibration roster 6 of 7 anchors hold (enterprise $55B
in 2024, 7.5% of US software spend in 2025, unemployment flat, labs'
share within 1.2-1.6x of the curve, convergence by 2030); the
productivity effect through 2025 is 0.30 pt against an anchor of 0.20.
The switch (`DEMAND_MODEL`) stays on the curve; flipping it is the next
session's job, with the sector checkpoints re-passed. *Files:
`sim/econ_checkpoints.py`, `sim/econ.py`, `results_economy.txt`.*

## v1.19 — chip supply responds to demand (Sep 15 2026)
HARDWARE.md 5 step 3 / ROADMAP item 8. The industry's deliverable chips
per month come from the hardware tier's packaging capacity, not a
yearly table; capacity is built on forecast against the demand labs
*wanted* (orders queue with a seller and lapse after a year), so a
backlog and a lead-time spike form when demand runs past capacity. Two
false starts on the way: capacity that only saw delivered orders never
saturated (no crunch), and a backlog that never lapsed pinned lead time
at 24 months. Now: an 11-month peak in mid-2024, incumbent 82-83%
through it, the 100k-cluster checkpoint at +1 month. Sector timing
median -4 / mean 6.5 / worst -16 / 16 of 16 / order 114; magnitude
2.06x (frontier runs mixed: early years high, 2025-26 a little small -
supply post-2025 is tighter than the record; the packaging forecast
rule is the knob). Rivals' point releases are one summary line in the
event log. *Files: `Hardware.sellable_per_month`, `Hardware.step`,
`World._procure`.*

## v1.18 — the private algorithmic edge, bounded (Sep 15 2026)
The last year of capability earliness. With runs on the record,
capability per FLOP was still high; switching off the private
algorithmic edge alone moved "knowledge 86" from -14 to -2 months. The
cap on how far a lab can privately run ahead of the field's efficiency
track was 7x - but the track is fitted to the real leader, so the
leader's edge over it must be small. Set to 3x (swept 1, 2, 3, 7).
Timing: median -2 / mean 6.2 / worst -17 / 16 of 16 / order 113 (from
7.5 / -19 / 15 / 112); magnitude 1.83x. Balance 36-100% of goals, 5.5
of 7 viable, 8% runaways, 84 lead changes. HYPERSCALER 36% - see v1.13.
*File: `constants.MAX_ALGO_ADVANTAGE`.*

## v1.17 — the world's events are news; bloc power reaches the labs (Sep 15 2026)
The dated world events (export controls, the AI Act, the assistant
moment, the Gulf deals, the US order and its rescinding) now appear in
the event log the month they happen. WORLD_STATE.md 5 step 2: a lab's
build lead is max(greenfield build, its bloc's interconnect queue) + 6
months, and leased power is priced at the bloc's industrial rate. The
chip-price premium from the hardware tier is capped at 1.3x list (the
record's 20-30% over list at the 2023 peak; 1.6x was pushing capex 1.6x
over while power stayed 1.8x under). Timing mean 7.5 / worst -19 / 15
of 16 / order 112; magnitude 1.89x. The power family stays ~1.8x under
and 10 GW lands a year late: the anchor counts all AI load, the sim's
seven labs are the sector - a definitional gap to resolve when the
economy layer gives the rest of the world its own AI load. *Files:
`geo.EVENTS`, `Lab.contract_power`, `World._decide`, `market_terms`.*

## v1.16 — choose your supplier (Sep 15 2026)
HARDWARE.md 5, step 2, player side. "Buy from" on the compute panel:
each seller's current chip, price, lead time; greyed under export
controls (a China-bloc lab cannot buy from a US designer after Oct
2022). The order joins that designer's backlog, so what you buy moves
its lead time and margin. The AIs still buy the year's best chip -
calibration untouched. Replay covers supplier orders. *Files:
`Hardware.offers`, `Chip.as_accelerator`, `World.buy_now`.*

## v1.15.1 — a valuation ceiling; an instrument fix (Sep 15 2026)
The narrative valuation had no ceiling: a lab at score 185 was "worth"
$60T and a routine round raised trillions (Vantor's cash hit $21T in
2026). The story term now saturates six points past GPT-3 class; beyond
that, revenue multiples carry. 2030 cash $130B-1T, valuations $3-10T.
And the 100k-cluster checkpoint counted chips at the newest chip's
throughput, which halved the count the month a new generation landed;
it now uses the fleet's average - the checkpoint reads +8 months (was
+13). Timing mean 7.7 / worst -19 / 15 of 16 / order 112. *Files:
`_capital_market`, `checkpoints._cluster`.*

## v1.15 — the hardware tier reaches the labs (Sep 15 2026)
HARDWARE.md 5, step 1. The chip you buy is priced at list x the
incumbent designer's margin over its normal 60%, and arrives after the
incumbent's backlog (3-14 months) instead of a flat five - so the 2024
crunch is felt: dearer chips, longer waits, shown on the compute panel
and in every purchase estimate. The tier's own anchors: 7 of 14 lines
pass across two rosters; the lead-time spike now lands Oct 2024 at
11-12 months on its own. Cost on the sector instrument: timing mean 6.9
-> 8.0 months (one checkpoint tips to -19), magnitude 1.86x (same);
balance: runaways 0% -> 12%, 5.0 of 7 viable - the biggest buyer
rides the crunch best; flagged. *Files: `World.market_terms`, `_procure`,
`buy_now`.*

## v1.14 — one meaning for capability; a staggered opening (Sep 15 2026)
Finding 2: `Model.capability` is now always the best domain (the
headline index is kept as `Model.headline`); the frontier, pricing,
valuation, prestige and safety all read one thing. Finding 3: each lab's
first run starts at a month its cycle says (fixed on the calibration
roster, 2-9; drawn 0-9 in a random game) instead of everyone on day one
- "a paid API exists" moved from -5 to +1 months. That exposed a bug: a
lab with no model yet read as 23 OOM behind, which compressed its first
run to the minimum window and inflated its capex and comp; threat is
now zero before a lab has entered (`intel.threat`). Measured: timing
median -1 / mean 6.9 / worst -18 / 16 of 16 / order 112 (v1.13: -6 /
7.5 / -20 / 15 / 114); magnitude 1.85x; balance 40-100% of goals, 5.2
of 7 viable, 0% runaways, 81 lead changes. HYPERSCALER still 40% (see
v1.13). *Files: `World.Model`, `scenarios.CALIBRATION_ROSTER`,
`DoctrinePolicy.decide_run`, `intel.threat`.*

## v1.13 — labs can die (Sep 15 2026)
Finding 1. Six months of negative cash with no round closed puts a lab
in distress: the rival with the deepest pockets acquires it (iron,
power, data and 70% of the people move; the models do not) if its cash
covers the hole three times over, otherwise it is wound down. The player
dying ends the game. Switching this on showed every lab had been running
at negative cash through 2020-21 all along, so three capital-side rules
were added that real labs have: the standing capex rule spends only cash
beyond nine months of costs and spreads it over six; rounds are sized to
two years of burn (cap 30% sold, six months apart); a backed lab is
bridged by its parent and an independent gets an emergency down round
while the hole fits under 35% dilution. And the narrative valuation no
longer values a lab two OOMs behind at $60M (12x per OOM -> 1.8x; the
story starts paying at GPT-3 class) - Cohere, Inflection, Adept raised
at $1-4B behind the frontier. Result: 0-2 acquisitions a decade, 5-7
survivors, few emergency rounds. Measured: timing mean 7.5 / worst -20
/ 15 of 16 / order 114 (v1.12: 7.9 / -17 / 16 / 115); magnitude 1.90x
(1.82x), capex 1.61x, frontier runs 1.86x, revenue 2.64x (up from 2.05x
- better-funded labs serve more); balance 41-94% of goals, 5.3 of 7
viable, 0% runaways, 78 lead changes. **HYPERSCALER fell 85% -> 41%**:
a parent's cash is no longer decisive once independents can raise; the
real 2020s, arguably, but review it. *Files: `World._insolvency`, the
raise and capex blocks in `_procure`, `_capital_market`;
`results_balance.txt`.*

## v1.12 — the sim's early capability, fixed at the source (Sep 15 2026)
Finding 12. Frontier runs were 3-13x the record in 2021-24 while capex
was within 1.5x: the iron was right, the run it went into was not. The
flagship run's share of the training lane (a constant 30%) is now an
era track, 6% in 2020 rising to 28% by 2026 - the field learned to
consolidate the cluster on one run as the scaling result sank in
(`constants.FRONTIER_RUN_SHARE_ERA`, used in `World._next_run_size`).
Measured: timing mean |offset| 8.9 -> 7.9 months, worst -19 -> -17,
16/16 in band (was 15), order 113 -> 115/120; magnitude 2.23x -> 1.82x
weighted (best ever), frontier runs 3.3x -> 2.0x; balance 50-93% of
goals, 5.4 of 7 viable, 0% runaways; cadence 1.05 base models per
lab-year. Enterprise agents inside the band for the first time.
*Review: `results_checkpoints.txt`, the "frontier run" table from
`python -m sim.score`.*
