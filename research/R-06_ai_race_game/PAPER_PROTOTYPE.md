> **SUPERSEDED — Sep 11, 2026.** Nick's direction changed the approach:
> model the world at high fidelity in real units first, run the simulation,
> and make the game a window onto it. See `WORLD_MODEL.md`. This document is
> kept because its kill-gate discipline and its demand/incident structure
> still apply, but its abstract "compute units" do not — that abstraction was
> exactly the thing that could not express a decade spanning six orders of
> magnitude.

# Frontier — P0 Paper Prototype
### 12 turns · one charter · two rivals · pencil, paper, two d10

**Purpose:** answer one question before anything is built — *is the
compute split agonizing with no art, no UI, and no atmosphere?* If it
isn't, R-06 dies here for the cost of a weekend. See §10 for the
falsification criteria.

**Play time:** ~90 minutes. **Players:** 1.

---

## 1. The slice

**Q1 2022 → Q4 2024.** Twelve quarters.

Not 2020. The compute split is only interesting once *serving paying
customers* competes with *training the next model* — which needs a
market to exist. Starting in 2022 puts the player in the pressure
immediately instead of spending four turns with no revenue. The 2020–21
opening is a real part of the game; it just isn't what P0 is testing.

**You are:** a venture-backed lab, one year old, holding a modest
cluster and a reputation. You name it.

**Your rivals:**

| | **VAST** *(The Scaler)* | **Kestrel** *(The Product Lab)* |
|---|---|---|
| Doctrine | Compute above all. Prices Premium, doesn't chase share, out-trains everyone | Ships first, worries later. Best distribution, goes Aggressive on price from 2023 |
| Start | CAP 104 · 14 CU · Reliability 2 | CAP 98 · 10 CU · Reliability 4 |
| Threat | Out-scales you by 2024 | Takes your customers by undercutting you |

---

## 2. Components

- **Play sheet** — one row per turn (§11 layout).
- **Scoreboard** — published AA for all three labs, every quarter. Keep
  this visible at all times. It is the emotional centre of the game.
- **Two d10** (or one, rolled twice).
- **Event deck** — twelve cards (§8), cut up and shuffled.
- **Rival tracks** — §7, pre-computed.

---

## 3. Starting position

| | |
|---|---|
| Cash | **$400M** |
| Compute owned | **8 CU** (compute units per quarter) |
| CAP (capability) | **100** |
| A (efficiency) | **1.00** |
| Reliability | **3** (of 5) |
| Trust | **50** (of 100) |
| Safety Debt | **0** |
| Dilution | **1** |
| Price posture | Standard |
| Train bank | 0 |
| Experiment bank | 0 |

---

## 4. The turn

Seven steps. Steps 2 and 3 are the game; everything else is bookkeeping.

### Step 1 — Draw an event
Flip the top event card. Apply it now unless it says otherwise.

### Step 2 — Buy compute *(optional)*
- **Rent:** $8M per CU per quarter. Available immediately, cancel any
  time. Maximum **+6 CU** rented (chip scarcity), unless an event says
  otherwise.
- **Build:** $30M per CU, one-time. Arrives **two turns later**, then
  costs $4M/qtr like the rest of your owned fleet.
- **Owned compute costs $4M per CU per quarter**, whether you use it or
  not. Rented costs $8M. Write the total in the Costs column.

### Step 3 — Split the cluster ← *the decision*
Divide **all** your CU this turn among three lanes, in whole units:

| Lane | Effect |
|---|---|
| **TRAIN** | Add the CU to your Train Bank. |
| **SERVE** | Capacity for customers. Resolved in step 5. |
| **EXPERIMENT** | Add the CU to your Experiment Bank. Every **4 CU** banked converts to **A +0.15** (keep the remainder). |

Unallocated CU is wasted and still costs money.

### Step 4 — Actions *(any or none)*
- **Set price posture:** Premium · Standard · Aggressive. Takes effect
  this turn.
- **Ship a model.** Requires a Train Bank. Effective size = **Bank × A**
  (round to nearest). Look it up:

  | Effective CU | 3 | 5 | 8 | 12 | 18 | 27 | 40 | 60 | 90 |
  |---|---|---|---|---|---|---|---|---|---|
  | **New CAP** | 103 | 110 | 118 | 126 | 134 | 142 | 150 | 158 | 166 |

  Use the highest row you meet or exceed. CAP only ever goes up. Ship
  empties the Train Bank.
  - **With a safety eval:** costs 2 CU from this turn's allocation and
    delays the ship by one turn. Reliability **+1** (max 5).
  - **Without:** ships now. Safety Debt **+2**.
- **Safety work:** $25M → Safety Debt −1. Once per turn.
- **Raise capital:** once every three turns. You get **$500M** if you
  are AA rank 1, **$300M** at rank 2, **$150M** at rank 3. Trust ≥60
  adds $100M; Trust ≤35 subtracts $100M. **Dilution +1.**
  At **Dilution 4+**, if your revenue fails to grow for two consecutive
  turns, the board removes you. Run over.

### Step 5 — Resolve the market
1. **Compute AA for all three labs:**
   `AA_true = (CAP − 60) × 0.8 + Reliability × 2` — round to nearest.
