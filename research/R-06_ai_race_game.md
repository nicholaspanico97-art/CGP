# R-06 — *Frontier*: an AI-race business simulation, 2020–2030

**Status:** design plan, pre-build. Nothing coded. For Nick's review.
**Filed:** Sep 11, 2026
**Working title:** *Frontier* (alt: *Scaling Laws*, *Compute*, *The Race*)

---

## 1. The pitch

You run one of a handful of frontier AI labs from Q1 2020 to Q4 2030.
Forty-four quarterly turns. You start with a research team, a modest
cluster, a charter, and a thesis about how intelligence scales. By 2030
you are either the lab that got there, the lab that got bought, the lab
that got regulated out of existence, or the lab that blew it up for
everyone.

The fantasy isn't "build a tech company." It's **being at the controls
during the most compressed technology race in history, with worse
information than you want and less compute than you need.**

### Why this premise works as a game

Most business sims are boring because the optimal play is stable:
maximize throughput, minimize cost, repeat. The AI race is a good game
subject because it has four genuinely unresolved tensions, all of which
map to mechanics rather than flavor text:

1. **Every unit of compute has three jobs and can only do one.** Train
   the next model, serve today's customers, or run the experiments that
   make the next training run cheaper. This is the whole game in one
   decision, repeated 44 times.
2. **Being ahead is not a moat.** Staff move, papers publish, weights
   leak, open releases collapse the price floor. Leads decay unless
   re-earned.
3. **Speed is rewarded continuously; recklessness is punished rarely
   and enormously.** Safety spending buys down a tail you cannot see.
   The greedy line is usually right — until it isn't.
4. **The thing you're building eventually does your job.** Late game,
   your own models start contributing to research. Whoever crosses that
   line first stops being on the same curve as everyone else.

---

## 2. Design pillars

| Pillar | What it means in practice |
|---|---|
| **Scarcity is compute, not money** | Money is a means of buying compute, and late-game money can't buy it at all (fab capacity, power, export rules). The binding constraint moves over the decade — that movement is the campaign's arc. |
| **Legible math, illegible world** | The player-facing numbers (compute, capability, margin) are exact and auditable. The world's reaction (public trust, regulators, rivals' intent) is noisy and lagged. |
| **No dominant strategy** | Six charters, each with a different win shape. A build that dominates in 2023 should be structurally fragile by 2027. |
| **Consequences arrive late** | Corners cut in turn 12 come due in turn 30. The game keeps a memory (Safety Debt, Trust, Legal Exposure) that the dashboard shows but does not price for you. |
| **Recognizable, not real** | Fictional labs and people with real-world texture. See §10. |

**Target session:** 3–5 minutes per turn, ~2.5–3 hours per campaign,
single player vs. AI rivals, turn-based, no real-time pressure.

---

## 3. Core loop

Each quarter:

```
1. INTEL      — news wire, rival estimates (noisy), market report
2. ALLOCATE   — split cluster: Train / Serve / Experiment  (the big one)
3. INVEST     — capex, hiring, data deals, safety, lobbying, fundraise
4. BUILD      — start/continue/ship a training run; set product & price
5. COMMIT     — end turn
6. RESOLVE    — rivals act, market clears, events fire, incidents roll
7. REPORT     — quarterly board letter: what moved and why
```

Target decision density: **6–10 meaningful choices per turn**, where
"meaningful" means at least two options are defensible.

---

## 4. Resources & meters

### Hard resources
- **Capital** — cash on hand. Sources: revenue, fundraising, partner
  prepay, government contract.
- **Compute** — owned clusters + rented capacity, measured in *Training
  Units (TU)/quarter*. Split three ways every turn (§5).
- **Talent** — headcount in three tiers: Juniors, Seniors, **Principals**
  (named, rare, large multipliers, poachable both directions).
- **Data** — a stock with a *quality* and a *provenance* rating. Licensed,
  scraped, synthetic, user-generated. Provenance feeds Legal Exposure.
- **Power** — contracted megawatts + interconnect queue position. Dormant
  until ~2026, then a hard wall.

### Soft meters (0–100, slow-moving, visible but not directly buyable)
- **Public Trust** — consumer demand, hiring appeal, regulatory mood.
- **Enterprise Confidence** — reliability and compliance track record.
- **Government Standing** — export licences, contracts, and whether the
  hammer falls on you or your rival.
