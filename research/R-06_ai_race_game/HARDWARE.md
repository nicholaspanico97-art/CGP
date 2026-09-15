# The hardware supply chain — design and initial parameters

Written Sep 14 2026 (Nick's direction): build the world outward from what
the labs already need every month. A fleet is not "accelerators"; it is
chips that need wafers, memory, packaging and power, sold by companies
with their own books and their own designs. Dominance is not scripted.

**v1.15 status: step 1 of §5 is wired.** The chip a lab buys is still
the year's best from `constants.ACCELERATORS`, but its **price** is list
× the incumbent's margin against its normal 60%, and its **lead time**
is the incumbent's backlog (3-14 months) — `World.market_terms`. So the
2024 crunch now reaches the labs: chips cost more and arrive later while
the backlog runs. Steps 2-4 (choose a supplier; capacity from sector
capex; in-house silicon) are not wired. The tier is fed the sim's real
order flow and checked against §6 (`results_hardware.txt`).

## 1. Three tiers, each with entities that have books

### Foundries
Own leading-edge **wafer** capacity and **advanced packaging** capacity
(CoWoS-type — the 2023-24 bottleneck was packaging, not wafers). Capacity
grows only from capex, landing 30 months later; capex is triggered by
sustained utilisation. A foundry sells slots to designers.

| Foundry | Wafers, k/mo (2020) | Packaging, k/mo | $/wafer | Node lead | Notes |
|---|---|---|---|---|---|
| Tessera (leader) | 120 | 4 | 17,000 | 0 | MED. The only advanced packaging until 2024 |
| Halden (follower) | 40 | 0 → 2 (2024) | 13,600 | −1 node | MED |
| Jinhua (domestic China) | 15 | 0 → 1 (2025) | 9,000 | −2 nodes | LOW. +25%/yr after controls, on state capex |

### Memory makers
**HBM** is its own product with its own capacity and price. Capacity lags
18 months; price follows demand/capacity.

| Maker | HBM, EB/yr (2020) | $/GB | Notes |
|---|---|---|---|
| Sora Memory | 0.035 | 25 | MED. The volume leader (HBM2, 2020) |
| Nordmark | 0.025 | 27 | MED. Wins share on the next HBM generation |

### Chip designers
Each has a **current generation** for sale, a **next generation** in
development, an R&D rate, a chosen margin, foundry bookings, a backlog and
therefore a lead time. Revenue is what labs buy; R&D is what it reinvests.

| Designer | Bloc | Shipping (2020) | Next lands | R&D, % rev | Gross margin | Notes |
|---|---|---|---|---|---|---|
| Aurex (incumbent) | US | V100-class | A100-class, 2020-05 | 25% | 60% | HIGH. Software moat as a stickiness term |
| Vega Silicon (challenger) | US | one generation behind | 2021-06 | 35% (floor $1.5B/yr from other lines) | 40% | MED |
| Lattice (in-house, hyperscaler) | US | TPU-class, not for sale | feeds its parent's lab | n/a | n/a | MED |
| Huaxin (domestic China) | China | two generations behind | 2022-03 | 30% (floor $1B/yr, state) | 35% | LOW. The only seller into China after controls |

A chip: `(name, lands, peak_tflops, watts, hbm_gb, die_mm2, foundry, node)`.
Cost = die area / usable wafer area × wafer price + HBM × $/GB + packaging.
Price = cost / (1 − gross margin). **Perf/W steps ~1.5-2.2× per generation**,
the larger step only when the designer's foundry has moved a node.

## 2. What labs will need (once wired, §5)

A purchase becomes **a supplier, a generation, a quantity** with a lead
time set by that supplier's backlog against its packaging slots. A
20,000-chip order from a designer with no slots is a 14-month wait; a
worse chip in stock is 5 months. Power is unchanged. Export controls
(from `geo`) decide which designers may sell to which bloc.

## 3. The chip companies' rules (their `Policy`, same seam)

Deterministic; they draw no randomness, so replay is unaffected.

- **Demand allocation.** The sector's monthly chip demand splits across
  sellers by a logit on perf per dollar, lead time, and the incumbent's
  software stickiness; a bloc under controls can only buy from sellers
  allowed to sell to it.
- **Price.** Margin rises 2 points a month while backlog exceeds 6
  months, falls 2 while under 3, bounded [25%, 75%].
- **R&D.** A fixed share of revenue, plus half again when a rival's
  current generation leads on perf/W. A generation lands when
  accumulated R&D reaches the generation's cost (rising 1.6× each time)
  and at least 20 months have passed.
- **Booking.** A designer books foundry wafers and packaging in
  proportion to its trailing order book; slots are rationed pro rata
  when oversubscribed - this is what makes lead times.
- **Foundry capex.** Utilisation above 90% for 12 months → +25% wafer
  capacity, landing 30 months later. Packaging is built on forecast:
  three months above 70% → a doubling, landing 12 months later.
- **Memory.** Price = base × (demand / capacity)^0.8; capacity +30% when
  utilisation above 90% for 9 months, landing 18 months later.

## 4. Later: diplomacy

Exclusive supply, prepayment for slots, a lab funding a designer's next
generation, a bloc subsidising its fab, a lab starting its own chip
programme (huge R&D, long lead, no margin paid). These are deals between
entities that already have books; nothing here needs to be designed for
them now, only not designed against them.

## 5. Wiring order (each against §6 before the next)

1. Lead time and price of the chip labs buy come from the incumbent's
   backlog and margin instead of a constant 5 months and list price.
2. Labs choose a supplier and generation; `supply_share` becomes each
   lab's bloc access × its sellers' slots.
3. Foundry and memory capacity respond to sector capex (ROADMAP item 8).
4. In-house silicon as a lab decision.

## 6. The instrument — what the tier must reproduce on its own

| Anchor | When | What the tier must show |
|---|---|---|
| Incumbent holds ~80% of accelerator revenue | 2020-2024 | Aurex share ≥ 75% every year to 2024 |
| Lead times peak | 2023 | Aurex lead time ≥ 9 months in 2023, back under 6 by late 2024 |
| Packaging ×8 | 2022 → 2025 | Tessera packaging 8k → 60k+ /mo |
| HBM price doubles | 2024 | $/GB ≥ 1.8× the 2022 level during 2024 |
| Controls cut China off | Oct 2022, Oct 2023 | China-bloc purchases from US designers → ~0; Huaxin the only seller |
| Challenger reaches parity on perf/W | 2024-25 | Vega Silicon within 15% of Aurex on a generation, share ≥ 10% |
| Sector capex drives fab capex | 2023 → 2026 | Tessera leading-edge capacity +25% by 2026, landing 30 months after utilisation saturates (LOW) |

Same criteria as `PREMISES.md`: timing, order, magnitude within an OOM,
shape.

## 7. First measurement (v1.10, `results_hardware.txt`)

Historical roster: 4 of 7 anchors hold (HBM doubling, challenger parity,
controls, fab capex); the three misses are near — incumbent 73% in 2024
against 75%, a 7-month lead-time spike against 9, packaging ×9 but 36k
against 60k. On a randomised roster the lead-time spike lands in
mid-2025 rather than 2023-24: **the sim's sector buys about half the
chips the real 2023 sector did, a year later** — the same fact the
100k-cluster and 10 GW checkpoints show from the demand side. That is a
sector-demand finding, not a supply-chain one, and it is the first thing
to fix before the tier is wired in (§5). Three supply-side rules were
set on the way and are recorded in §3: packaging is built on forecast,
the challenger and the domestic designer have R&D floors from other
lines, and a leading-edge fab runs ~82% busy without AI.
