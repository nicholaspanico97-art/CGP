# Changelog — broad strokes, for review

Newest first. Each entry: what changed, why, what was measured. Details
in the commit messages and the file each points to.

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
