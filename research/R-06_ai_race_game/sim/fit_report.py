"""Calibration report: model prediction vs. every historical anchor."""
import math
from . import anchors as A
from .capability import BenchmarkModel, FrontierHistory, algo_efficiency


def report():
    bm = BenchmarkModel().fit()
    fh = FrontierHistory()
    print("CAPABILITY CURVE FIT  (fitted parameters)")
    for s, (c50, w) in bm.params.items():
        print(f"   {s:5s}  midpoint at C={c50:6.3f}"
              f"  ({10**c50:.1e} effective FLOP)   width={w:5.3f} OOM")

    print("\nBENCHMARK ANCHORS  vs  MODEL")
    print(f"   {'date':9s} {'suite':6s} {'model':>7s} {'actual':>7s} {'err':>7s}"
          f"  {'C':>6s}  source")
    errs = []
    for date, suite, actual, model_name, conf in A.BENCHMARKS:
        m = A.month_index(date)
        from .capability import DOMAIN_OF_SUITE
        c = fh.domain_capability_at(m, DOMAIN_OF_SUITE[suite])
        pred = bm.score(suite, c)
        errs.append(abs(pred - actual))
        print(f"   {date[0]}-{date[1]:02d}   {suite:6s} {pred:7.1f} {actual:7.1f} "
              f"{pred-actual:+7.1f}  {c:6.2f}  {model_name} [{conf}]")
    print(f"   mean absolute error: {sum(errs)/len(errs):.2f} benchmark points")

    print("\nFRONTIER TRAINING RUN  vs  MODEL TRACK")
    print(f"   {'date':9s} {'actual FLOP':>12s} {'model FLOP':>12s} {'err':>8s}  label")
    for date, label, flop, *_rest in A.TRAINING_RUNS:
        m = A.month_index(date)
        mod = fh.flop_at(m)
        ratio = mod / flop
        print(f"   {date[0]}-{date[1]:02d}   {flop:12.2e} {mod:12.2e} "
              f"{ratio:7.2f}x  {label}")

    print("\nEFFECTIVE-COMPUTE DECOMPOSITION (frontier)")
    print(f"   {'date':9s} {'pretrain':>10s} {'algo x':>9s} {'reason x':>9s}"
          f" {'effective':>11s} {'C':>6s}")
    from .capability import reasoning_multiplier
    for y in range(2020, 2031):
        m = A.month_index((y, 6))
        if m < 0:
            continue
        tt = 0.0
        m_rl = A.month_index((2024, 9))
        if m > m_rl:
            tt = min(2.5, (m - m_rl) / 12.0)
        r = reasoning_multiplier(m, 1.0, tt)
        a = algo_efficiency(m)
        f = fh.flop_at(m)
        print(f"   {y}-06   {f:10.1e} {a:9.0f} {r:9.0f} {f*a*r:11.1e}"
              f" {math.log10(f*a*r):6.2f}")
    return bm, fh


if __name__ == "__main__":
    report()
