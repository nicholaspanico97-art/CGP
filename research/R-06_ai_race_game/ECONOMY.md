# The world economy — four blocs, and demand as a labour market

Written Sep 14 2026 (Nick's direction). `ROADMAP.md` thrust C, "the world
reacts to AI". Four blocs: **US, EU, China, rest of world** (the Gulf
stays a compute bloc in `geo.py`; for GDP it is part of RoW).

**v1.21 status: acting.** `DEMAND_MODEL = "labour"`: sector spend is the four blocs' realised AI spend x the labs' share (`LAB_SHARE_2025`). A pilots term (firms paying to try what they cannot yet deploy) carries the 2021-22 API-era revenue. Sector timing 16/16, order 114; revenue magnitude 2.6x (2024 high, 2026 low). *Original status note follows.*

**v1.11 status: observed, not acting.** `sim/econ.py` carries each bloc's
economy, steps it monthly, reads the AI sector, and computes what the
labour-market demand model *would* say — beside the capability curve
that still sets sector spend. The World tab shows both. The switch
(§4) flips only when the sector checkpoints hold with it on.

## 1. The blocs, January 2020

| | US | EU | China | RoW |
|---|---|---|---|---|
| GDP, $T/yr | 21.1 HIGH | 15.3 HIGH | 14.7 HIGH | 34.0 MED |
| Trend real growth, %/yr | 2.0 | 1.3 | 5.0 → 4.0 (2023) | 3.5 |
| Workforce, M | 160 HIGH | 200 HIGH | 780 HIGH | 2,300 MED |
| Knowledge-work share of jobs | 38% MED | 35% MED | 18% LOW | 15% LOW |
| Knowledge wage bill, $T/yr | 6.3 LOW | 4.1 LOW | 2.2 LOW | 5.1 LOW |
| Software & IT services spend, $T/yr | 1.2 MED | 0.6 MED | 0.4 MED | 0.8 LOW |
| Unemployment | 3.5% HIGH | 7.5% HIGH | 5.2% MED | 6.0% LOW |
| Enterprise adoption half-life, months | 14 | 20 | 12 (domestic products) | 24 |
| Consumer adoption half-life, months | 3 | 4 | 3 | 5 |

*Knowledge work*: jobs whose output is text, code, analysis, decisions or
coordination — the work a language model can do parts of. The wage bill
is the number the demand model is built on.

## 2. The mechanism

**Automatable share.** The fraction of knowledge-work *tasks* a model of
capability C (score scale: GPT-4 = 100) can do to an acceptable standard,
by task tier:

| Tier | Share of knowledge tasks | Half-point (score) | Width |
|---|---|---|---|
| Routine text: drafting, summarising, support | 30% | 105 | 8 |
| Analysis and code: structured problems with a checkable answer | 30% | 118 | 9 |
| Agentic: multi-step work in tools over hours | 25% | 130 | 10 |
| Expert judgment and coordination | 15% | 150 | 12 |

Each tier is a sigmoid in C. GPT-4-class ≈ 14% of tasks; ~120 ≈ 45%;
~150 ≈ 85%. (LOW — the shape is defensible, the half-points are guesses
pinned by §5.) **Deployable** is a second sigmoid (half 150, width 12):
a task the model can do acceptably is not one a firm has integrated
reliably — ~1.5% of GPT-4-class tasks, ~6% at 122, half at 150. This is
the number the 2023-24 adoption surveys pin (~5% of firms in production).

**Value unlocked** per bloc = automatable share × knowledge wage bill ×
capture × deployable. *Capture* is what a buyer pays of what it saves: 6% at first,
rising toward 20% as products become workflows (stickiness).

**Adoption friction.** Realised spend chases value unlocked with the
bloc's half-life — consumer fast, enterprise slow, EU slower under
regulation, China fast for domestic products only. This is the missing
piece behind "enterprise agents open two years early".

**Feedback.**
- Productivity: the year-on-year *increase* in realised spend × 1 lifts
  the bloc's growth that year — a level of spend adds a level of output
  once. (Was ×2; the negative anchor wants it barely visible to 2025.)
- Displacement: hours automated × (1 − re-employment rate) → knowledge
  unemployment, with a 12-month lag; wage pressure on knowledge work.
