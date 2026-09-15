# HANDOFF — Frontier (R-06), Sep 13 2026

Written at the end of the session that built the decision seam and then
made the sim playable on top of it (v1.4, v1.5). If you are
a new session, read `CLAUDE.md` first (it auto-loads), then this, then
`WORLD_MODEL.md`. This file is the *session* record: what was just done,
what is known to be true about it, and what I would do next. `CLAUDE.md` is
the permanent orientation; this one goes stale.

## Where the project actually is

A calibrated, zero-dependency simulation of the AI race 2020–2030 lives in
`sim/`. As of v1.4 it is a world model *with a seam a player can stand in*:
every choice a lab makes goes through `observe → decide → apply`, is
validated and logged, and the log plus the seed is a saved game. There is
still no player, no turn structure, no UI beyond a read-only viewer. The
plan of record (`DESIGN.md`, `ROADMAP.md`) is that the game is a window
onto this simulation, and the window comes last. No architectural items
remain on the roadmap; what is left is content and the player.

Branch: `claude/ai-race-game-plan-vl6gi3`, pushed. No PR has been
opened and none was asked for.

## What this session added

**The decision seam** — `ROADMAP.md` item 2, the last architectural item.
`sim/policy.py` is new: `Observation` (what a lab can see), `Actions` (its
standing decisions for the month, ~24 fields, bounds-checked), `Policy`
(decide + the release interrupt), `DoctrinePolicy` (the eleven strategies
as behaviour) and `ReplayPolicy` (replays a log, reads nothing else).
`sim/world.py` gained `observe`, `apply`, `ask_release`, `_decide` and an
`action_log`; lost every inline `doctrine.get(...)` that was a *choice*.
`sim/strategy.py` now only says what each strategy wants — its behaviour
(`withholds`, the bids, the spiral) moved to the policy. `sim/replay.py`
is the standing check. The action log is exported in `meta.actions`.

Design choices worth knowing, because they were choices:

- **Decision vs identity.** The cut is in `WORLD_MODEL.md` §2g. If you add
  a mechanic and find yourself writing `lab.doctrine.get(...)` in
  `world.py`, stop and ask whether a player could choose it. If yes it is
  an `Actions` field, set by the policy, read from `lab.actions`.
- **The release decision is an interrupt, not a standing order.** A run
  lands with an outcome nobody knew; `decide_release` is asked at that
  moment with the result in hand: ship or hold, and if shipping, evaluate
  first or carry the debt. I chose the interrupt over deferring the
  question to the next tick because it is bit-compatible with v1.3 and
  because for a player "your run landed — ship it?" is the right modal.
  If a quarterly turn structure later wants the question batched, the
  place to change is `World.ask_release`.
- **The spiral moved into the policy.** Fear compressing the run window,
  bidding up compensation, raising capex aggression, widening the data
  wallet — all now computed in `DoctrinePolicy` from `obs.threat`. The
  world only prices the *consequence* (the ambition term in the outcome
  distribution). A player gets no automatic panic.
- **Policies have their own dice.** `lab.rng_policy` is a fifth stream.
  This was forced, not chosen: the first cut drew the eval roll from
  `lab.rng` and the replay check failed instantly, because a replay draws
  nothing and every world draw after the first ship was shifted. The
  general rule is now in `CLAUDE.md`: the world never draws from the
  policy's stream, and the policy never draws from the world's.
- **A held model that is finally released now faces the eval question.**
  Before v1.4 it skipped it entirely (no eval, no debt). Small behaviour
  change, affects RSI labs only, correct.

## Then: it is playable (v1.5, same session)

Nick's direction mid-session: *the goal is a viable simulation model, and
then a way for the game to be played, because play testing is its own
calibration.* So the playable path was built immediately, headless and
deliberately plain:

- `sim/game.py` — `PlayerPolicy` (holds your orders, hands them to the
  world monthly; answers the release interrupt through a callback) and
  `Game` (three ticks a turn; `letter()` is the board letter; `commit()`
  returns the quarter's events in date order; `save()` is seed + log).
- `sim/play.py` — the terminal: `split`, `set`, `mix`, `buy`, `bid`,
  `end`, `save`, `auto`. A refused order changes nothing (edits go to a
  copy and are validated before they land). `--auto N` watches autopilot.
- The interrupt receives the candidate `Model` now, so the prompt shows
  per-domain capability against what you currently sell.
- `sim/replay.py` gained `check_game`: a played game — human orders,
  three different interrupt answers — replays bit for bit from its save.

Nick played the terminal version and asked for a GUI - not the final
game's, something to learn the model through. `sim/serve.py` +
`viewer/play.html`: a stdlib HTTP server runs the game in a worker thread
(so the release interrupt can block mid-quarter while the browser shows the
question) and a single page shows orders with a one-line explanation each,
money tiles and three small charts (cash, revenue, your best vs the
frontier you fear), the scoreboard, markets, rivals as believed, ops, data,
and the event log. `python3 -m sim.serve` then `http://localhost:8765`.
The `EXPLAIN` dict in `serve.py` is the plain-English glossary of every
order; keep it honest when an order's meaning changes.

Nick's first requests from playing (v1.5.2): **manual control** over the
things that auto-fired — accelerator purchases, power contracts, raising
rounds — and a **balance sheet**. `Actions` gained three switches
(`auto_capex`, `auto_power`, `auto_raise`; the strategy AIs keep them True
so calibration is unchanged) and three one-shot orders (`buy_accels`,
`contract_mw`, `raise_now`) that fire once, the first month they are in
force, then clear. In manual mode the world *says why* an order was clipped
or refused (`lab.notices`, surfaced as `ORDER:` events). Every dollar that
moves is now booked by category in `lab.ledger` (`Lab.book`), and the
dashboard shows this quarter and the whole game: revenue by market,
operating costs by kind, capital and financing. Also: `sim.serve` listens
on IPv6 too (browsers try `::1` first; the missing listener was the
"stubborn button"), refuses to start twice on one port, and opens a tab.

v1.6 (same session, Nick's request): **the run is planned, not timed.**
When the cooldown ends the policy is asked `decide_run(obs, proposal)`;
the strategy AIs return the proposal (bit-identical), the player gets a
planner with a live preview. The recipe and mixture are now **fixed at
planning time** in `lab.run_plan` and read from there at landing (was:
read from the standing orders at landing - same values for the AIs, hence
unchanged calibration). One-shots `extend_run_months` and `finish_run`
change a run in progress. `sim/explain.py` itemises the capability chain
(compute x sector progress x edge x reasoning era x luck = headline; per
domain: share, data have/want, fed, transfer, quality) and is used both
to record `model.why` at landing and to preview in the planner, so a
difference between promise and result is the dice and nothing else.
`domain_capability` gained an optional `detail` dict; arithmetic untouched.

*Findings 8, 10 and 11 were fixed in v1.7 (the model batch); 9 is
"said so" in the planner. Measured together: checkpoints median -9
(was -10), mean |offset| 8.5 (9.4), worst -18 (-22), 16/16 inside the
band (15/16), order 113/120 (113); balance eleven strategies at 59-88%
(54-89%), 85.7 lead changes (86.3), 5.7 of 7 viable (5.8). Fixing #8
alone moved the frontier a year early: `behind` is now the max of six
noisy beliefs, biased high, and the leader no longer rolls safe dice;
`BEHIND_RISK_APPETITE` was refit 0.55 -> 0.25 on the checkpoint table
(0.15 / 0.35 / 0.40 / 0.55 tried). The data changes alone were neutral.*

8. **`maybe_ship` reads the TRUE frontier.** *(fixed v1.7)* `fc = self.frontier_capability()`
   is passed in as `frontier_cap` and used for `behind`, which loads the
   run's dice. The comment says "this lab's BELIEF" but it is the world's
   max. An observability-seam breach (CLAUDE.md invariant). The fix is
   `lab.perceived_frontier`; it will change realisations, so re-measure.
   `explain.risk()` already uses the belief, so the planner's stated risk
   differs slightly from the risk actually rolled until this is fixed.
9. **A run starts the month after it is planned** *(planner says so, v1.7)* - the plan is taken at
   the end of the tick, after `train_step`. Harmless, but the planner says
   "lands in ~3 months" and it lands in 4. Either move the ask before
   training or say so.

10. **You run out of data early, and there is nowhere to get more** *(fixed v1.7)* (Nick,
    playing v1.6 with the data panel open). The market is ten sources,
    three free, none of which grow; there is no synthetic data, no
    expanding crawl, no steady flow of licensing deals, and telemetry only
    once you have customers. A 2023-scale run wants ~10T tokens; the free
    corpora are ~15T effective and the mixture shares split them. Real
    labs solved this from 2023 with synthetic generation (a compute-for-
    data trade that should be an *action*), crawls that grow with the web,
    and dozens of deals. This is world-engine work (`ROADMAP.md` v2, B):
    the data market needs supply that responds to demand and to time, and
    a `synthesize` order that spends training compute to make tokens for a
    domain at a quality set by the model you already have.

11. *(b fixed v1.7)* **Pointing compute at a domain you have no data for makes it worse,
    and the optimum is 0.01** (Nick). Correct in direction - the share
    trains on nothing (`data_sufficiency` floor 0.02) and is taken from the
    donors it borrows from - but two things are wrong: (a) the page called
    it "mixture" as if it were a wish list; now says "you hold no data,
    this share trains on nothing" (v1.6.2). (b) A domain with a *sliver*
    of data scores below one with none: `raw * (1 + ln epochs)` falls under
    the 0.02 floor for raw < ~0.008. One line (`max(0.02, ...)`), changes
    realisations, measure it. The real cure is #10: a way to get data.

**Playtest findings from the first scripted games** (this is the list the
next session should start from; each is a model finding, not a UI one):

1. **Labs cannot die, and the letter has to shout about it.** A frozen-
   orders player is insolvent by 2021 and keeps operating; the letter now
   prints `** INSOLVENT **`. `PREMISES.md` structural issue 5. A game
   needs a rule: forced fire-sale, acquisition, or game over.
2. **`model.capability` changes meaning after the first point upgrade.**
   At ship it is the headline index; `maybe_post_train` overwrites it with
   `max(caps)`, which is lower for any model with a spread mixture. It is
   commented "for reporting only" but `frontier_capability()`, the
   close-rival count in `set_price` and the narrative valuation all read
   it. Pick one definition. (The game already displays best-domain
   consistently; `ships[3]` now records that too.)
3. **The opening is a stampede.** Every lab ships in 2020-02 and again in
   2020-03. Fine for the GPT-3 checkpoint (−4 months); as a game the first
   turn has no decision in it. Consider a staggered first run.
4. **The wage rate falls from $900k to $371k in month 1.** The $900k was
   a placeholder (fixed — the opening rate is now the real one), but the
   real 2020 rate of ~$370k against a per-strategy opening offer of $810k
   still reads oddly. Check `talent.market_comp` at m=0.
12. *(fixed v1.12 - the flagship run's share of the lane is an era
    track; see CHANGELOG.md)* **The sim's capability runs ~15 points (a year and a half) early,
    and the demand curve was fitted on top of it.** Exposed by the
    labour-market demand model (v1.11, `ECONOMY.md` 6): pinned to the
    real GPT-4 = 100, it gives ~10x the calibrated spend curve in
    2023-25 because the sim is at 113 in 2023. The capability checkpoints
    have said -10 to -18 months since v1.0; the spend curve absorbed it.
    Fix at the source - the reasoning multiplier or the algo-efficiency
    track are the candidates - then re-fit `SPEND_*` and flip
    `DEMAND_MODEL`. Until then the labour model is observed only.

*v1.8.1: purchases are instant (`World.buy_now`; accelerators, power,
a round, a corpus) - cash moves when the button is pressed, logged and
replayed before the tick. Power headroom for chip orders now counts
pipeline power landing by the time the chips would (you order chips to
arrive with the power). Measured: checkpoints -9 / 8.9 / -19 / 15 of 16
/ 113; balance 50-89%, 6.1 of 7 viable, 4% runaways, 73 lead changes.*

*6 and 7 done in v1.8 - see WORLD_MODEL.md 2c "Between runs". Measured:
checkpoints median -6 / mean 9.0 / worst -23 / 15 of 16 / order 110
(was -9 / 8.5 / -18 / 16 / 113); balance 53-91% of goals, 69 lead
changes (86: fewer runs a decade, which was the point), 5.4 of 7 viable
(5.7), 4% runaways (8%). Two lessons paid for on the way: fear must not
run through cadence (the constants file already said so), and idle
compute routed to research at 0.5 of the lane made the leaders run away
(17% runaways, 5.0 viable) - it is 0.2.*

6. **`ship_cooldown` is a fitted timer doing a mechanism's job** *(fixed v1.8)* (Nick,
   playing: "shouldn't you always be training?"). It stands in for
   post-training, evals, launch, cluster build-out and recipe design, and
   it is what makes release cadence match history. Replace the timer with
   reasons: post-training and the next run compete for the same compute
   and people; a run started before the new cluster lands is small; a
   recipe with no research behind it lands badly. Then "always training"
   is a legal strategy with a real price. Must re-pass the cadence
   checkpoints for the *reasons*, not by the timer. Same shape as the
   run-size ceiling in `PREMISES.md`.
7. *(fixed v1.8)* **Post-training is not a decision.** 1-3 automatic x.5 releases per
   base model, free of explicit cost. Should be a player call with a
   compute and people cost (Nick asked; deferred at his request).
5. **Frozen orders are a bad player.** Left alone from the strategy's
   opening book, the player lab does not panic, does not raise comp, does
   not buy data beyond the first corpus, and lags the AI running the same
   strategy. Expected — the point is that a human steers — but it means
   the opening book should probably include the strategy's data priority
   list rather than a single `data_buy`.

## What is verified, and what is not

**Verified.**

*The refactor was mechanical.* Commit 1 (`08c42cf`) is bit-identical to
v1.3: three full 132-month exports (historical seed 0, randomised seeds
7 and 11) and the five-seed checkpoint table match the pre-refactor output
exactly. Two things had to be got right to achieve that and are worth
knowing: a lab's auction bids are computed with the cash left *after* this
month's non-exclusive licence (the old code spent first, then bid), and
`ship_cooldown` is allowed to go negative in `Actions` because the doctrine
cut can exceed the base and the world floors it at one month.

*The seam is complete.* `python3 -m sim.replay`: a `ReplayPolicy` with no
doctrine and no observation reproduces the recorded run bit for bit on
seeds 0 (historical) and 7 (randomised), through a JSON round trip of the
save. Four illegal actions are refused. This is the check to run after any
change to `world.py`.

*Calibration survived the realisation change.* Commit 2 moved the eval
roll to `rng_policy`, which changes every run's dice. Over five seeds:
15/16 inside ±18 months, median −10, mean |offset| 9.4, worst −22, order
113/120 (was 15/16, −10, 9.4, −24, 111/120). Balance over 24 seeds: eleven
strategies at 54–89% of their own goals (was 60–95%), 86 lead changes a
run (was 90), 5.8 of 7 viable (was 5.7). Same standing; the movement is
seed noise. `results_checkpoints.txt` and `results_balance.txt` are
regenerated.

**Not verified.**

- The safety severity gradient and the paired careless/diligent A/B from
  v1.3 were not re-run. The gradient is gated on capability, not on dice,
  so it should be unchanged; the A/B numbers (mean +$27B, ahead in 51/84)
  will have moved with the realisation and should be re-measured before
  anyone quotes them. `scratchpad/ab.py` from last session was never
  committed; the paired-lab shape is described in `CLAUDE.md`.
- "An enterprise agent market opens" is still outside the band, at −22
  (was −24), on a different realisation. Two different draws both landing
  two years early says this is structural, not noise. It is the first
  calibration item to look at, and it is not the regulation gate.
- `sim/checkpoints.py:85` still reads `doctrine["run_months"]` to estimate
  cluster size. It is an instrument, not a decision, and switching it to
  the window actually used (`lab.run_window`, threat-compressed) would
  move the 100k-cluster checkpoint for a non-model reason. Left alone,
  flagged.

## Where the bodies are buried

- **Floating-point order matters for bit-identity.** Moving an expression
  from the world into the policy is only exact if the operands multiply in
  the same order. I kept the original left-to-right forms; if you refactor
  one and the golden diff starts showing ±1 in the third decimal, this is
  why, and it is not a bug.
- **`Actions.diff` logs only what changed**, and threat moves every month,
  so `run_months`, `comp_offer`, `ship_cooldown` and `capex_aggression`
  log every month for every lab (~900 entries a run). Fine for a save
  file; if a viewer shows the log it should filter those.
- **Runs are slow.** ~8 s each. `sim.balance 24` is ~3.5 min,
  `sim.checkpoints` ~1 min, `sim.replay` ~35 s. Same advice as before:
  budget for it, do not iterate interactively on a full sweep.

## What I would do next, in order

Written Sep 15 2026 after the second batch (v1.21-1.28; `CHANGELOG.md`
has each step with its numbers). The sector instrument stands at timing
median -5 / mean 5.9 / worst -16 / 16 of 16 / order 113, magnitude
2.09x (power 1.85x, frontier 2.4x). Demand comes from the four blocs'
labour markets; the AI labs buy in the hardware market and one owns
its silicon; the world state acts on compute access, power, capital and
regulation, and mood and rules move on their own. Labs can die.

1. **Nick reviews `CHANGELOG.md` v1.12-1.28** and plays a decade. Things
   to look at: HYPERSCALER's goals (~55-67%), runaways (4-17% depending
   on the batch - watch whether the cost-led lab on the cheaper chips
   runs away), the 2022 frontier run still ~6x the record, and whether
   the labour-market demand feels right in play (the World tab shows it
   against the old curve and booked revenue).
2. **The three tier instruments** (`sim.hardware_checkpoints`,
   `sim.econ_checkpoints`, and WORLD_STATE.md 6 which has no script yet)
   should be run and pinned like the sector one; write the geo one.
3. **Diplomacy** (HARDWARE.md 4): exclusive supply, prepayment for slots,
   funding a designer's next generation - the entities have books now.
4. **Named people** and **charters** (ROADMAP D): the organisation layer.
5. **The map** (ROADMAP E): blocs exist; there is something to draw.

Standing checks after any change to `world.py`: `python -m sim.replay`
(must say "seam holds"), then `sim.checkpoints`, and the tier
instruments if the change touches them.