- **Mission Alignment (internal)** — staff belief you're still the good
  guys. Low alignment → Principal departures, leaks, public letters.

### Hidden-ish accumulators (shown as a band, not a number)
- **Safety Debt** — untested capability shipped, evals skipped, red-team
  findings waived. Drives the incident tail.
- **Legal Exposure** — data provenance, copyright, privacy, contract risk.
- **Concentration Risk** — dependence on one chip vendor / one cloud /
  one customer. The thing that ends runs in a single event card.

---

## 5. The central mechanic: the compute split

Each turn you divide your available TU across three (later four) lanes:

- **TRAIN** — accumulates toward your next frontier model. A run has a
  declared target size; you can extend, cut short, or abort (sunk cost).
- **SERVE** — capacity for paying customers. Under-serve and you get
  outages, churn, and an Enterprise Confidence hit. Over-serve and you
  burned compute you could have trained on.
- **EXPERIMENT** — buys **algorithmic efficiency (A)**, the multiplier
  that makes every future TU worth more. Compounding, invisible in the
  short run, decisive over ten years.
- **AUTOMATE** *(unlocks ~2027)* — point your own agents at your research
  queue. Converts compute into A-growth at a rate that rises with your
  model's capability. This is the endgame flywheel.

This single screen should carry the game. If the split isn't agonizing
by turn 10, the balance is wrong.

---

## 6. Simulation model (v0 — starting numbers, expect heavy tuning)

Everything here is a first draft to be fitted in the headless simulator,
not a claim about reality.

### Capability
```
EC   = TU_train × A × D × Q          (effective compute of a run)
CAP  = 50 + 30 × log10(EC / EC_2020) (capability index)
```
- `A` — algorithmic efficiency. Starts 1.0. Compounds ~1.15×/yr at
  minimum investment, ~1.6×/yr at maximum, plus a **diffusion floor**:
  every lab drifts toward the ecosystem frontier at a rate set by how
  open the ecosystem is (open-weights releases, publishing norms, staff
  churn). Nobody keeps an algorithmic lead for free.
- `D` — data quality multiplier, 0.6–1.4.
- `Q` — team quality multiplier, driven by Principals and Mission Alignment.

Each 10× of effective compute buys +30 CAP. A full campaign should run
roughly CAP 50 → 220, gated into milestones (§7).

### Money
- **Serving cost per unit** falls with `A` and chip generation, rises
  with model size → margins get squeezed exactly when you most want cash.
- **Demand** per segment via a softmax over a value score:
  `value = w1·(CAP − frontier_CAP) + w2·(−price) + w3·reliability + w4·trust_segment`
- **Segments:** Consumer subscription, Developer API, Enterprise
  deployment, Government, Licensing. Different weights each — consumers
  chase brand and novelty, developers chase price/performance,
  enterprises chase reliability and compliance, government chases
  national standing and security posture.
- **Capex:** clusters depreciate on a ~4-year curve and a chip generation
  behind is a real handicap. Buy vs. rent is a live decision all game.

### Incidents
```
p(incident) = base × deployment_surface × capability_jump_since_eval
              × (1 − safety_effectiveness)
```
Severity tiers: **1** embarrassment (Trust hit) · **2** real harm
(lawsuit, Legal Exposure) · **3** systemic (sector-wide regulation,
often hurting you most) · **4** catastrophic (campaign-ending, rare,
reachable only through sustained Safety Debt at high CAP).

Safety investment lowers the **tail**, barely touching the mean. It has
to *feel* like insurance you resent paying, or the tension is gone.

---

## 7. Era structure & milestone ladder

The decade is five eras. Each changes which constraint binds, so the
optimal build has to be rebuilt roughly every two years.

