# The world outside the labs — initial parameters

Written Sep 14 2026, for `ROADMAP.md` thrust B ("the world gets state").
The sim's "world" has so far been the AI sector: seven labs, one demand
curve, a fab table by year, one regulation scalar, and geopolitics as a
constant per lab (`supply_share`). This is the first cut of a world that
exists whether or not the player touches it. Every figure is a public
order-of-magnitude number for **January 2020**, tagged HIGH / MED / LOW
like `sim/anchors.py`; the exogenous tracks run to 2025 on the record and
are projected after.

**v1.25 status: acting on all five fronts of §5** - compute access through the hardware tier's per-bloc supply, power (v1.17), capital (rounds by appetite, debt by rate), demand (the labour model, v1.21), regulation per bloc. Each is a first cut with LOW-confidence constants; the anchors in §6 are the next thing to build as an instrument. *Earlier status notes follow.*

**v1.17 status: partly acting.** Step 2 of §5 is wired: a lab's
datacentre build lead is the greater of the greenfield build and its
bloc's interconnect queue (the US 24→48-month track), plus commissioning;
its leased power is priced at its bloc's industrial rate. The dated
events (§4) are announced in the player's event log as they happen.
Steps 1, 3-5 are not wired. *Original status note follows.*

**v1.9 status: observed, not acting.** `sim/geo.py` carries this state,
steps it monthly, and the dashboard's World tab shows it. Nothing in it
changes a lab's outcome yet. That is deliberate: the roadmap rule is
*instrument before content* — the state has to be visible and checkable
against the record before it is allowed to push on the sector. The
instrument is the dated anchors at the bottom.

## 1. Blocs

Five blocs. A lab belongs to one (`Lab.bloc`; by strategy for now —
SOVEREIGN in the Gulf, COST in China, OPEN in the EU, the rest in the US).

| | US | China | EU | Gulf | Rest of world |
|---|---|---|---|---|---|
| GDP, $T/yr (2020) | 21.1 HIGH | 14.7 HIGH | 15.3 HIGH | 1.6 HIGH | 32 MED |
| Real growth, %/yr | 2.0 | 5.0 → 4.0 | 1.3 | 3.0 | 3.5 |
| Knowledge-work wage bill, $T/yr | 6.3 LOW | 2.2 LOW | 4.1 LOW | 0.3 LOW | 4.8 LOW |
| Grid capacity, GW installed | 1,100 HIGH | 2,200 HIGH | 1,000 HIGH | 200 MED | 3,000 MED |
| Grid growth, %/yr | 1.5 | 8 | 2 | 5 | 4 |
| Industrial power price, $/MWh | 70 MED | 85 MED | 120 MED | 45 MED | 90 LOW |
| Interconnect queue, months (2020) | 24 → 48 by 2025 MED | 8 | 36 | 12 | 24 |
| Leading-edge accelerator access, share | 1.0 | 1.0 → 0.35 (Oct 2022) → 0.15 (Oct 2023) HIGH | 1.0 | 1.0 → 0.5 (2023) → 0.8 (2024-25 deals) MED | 0.8 |
| Public mood toward AI, −1..+1 | +0.1 | +0.3 | −0.1 | +0.2 | 0.0 |
| Regulatory stance, 0..1 | 0.1 → 0.35 (EO Oct 2023) → 0.2 (Jan 2025) | 0.3 → 0.5 (Aug 2023 rules) | 0.3 → 0.7 (AI Act Aug 2024) | 0.1 | 0.2 |

*Knowledge-work wage bill* is the number the demand model will eventually
be built on (thrust C): the share of GDP paid to people doing cognitive
work — roughly 30% in the US, 27% EU, 15% China. The current demand curve
(`_sector_spend`) is a function of capability alone; the labour market is
what it will be a function of.

## 2. Global supply

| | 2020 | 2022 | 2024 | 2025 | note |
|---|---|---|---|---|---|
| Leading-edge wafers, k/month (N7 and below) | 120 | 180 | 240 | 290 | MED; `FAB_OUTPUT_PER_MONTH` derives from this |
| Advanced packaging (CoWoS), k wafers/month | 4 | 8 | 35 | 75 | HIGH; the actual 2023-24 bottleneck |
| HBM supply, exabytes/yr | 0.2 | 0.5 | 1.5 | 3.0 | MED |
| Share of leading-edge going to AI | 8% | 18% | 45% | 60% | MED |

Fab capacity should respond to sector capex with a 2-3 year lag
(`ROADMAP.md` item 8); the 2020-25 column is the record, after that it
is what the sector's orders make it.

## 3. Capital

| | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| US policy rate, % | 0.1 | 0.1 | 4.3 | 5.3 | 4.4 | 3.9 |
| AI venture appetite, index (2020 = 1) | 1.0 | 1.6 | 1.2 | 2.5 | 3.5 | 4.0 |
| Public-market AI sentiment, −1..+1 | 0.0 | +0.3 | −0.2 | +0.6 | +0.7 | +0.5 |

Rates set the discount on a lab's narrative valuation and the cost of the
infrastructure debt that funds gigawatt datacentres; appetite scales what
a round can raise. Neither is wired yet.

## 4. Politics and mood (endogenous later)

Public mood moves on: capability jumps the public can see (the assistant
gate), incidents (`sim/safety.py` already produces them), job displacement
(thrust C), and each bloc's press. Regulatory stance follows mood with a
lag, plus dated events on the record. Export-control severity is a bloc
relationship, not a constant — the US-China track above is the one that
exists; the sandbox lets it go differently.

## 5. What the world will act on, in order

1. **Compute access**: `supply_share` derived from bloc fab access ×
   packaging share, not set per lab. Export controls become an event on a
   relationship.
2. **Power**: a lab's lease cap, build lead time and price come from its
   bloc's grid, queue and price; AI load as a share of bloc grid is the
   thing that triggers the 2024-25 crunch.
3. **Capital**: rounds and debt priced off rates and appetite.
4. **Demand**: the labour-market model (thrust C) replaces the capability
   spend curve; eras fall out of which loops are on.
5. **Regulation** per bloc replaces the single sector scalar.

## 6. The instrument — dated anchors

Same criteria as `PREMISES.md`: timing, order, magnitude within an OOM,
shape. Before any of §5 goes live, the sim must reproduce these *for the
reasons*.

| Anchor | When | What the sim must show |
|---|---|---|
| US export controls on advanced accelerators to China | Oct 2022, tightened Oct 2023 | China-bloc labs' effective fab access falls to ~0.35 then ~0.15; their fleets flatten; a domestic-chip track appears |
| ChatGPT moment: public mood and venture appetite jump | Dec 2022 – Q1 2023 | mood +0.3 in a quarter; appetite index doubles in a year |
| EU AI Act in force | Aug 2024 | EU regulatory stance ~0.7; agentic products gated harder there |
| CoWoS shortage | 2023 – mid 2024 | accelerator deliveries capped by packaging, not wafers; lead times 9-12 months |
| Power crunch: interconnect queues and gas turbines | 2024-25 | US queue ~48 months; AI load passes 2% of US grid; leased-power price up 30-50% |
| Gulf compute deals | 2024-25 | Gulf access restored to ~0.8; sovereign clusters at 100k+ accelerators |
| Rates peak and ease | 2023 → 2025 | infrastructure debt cheaper; SPV-funded builds accelerate |
