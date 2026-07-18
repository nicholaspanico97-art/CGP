# R-05 — Supercoiled Polymer (TCP/SCP) Actuators

**Status:** candidate — Nick's stated white whale (Jul 18, 2026).
Long-horizon R&D + product track.
**Fit:** the one robotics niche that is squarely chemical-engineering
turf — the hard problems are polymer processing (draw-induced chain
alignment, twist insertion, annealing schedules, creep/fatigue),
not mechanism design. Nick attacks from the correct side.

## What it is
Twisted-and-coiled polymer muscles (Haines et al., Science 2014
lineage): nylon monofilament twisted to coiling, annealed, thermally
actuated. ~10–20% contraction, extraordinary specific work density.
A decade later there is still no commercial off-the-shelf supplier for
hobbyists/researchers at small scale — genuine white space.

## Why the white space exists (the honest part)
1. **Cooling is the bottleneck.** Heating is fast; cooling sets cycle
   rate. Ambient TCP is sub-0.1 Hz; forced air/water buys speed at the
   cost of plumbing.
2. **Efficiency ~1–2%.** Thermal actuation rejects nearly everything
   as heat. Fine for a slow gripper; brutal for battery budgets.
3. **Repeatability/creep.** Making muscle N+1 behave like muscle N is
   an annealing-consistency problem — precisely a ChemE problem.

Consequence: TCP muscles do NOT replace servos, and are NOT a CEV v0.x
actuator (CEV stays on gearboxes). This is a parallel research program.

## Product thesis
Sell the *enablement*, not the dream: a printable twist-insertion rig
(controlled tension + turn counting), annealing fixture, force/stroke/
cycle-life test stand, characterized starter materials, and
documentation good enough that a buyer gets a working muscle on
attempt one. Nobody sells this. Buyers: hobbyists, uni labs, FIRST-tier
teams. Synergy with [R-04](R-04_content_channel.md): the whale hunt is
the content; a test stand lifting weights with coiled fishing line is
excellent camera material; the audience is the demand check.

## Effort / capital / risk
- **Effort:** long-horizon; competes with CEV hours. Natural sequencing:
  after CEV v0.5 ships (gearbox program winds down to production).
- **Capital:** cheap — nylon line, nichrome/silver-coated thread,
  printed rigs; well under $100 to first characterized muscle.
- **Risk:** demand may be tiny (labs make their own); mitigated by
  R-04 running first. Physics risk is low — the actuators demonstrably
  work; the question is repeatability and whether tooling is sellable.

## First build if selected
Twist rig v0 + one characterized muscle: force, stroke, cycle count to
failure, all logged. That single data sheet is simultaneously episode
material (R-04), the product's proof, and the start of the repeatability
study.