- Expansion: as agents get cheaper per task, the addressable work grows
  (substitution) — the pie grows past the wage bill it started from, at
  a rate set by price per task falling.
- Mood: displacement and incidents push public mood down; visible
  capability and cheaper services push it up. Mood moves regulation
  with a lag (`geo.py` blocs). Regulation gates agentic segments per bloc.

Eras fall out: chatbot (routine tier crossing) → agents (agentic tier) →
automation (expert tier + displacement visible). Nothing is scripted.

## 3. What it replaces

`World._sector_spend`: `$2B × 10^(0.45 × (C − 26.5))`, one number for the
world, adopted with a 12-month half-life, no friction, no feedback, no
blocs. Under the switch, sector spend = Σ blocs' realised spend, and the
nine segments' TAM shares are applied to that as before.

## 4. The switch

`K.DEMAND_MODEL = "capability" | "labour"`. Default stays "capability"
until, with "labour", the sector checkpoints (`sim.checkpoints`) hold at
least as well as now (median −9 / mean 8.9 / worst −19 / 15 of 16 / 113)
**and** §5 holds. Both are printed side by side on the World tab.

## 5. The instrument — anchors for the labour model

| Anchor | When | What the model must show |
|---|---|---|
| Consumer assistant reaches ~100M users | 2 months after the consumer gate opens (Nov 2022 → Jan 2023) | consumer-tier realised spend at ≥ 50% of unlocked within 3 months of the gate |
| Sector revenue $1B / $10B / $60B | 2023-06 / 2025-03 / 2026-06 | already in `sim/checkpoints.py`; must hold under "labour" — via the labs' share of world AI spend (`LAB_SHARE_2025` ≈ 0.12: lab revenue ~$26B against ~$250B of AI spend in 2025) |
| Enterprise AI spend ~$40B/yr | 2024 | enterprise segments' realised spend $25–60B in 2024 |
| AI ≈ 5% of US software spend | 2025 | US realised AI spend / software spend 3–8% in 2025 |
| **No measurable productivity effect** | through 2025 | bloc GDP growth within ±0.2 pt of trend through 2025 (a negative anchor) |
| Knowledge-work unemployment flat | through 2025 | ≤ +0.5 pt over trend by end 2025 |
| Enterprise agents market opens | 2025-06 | the checkpoint that has always been early must land within the band under "labour" |

Same criteria as `PREMISES.md`. Not fitted yet; this is the record of what
was assumed.

## 6. First reading (v1.11, historical roster)

| | 2021 | 2023 | 2024 | 2026 | 2030 |
|---|---|---|---|---|---|
| Frontier score (sim) | 105 | 113 | 124 | 148 | 180 |
| Labour model, $/yr | 9B | 82B | 429B | 2.4T | 6.1T |
| Capability curve, $/yr | 0.7B | 3.9B | 13B | 137B | 4.7T |
| Sector revenue, $/yr | 0.6B | 3.1B | 12B | 108B | 835B |
| US growth vs trend | +0.03 | +0.17 | +1.1 | +4.1 | +1.6 |
| US unemployment | 3.50 | 3.52 | 3.56 | 4.02 | 5.55 |

The negative anchors hold through 2023 and the two demand models
converge by 2030. In 2023-25 the labour model runs ~10x the capability
curve. **The cause is the sim's capability index, not the labour
model**: the tiers are pinned to the real GPT-4 = 100 in 2023, and the
sim reaches 105 in late 2021 and 113 in 2023 - the capability
checkpoints have read -10 to -18 months all along, and the spend curve
was calibrated on top of that earliness, absorbing it. The labour model
exposes it. So the switch (§4) waits on fixing the sim's early
capability at the source (HANDOFF.md finding 12), not on shifting the
tiers to match it.

**After v1.12** (the flagship-share fix): the sim's 2023 score is 113,
2024 is 124, ~a year ahead of the record; the labour model gives $67B /
$413B there. Read on the *real* timeline it is right where it can be
checked: at score ~110 (the real 2024 frontier) it gives ~$35B against
~$40B recorded. So what remains is the sim's residual year of earliness
in capability (checkpoints −6 to −13 months), plus a labs' share of AI
spend (the seven labs book perhaps a third of what the world pays for
AI; the rest is applications and cloud) that the switch will need. The
switch stays off until capability is within ±6 months of the record.