2. **Roll d10 noise for each lab, separately**, and write the *published*
   number on the scoreboard:

   | d10 | 1–2 | 3–4 | 5–6 | 7–8 | 9–10 |
   |---|---|---|---|---|---|
   | **AA** | −2 | −1 | 0 | +1 | +2 |

   The published number is the only one the market sees. Yours included.
3. **Rank by published AA.** Ties broken by CAP.
4. **Weight each lab:** 1st = **1.00**, 2nd = **0.60**, 3rd = **0.35**.
   *If 1st leads 2nd by 6 or more, 1st becomes **1.40** instead.*
5. **Multiply** by price posture — Premium **×0.6**, Standard **×1.0**,
   Aggressive **×1.5** — and by **Trust ÷ 50** (minimum ×0.4).
6. **Share** = your weight ÷ total weight.
   **Demand** = Market Size × share, rounded.

   | Turn | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
   |---|---|---|---|---|---|---|---|---|---|---|---|---|
   | **Market (CU)** | 3 | 4 | 5 | 6 | 8 | 10 | 13 | 16 | 20 | 25 | 30 | 36 |

7. **Serve it.** Served = min(your SERVE allocation, Demand).
   - **Revenue per CU served:** Premium **$14M** · Standard **$10M** ·
     Aggressive **$6.5M**.
   - **If SERVE < Demand:** capacity crunch. Reliability **−1**,
     Trust **−3**.
   - **If SERVE > Demand:** the excess is wasted. You paid for it and
     could have trained with it.

### Step 6 — Money
```
Revenue  −  compute costs  −  payroll  −  purchases  =  net
payroll: $30M/qtr in 2022 (T1–4) · $45M in 2023 (T5–8) · $60M in 2024 (T9–12)
```
Cash below zero at end of turn = **insolvency, run over.**

### Step 7 — Incidents
Roll d10. **If the roll is ≤ your Safety Debt, an incident fires.**
Roll again for severity:

| d10 | Tier | Effect |
|---|---|---|
| 1–6 | **1** | Trust −8, Reliability −1 |
| 7–9 | **2** | Trust −12, cash −$80M, Safety Debt −1 |
| 10 | **3** | *(unless Tier 4 applies)* Trust −20; your demand is **halved for two turns**; *every* lab permanently loses $2M revenue per CU to compliance |
| 10 | **4** | Replaces Tier 3 **only if** Safety Debt ≥8 **and** CAP ≥140. Catastrophic. **Run over.** |

**Diffusion check — end of T4, T8, T12 only:** if your A is more than
0.30 below the highest A in the game, raise it to (highest − 0.30). You
are not allowed to fall permanently behind on efficiency, and neither
are they.

---

## 5. The two clocks

Write these at the top of every turn, before you decide anything:

- **RUNWAY** = cash ÷ last turn's net burn, in quarters.
- **GAP** = your published AA minus the best rival's published AA.

The game is the argument between those two numbers.

---

## 6. What P0 deliberately leaves out

Not forgotten — excluded, so twelve turns stay playable with a pencil.

**Out:** talent and hiring (payroll is a flat schedule) · data quality
and provenance · power and interconnect · government standing and export
controls · the other five charters · the five market segments (one
blended market instead) · modality coverage in the AA formula · Eras IV
and V, including the Automate lane · benchmark saturation and retirement
· legal exposure · concentration risk.

**In, because it's what we're testing:** the compute split · the
published benchmark index with noise · demand keyed to published rank ·
gross margin and runway · safety debt as a tail risk · two rivals with
opposed doctrines.

---

## 7. Rival tracks

P0 tests *your* decisions, not rival AI. These are pre-computed so a
turn takes seconds. Fidelity in rival behavior is a P1 problem, solved
by running them through the real simulator under their own doctrine.

### VAST — *The Scaler* · prices **Premium** all game · Reliability **2**

| Turn | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 14 | 14 | 16 | 16 | 18 | 20 | 20 | 24 | 26 | 28 | 32 | 34 |
| CAP | 104 | 104 | 104 | 104 | **122** | 122 | 122 | 122 | **140** | 140 | 140 | **152** |
| A | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.15 | 1.15 | 1.15 | 1.15 | 1.15 | 1.30 | 1.30 |

**Reacts:** if your published AA leads VAST's for two consecutive turns,
VAST rents +4 CU immediately and pulls its next ship one turn earlier.

### Kestrel — *The Product Lab* · Reliability **4** · Standard, then **Aggressive from T6**

| Turn | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CU | 10 | 11 | 12 | 14 | 16 | 18 | 21 | 24 | 27 | 30 | 33 | 36 |
| CAP | 98 | 98 | 98 | **112** | 112 | 112 | **124** | 124 | 124 | **134** | 134 | **141** |
| A | 1.00 | 1.00 | 1.00 | 1.15 | 1.15 | 1.15 | 1.15 | 1.30 | 1.30 | 1.30 | 1.30 | 1.45 |