| Era | Years | Binding constraint | Unlocks / pressure |
|---|---|---|---|
| **I — Thesis** | 2020–21 | Talent & conviction | Scaling bet, first large run, research reputation. Almost no revenue. |
| **II — Product** | 2022–23 | Serving capacity | Chat/assistant launch, developer API, sudden consumer demand, chip shortage, first real money and first real scrutiny. |
| **III — Reasoning** | 2024–25 | Cash & chips | Post-training and RL, inference-time scaling, agents, enterprise contracts, open-weight price collapse, export controls. |
| **IV — Industrial** | 2026–27 | **Power & fab capacity** | Multi-gigawatt sites, sovereign deals, agentic labor products, first serious regulatory regime, automation of parts of your own R&D. |
| **V — Transition** | 2028–30 | Legitimacy | Automated research flywheel, extreme concentration, nationalization pressure, endgame scoring. |

**Milestone ladder** (CAP-gated, first-to-claim gives a lasting bonus —
a "first mover" tag that shifts demand weights for several turns):
useful assistant · coding partner · reliable tool-use · long-horizon
agent · autonomous engineer · self-improving researcher.

---

## 8. Rival labs

Six to eight AI-run labs, each with a **doctrine** that drives its
policy, not a difficulty slider:

| Archetype | Doctrine |
|---|---|
| **The Scaler** | Compute above all. Out-trains everyone, ships late, terrible margins, terrifying by 2027. |
| **The Product Lab** | Ships first, worries later. High trust volatility, best consumer distribution, accumulates Safety Debt. |
| **The Opener** | Releases weights. Collapses your pricing, boosts the diffusion floor for everyone, monetizes indirectly. |
| **The Hyperscaler Division** | Infinite capital, slow decisions, owns its own compute and won't sell you any on good terms. |
| **The Safety House** | Slow, credible, wins Government Standing and enterprise trust; punishes you when the hammer falls. |
| **The National Champion** | State-backed, export-constrained, immune to public trust, wildcard after 2026. |
| **The Chip Vendor** *(non-lab actor)* | Not competing for models — setting the price of everything you do. |

Rival AI runs the same simulation you do (same resources, same rules, no
cheating) with doctrine-weighted objectives, plus a **diffusion** term
that keeps the field from spreading out into a non-game. Intel on rivals
is **noisy and lagged** — you see estimate bands, not truth, and the
bands narrow if you invest in intel (conferences, hiring, benchmarks).

---

## 9. Charters (start-of-game choice, big replayability lever)

Your charter sets starting resources, constraints, scoring weights, and
which failure modes are live:

1. **Capped Nonprofit** — mission constraints, board can remove you,
   cheap talent, hard to raise.
2. **Venture Startup** — fast capital, dilution and board seats,
   growth expectations that force early shipping.
3. **Big-Tech Division** — huge compute, slow approvals, internal
   politics, your products compete with your parent's.
4. **Open Foundation** — you *are* the diffusion floor; monetize via
   services and goodwill; permanently poor, permanently relevant.
5. **Sovereign Champion** — state capital, export walls, government
   standing trivial, public trust nearly irrelevant, borders matter.
6. **Safety-First Lab** — voluntary capability caps that *actually bind*,
   rewarded only in the endgame scoring. The hard mode with the best story.

---

## 10. Fiction policy

Fictional labs, fictional people, real physics and real economics. No
real company names, no real executives, no real logos. The satire is in
the *dynamics* — a board firing its CEO over a governance dispute, a
sudden open-weight release out of nowhere, an export-control shock — and
those are structural, not personal. An optional **Historical Almanac**
can show a post-game timeline of what actually happened each quarter, as
a reference layer rather than in-game content. Keeps it legally clean
and ages better than name-dropping.

---

## 11. Victory, defeat, and scoring

No single score. At end of 2030 the game produces a **Legacy Report**
across four axes, and names your run for whichever dominates:

- **Frontier** — peak capability, milestones claimed first.
- **Commercial** — cumulative profit, market share, enterprise footprint.
- **Stewardship** — incident record, safety contribution, whether the
  regime that emerged was one you'd want to live under.
- **Endurance** — still independent, still solvent, still you.

**Defeat states** (all should be reachable and all should feel earned):
insolvency · hostile acquisition · board removal · nationalization ·
regulatory shutdown after a Tier-3 incident · catastrophic Tier-4 ·
and the quiet one — **irrelevance**, where you're alive in 2030 and
nobody is using anything you make.

A campaign should be losable on turn 40 and should also be winnable
from last place on turn 20 if you read the era shift correctly.

---

## 12. UI / screens

