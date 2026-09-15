# Changelog — broad strokes, for review

Newest first. Each entry: what changed, why, what was measured. Details
in the commit messages and the file each points to.

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
