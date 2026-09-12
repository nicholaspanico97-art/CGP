# Proposal — make benchmarks mean something

**Status:** proposal, not built. Filed Sep 12 2026 in answer to two of
Nick's points: *"we should try to find a way to make benchmarks mean
something — capabilities might not have to 1:1 match benchmarks"* and
*"I'm not sure if effective FLOPs is the best way to measure."*

## The problem, stated exactly

Today: `score = sigmoid((C − c50) / w)` where `C = log10(effective FLOP)`.

Benchmarks are a deterministic, monotone function of one number. That means
**they carry no information the capability number doesn't already carry.**
They are a readout, not a measurement. Three consequences:

1. A lab cannot be good at a benchmark and mediocre at the underlying
   skill, or the reverse — which is most of what makes real benchmarks
   interesting and contested.
2. Every suite saturates on the same schedule, so late-game benchmarks all
   sit pinned at their ceiling and stop distinguishing anyone.
3. There is no way to *chase* a benchmark, which is a real and consequential
   strategy that real labs are accused of constantly.

And on effective FLOP: it is a fine aggregator of *inputs*. It is a poor
*measure of ability*, because it says nothing about what the model can
actually do — it is an accounting of what was spent, converted to a score by
a fitted curve.

## The proposal: capability as a difficulty frontier

Replace "capability is a number that maps to a score" with **"capability is
how hard a task the model can do, and a benchmark is a sample of tasks."**

```
For each domain, a lab's model has a difficulty frontier F (in OOM of
effective compute, so it stays commensurable with the rest of the model).

A task of difficulty d is solved with probability
    p(d) = sigmoid((F − d) / softness)

A benchmark is a DISTRIBUTION over task difficulty, plus a softness.
Its score is the expected fraction solved:
    score(suite) = mean over its task difficulties of p(d)
```

That single change buys the following, all of it for free:

- **Benchmarks saturate on their own schedule**, because each one's task
  distribution runs out at a different point. No hand-set ceilings.
- **New suites are just harder distributions.** Retiring MMLU for GPQA for
  something harder is a data change, not a code change.
- **Two labs with the same frontier can score differently** on the same
  suite if their `softness` differs — which is what elicitation and
  scaffolding quality actually are.
- **Benchmark-chasing becomes expressible.** Training on eval-like tasks
  narrows the gap between measured score and true frontier *for that suite
  only*: the score rises, the frontier does not. It wins market share now
  (the market prices the published number) and loses the RSI race later
  (the loop keys off the true frontier). That is a real strategic fork the
  current model cannot represent.
- **Contamination has a natural form**: shifting a suite's effective
  difficulty distribution down for one lab, with a chance of being caught.

## What stays

Effective compute stays as the *input* aggregator — it is how a lab buys a
higher difficulty frontier, and it is the thing the physical half of the
model produces. What changes is that it stops being the answer and becomes
the input to the answer.

## What it costs

- Re-fitting the anchored suites (MMLU, GPQA, SWE) as difficulty
  distributions rather than sigmoids. The existing 15 anchors are enough to
  fit a mean and spread per suite, but not much more.
- The five unanchored domains get less speculative, not more: a difficulty
  distribution is a more honest thing to guess at than a fitted curve with
  no data behind it.
- Perhaps a calibration regression while it settles. Worth it.

## Recommended order

1. Difficulty-frontier capability and benchmark-as-distribution, fitted to
   the existing anchors.
2. Per-lab elicitation quality (`softness`), so scaffolding matters.
3. Benchmark-chasing as an explicit spend, with contamination risk.
4. Suite retirement and replacement on a difficulty ladder.

Item 3 is the one that turns benchmarks from a readout into a decision.