**Baked in:** on **T8** Kestrel takes a Tier 2 incident — Trust 50→38
for four turns. Your window.
**Reacts:** if you go Aggressive, Kestrel goes Aggressive the following
turn and never goes back.

Both rivals start at Trust 50. Events move it; otherwise it holds.

---

## 8. Event deck — twelve cards, one per turn, no replacement

1. **Chip allocation cut.** Rental cap drops to +2 CU for three turns.
2. **Open weights.** Someone releases a near-frontier model free. All
   revenue per CU served drops **$2M** for three turns.
3. **Viral quarter.** Market size **+40%** this turn only. Everyone who
   has capacity feasts; everyone who doesn't takes the crunch penalty.
4. **Benchmark contamination allegation.** The lab with the highest
   published AA re-runs under supervision: −3 AA next turn, Trust −10.
5. **Enterprise whale.** The lab with the highest Reliability wins a
   contract worth **$120M** paid over three turns.
6. **Talent raid.** Pay **$60M** or lose 0.15 from your A.
7. **Power constraint.** Any lab above 24 CU pays **+$3M per CU** this
   turn and next.
8. **Data lawsuit.** Trust −10 and **−$100M** for whichever lab shipped
   most recently.
9. **Cloud prepay offer.** Take **$250M** now against three turns of
   serving revenue at half rate. Your call, this turn only.
10. **Regulatory inquiry.** Every lab with Safety Debt ≥4 loses $50M and
    Trust −8.
11. **Research breakthrough, published.** All three labs gain **A +0.15**.
    Being clever is temporary; the field catches up.
12. **Key departure.** Your next ship is delayed one turn. No exceptions.

---

## 9. Scoring at the end of T12

| Axis | Points |
|---|---|
| **Frontier** | 30 if you end as AA rank 1 · 15 if rank 2 · 0 if rank 3. **+10** if you ever held rank 1 for three consecutive turns |
| **Commercial** | Cumulative gross profit ÷ 10, floor 0, capped at 40 |
| **Stewardship** | (10 − final Safety Debt) × 2, minus 5 per incident tier suffered |
| **Endurance** | 20 if solvent at Dilution ≤2 · 10 if solvent at Dilution 3–4 · 0 if you took the prepay bailout or were removed |

Total out of ~100. The score is not the point. The playtest log is.

---

## 10. The kill gate

P0 passes only if **all four** hold. Write the answers down during play;
don't reconstruct them afterward.

1. **The split moves.** In at least **8 of 12 turns**, the allocation
   differs from the previous turn. A static split means a fake decision.
2. **Regret is nameable.** You can point at a specific turn and say what
   you should have done instead — *and* why it wasn't obvious then.
3. **The robot fails.** Play a second run on autopilot at a fixed
   40 / 40 / 20 split, no thinking, same seed order for the event deck.
   If the robot scores **within 10%** of your considered run, the
   mechanic is decorative and the project stops.
4. **The two-point loss lands.** At least once you lose AA rank by ≤2
   points on a noise roll and it genuinely annoys you.

Criterion 4 is the design's stated target feeling, so it is tested
directly rather than assumed. If losing by two points feels arbitrary
rather than infuriating, the noise band is wrong (try ±1) or the
consequence is too weak (try widening the rank weights).

**If P0 fails:** the honest options are to make the lanes less
substitutable, raise the stakes on being wrong, or shelve R-06. Not to
add features.

---

## 11. Play sheet layout

One row per turn. Print twelve.

```
T__  YEAR 20__  Q_          RUNWAY: ___ qtrs      GAP: ___ AA
EVENT: _______________________________________________________

COMPUTE   own ___  rented ___  total ___      arriving next: ___
SPLIT     TRAIN ___   SERVE ___   EXPT ___    (must total CU)
BANKS     train ___   expt ___ (÷4 → A)       A = ____
ACTION    price: PREM / STD / AGGR    ship? Y/N   eval? Y/N
          safety $25M? ___   raise? ___

SCOREBOARD        CAP    Rel   AA_true   d10   AA_PUBLISHED   rank
  you            ____   ____   ______   ___   ____________   ____
  VAST           ____   ____   ______   ___   ____________   ____
  Kestrel        ____   ____   ______   ___   ____________   ____

MARKET    size ___  weight ___  share ___  demand ___  served ___
MONEY     revenue ___  compute ___  payroll ___  other ___  NET ___
          cash after: ___
STATE     Trust ___  Reliability ___  Safety Debt ___  Dilution ___
INCIDENT  d10 ___  vs SD ___  →  ______________________________

NOTE (one line: what you wish you'd done)
_______________________________________________________________
```

---

## 12. Notes for the playtest log

Keep these as the run goes. They are the actual output of P0 — the score
isn't.

- Which turn was the hardest split, and why.
- The first turn you knowingly under-served demand to keep training.
- The turn you first considered pricing below cost, and what stopped you
  or didn't.
- Every AA loss of ≤2 points, and how it felt.
- Anything you had to look up twice — a rules-clarity bug.
- Anything you computed on autopilot — a mechanic that isn't earning its
  place and should be cut before P1.

---

*Design: `DESIGN.md` in this folder. P0 is rules on paper by
intention — no code until this gate passes.*