`Dashboard` · `Compute` (the split, the headline screen) · `Research &
Milestones` · `Org & Talent` · `Products & Pricing` · `Markets` ·
`World & Policy` · `Rival Intel` · `Quarterly Report`.

Visual direction: a terminal-flavored operations console — dense, dark,
data-first, chart-heavy. Closer to a trading desk or *Papers, Please*
than a cartoon tycoon game. The quarterly board letter is the
personality: written, specific, occasionally brutal.

---

## 13. Technical plan

- **Deterministic, seeded simulation core**, fully separated from UI.
  Same seed + same inputs = same run, always. Non-negotiable — it makes
  balancing, replays, and bug reports tractable.
- **Headless mode first.** Before there is a single pixel, the sim should
  run 10,000 campaigns overnight with scripted policies so balance is
  measured, not guessed. (The same discipline as the R-01 backtest
  harness: the tool's job is to say "this strategy dominates" before a
  player has to discover it.)
- **All content data-driven** — events, milestones, charters, rivals as
  JSON/YAML, not code. Balance changes must not require a rebuild.
- **Stack:** TypeScript throughout. Sim core as a pure library, React +
  Canvas/SVG front end, runs in a browser, no backend for v1. Saves are
  JSON (seed + action log → replayable).
- **Testing:** golden-run snapshots, invariant checks (no negative
  compute, conservation of cash), and a balance suite that fails CI if
  any scripted policy wins more than X% of seeded runs.

---

## 14. Build phases

| Phase | Deliverable | Gate to pass |
|---|---|---|
| **P0 — Paper** | Rules on paper / spreadsheet, 12 turns, one charter, two rivals | Is the compute split interesting *without* any art? If no, stop here. |
| **P1 — Headless** | Full 44-turn sim, CLI, scripted policies, batch runner | No scripted policy wins >40% of seeded runs. |
| **P2 — Playable** | Minimal UI, one charter, full campaign playable end to end | A first-time player finishes a campaign and can explain why they lost. |
| **P3 — Content** | All six charters, full event deck, all rival doctrines, milestone ladder | Six charters produce visibly different games. |
| **P4 — Polish** | Board letters, Legacy Report, almanac, tutorial, audio | Replay rate: do testers start a second run unprompted? |

P0 is deliberately cheap and deliberately a kill gate. The premise is
strong; the risk is that the *mechanics* turn out to be a spreadsheet
with news headlines taped on. P0 answers that for a weekend of work.

---

## 15. Known risks

- **Spreadsheet trap.** If the optimal split is computable, the game is
  over. Mitigations: noisy rival intel, lagged consequences, era shifts
  that invalidate builds, event variance.
- **Runaway leader.** A lab that pulls ahead compounds. Mitigations:
  diffusion floor, talent mobility, scrutiny scaling with success,
  margin squeeze on the biggest serving footprint.
- **Preachiness.** The safety system must be a *risk instrument*, never a
  lecture. If the game tells the player what's right, it's failed; it
  should let them find out.
- **Reality drift.** The 2026–2030 half is speculative and 2026 is now.
  Mitigation: data-driven content, and a design that models *constraints*
  (compute, power, trust, talent) rather than predictions.
- **Scope.** Six charters × eight rivals × five eras is a lot of content.
  P0–P2 deliberately ship one charter and two rivals.

---

## 16. Open questions for Nick

1. **Audience:** personal project for its own sake, or is this a live
   R-03 candidate (something sellable)? That changes the polish bar a
   lot more than it changes the design.
2. **Scale:** one lab (this plan), or also a mode where you play the
   chip vendor / a nation-state regulator? Tempting, and a trap for v1.
3. **Depth vs. reach:** hardcore econ sim (my default here) or something
   lighter that a non-technical player finishes in 45 minutes?
4. **Multiplayer:** out of scope for v1 in this plan. Say if it isn't —
   hot-seat is cheap to keep on the table, networked is not.
5. **The 2026–2030 half:** grounded extrapolation, or willing to get
   weird (recursive self-improvement, hard takeoff, treaties)?
6. **Kill gate:** is P0 (paper prototype, one weekend) the right next
   step, or do you want the headless sim skeleton first?

---

*No code written. Awaiting review.*
