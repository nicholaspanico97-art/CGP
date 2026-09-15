# Changelog — broad strokes, for review

Newest first. Each entry: what changed, why, what was measured. Details
in the commit messages and the file each points to.

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
