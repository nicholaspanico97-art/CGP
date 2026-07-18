"""CLI for the R-01 backtest harness.

  python run.py backtest    --product BTC-USD --granularity 86400 --days 1460 \
                            --strategy sma_cross --params fast=20,slow=100
  python run.py walkforward --product BTC-USD --granularity 86400 --days 1460 \
                            --strategy sma_cross --train-bars 365 --test-bars 90

Writes a markdown report to ../results/ and prints a summary.
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

# Windows consoles default to cp1252, which chokes on the report's arrows
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from backtest import DEFAULT_FEE_BPS, DEFAULT_SLIPPAGE_BPS, run_backtest
from data import fetch_ohlcv
from strategy import STRATEGIES, BuyAndHold
from walkforward import run_walkforward

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


def _d(ts: int) -> str:
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d")


def _parse_params(s: str | None) -> dict:
    if not s:
        return {}
    out = {}
    for pair in s.split(","):
        k, v = pair.split("=")
        out[k.strip()] = int(v) if v.strip().lstrip("-").isdigit() else float(v)
    return out


def cmd_backtest(args) -> str:
    candles = fetch_ohlcv(args.product, args.granularity, args.days)
    cls = STRATEGIES[args.strategy]
    strat = cls(**_parse_params(args.params))
    r = run_backtest(candles, strat, product=args.product,
                     fee_bps=args.fee_bps, slippage_bps=args.slippage_bps)
    bench = run_backtest(candles, BuyAndHold(), product=args.product,
                         fee_bps=args.fee_bps, slippage_bps=args.slippage_bps)

    lines = [
        f"# Backtest — {r.strategy} on {args.product}",
        "",
        f"*IN-SAMPLE run (debugging only — walk-forward is the score that counts).*",
        "",
        f"- Span: {_d(r.start_ts)} → {_d(r.end_ts)} ({r.bars} bars, granularity {args.granularity}s)",
        f"- Costs: {args.fee_bps:.0f} bps fee + {args.slippage_bps:.0f} bps slippage per side",
        "",
        "| metric | strategy | buy & hold |",
        "|--------|----------|------------|",
    ]
    for (name, val), (_, bval) in zip(r.summary_rows(), bench.summary_rows()):
        lines.append(f"| {name} | {val} | {bval} |")
    return "\n".join(lines)


def cmd_walkforward(args) -> str:
    candles = fetch_ohlcv(args.product, args.granularity, args.days)
    cls = STRATEGIES[args.strategy]
    wf = run_walkforward(candles, cls, product=args.product,
                         train_bars=args.train_bars, test_bars=args.test_bars,
                         fee_bps=args.fee_bps, slippage_bps=args.slippage_bps)

    lines = [
        f"# Walk-forward — {wf.strategy_cls} on {args.product}",
        "",
        f"- Data: {_d(candles[0].ts)} → {_d(candles[-1].ts)} ({len(candles)} bars, granularity {args.granularity}s)",
        f"- Windows: train {args.train_bars} bars → test {args.test_bars} bars, rolled",
        f"- Costs: {args.fee_bps:.0f} bps fee + {args.slippage_bps:.0f} bps slippage per side",
        f"- Folds completed: {len(wf.folds)}",
        "",
        f"## OUT-OF-SAMPLE (the honest number)",
        f"- Strategy stitched OOS return: **{wf.oos_return * 100:+.1f}%**",
        f"- Buy & hold over same span:    **{wf.benchmark_return * 100:+.1f}%**",
        "",
        "| fold test span | chosen params | train sharpe | OOS return | OOS maxDD | OOS trades |",
        "|---|---|---|---|---|---|",
    ]
    for f in wf.folds:
        p = ",".join(f"{k}={v}" for k, v in sorted(f.chosen_params.items()))
        lines.append(
            f"| {_d(f.test_start)} → {_d(f.test_end)} | {p} | {f.train_sharpe:.2f} "
            f"| {f.oos_return * 100:+.1f}% | -{f.oos_maxdd * 100:.1f}% | {f.oos_trades} |"
        )
    lines += [
        "",
        "Param stability check: if chosen params jump around every fold,",
        "the edge is noise, not signal.",
    ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description="R-01 backtest harness")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p):
        p.add_argument("--product", default="BTC-USD")
        p.add_argument("--granularity", type=int, default=86400)
        p.add_argument("--days", type=int, default=1460)
        p.add_argument("--strategy", choices=STRATEGIES, default="sma_cross")
        p.add_argument("--fee-bps", type=float, default=DEFAULT_FEE_BPS)
        p.add_argument("--slippage-bps", type=float, default=DEFAULT_SLIPPAGE_BPS)
        p.add_argument("--no-report", action="store_true",
                       help="print only, don't write results/ file")

    bt = sub.add_parser("backtest")
    common(bt)
    bt.add_argument("--params", help="e.g. fast=20,slow=100")

    wf = sub.add_parser("walkforward")
    common(wf)
    wf.add_argument("--train-bars", type=int, default=365)
    wf.add_argument("--test-bars", type=int, default=90)

    args = ap.parse_args()
    report = cmd_backtest(args) if args.cmd == "backtest" else cmd_walkforward(args)
    print(report)

    if not args.no_report:
        RESULTS_DIR.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        out = RESULTS_DIR / f"{stamp}_{args.cmd}_{args.strategy}_{args.product}.md"
        out.write_text(report + "\n", encoding="utf-8")
        print(f"\n[report written: {out}]")


if __name__ == "__main__":
    main()
