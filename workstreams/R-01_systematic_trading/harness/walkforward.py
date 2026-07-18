"""Walk-forward validation — the anti-overfitting discipline.

Split history into rolling (train, test) windows. On each train window,
pick the best parameter set from the strategy's param_grid (by Sharpe,
with a minimum-trades sanity floor). Run ONLY that parameter set on the
following unseen test window. Stitch the test-window results together:
that stitched, out-of-sample record is the strategy's honest score.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

from backtest import run_backtest
from data import Candle
from strategy import Strategy

MIN_TRAIN_TRADES = 3  # a "best" param set that barely trades is noise


@dataclass
class WalkForwardFold:
    train_start: int
    test_start: int
    test_end: int
    chosen_params: dict
    train_sharpe: float
    # metrics over the true out-of-sample span only (warmup bars excluded)
    oos_return: float
    oos_maxdd: float
    oos_trades: int


@dataclass
class WalkForwardResult:
    strategy_cls: str
    product: str
    train_bars: int
    test_bars: int
    folds: list[WalkForwardFold] = field(default_factory=list)
    # stitched out-of-sample equity, normalized to 1.0 at the start
    oos_equity: list[tuple[int, float]] = field(default_factory=list)
    oos_return: float = 0.0
    benchmark_return: float = 0.0  # buy & hold over the same stitched span


def _param_sets(cls: type[Strategy]) -> list[dict]:
    if not cls.param_grid:
        return [{}]
    keys = sorted(cls.param_grid)
    sets = []
    for combo in itertools.product(*(cls.param_grid[k] for k in keys)):
        params = dict(zip(keys, combo))
        try:
            cls(**params)  # let the strategy reject invalid combos
        except ValueError:
            continue
        sets.append(params)
    return sets


def run_walkforward(candles: list[Candle], strategy_cls: type[Strategy], *,
                    product: str,
                    train_bars: int, test_bars: int,
                    fee_bps: float, slippage_bps: float) -> WalkForwardResult:
    result = WalkForwardResult(
        strategy_cls=strategy_cls.__name__, product=product,
        train_bars=train_bars, test_bars=test_bars,
    )
    param_sets = _param_sets(strategy_cls)
    max_warmup = max(strategy_cls(**p).warmup_bars() for p in param_sets)

    equity = 1.0
    fold_start = 0
    while fold_start + train_bars + test_bars <= len(candles):
        train = candles[fold_start : fold_start + train_bars]
        # Test window gets warmup bars of history prepended so signals are
        # valid from its first bar, but scoring starts at the window proper.
        test_hist_start = max(fold_start + train_bars - max_warmup, 0)
        test = candles[test_hist_start : fold_start + train_bars + test_bars]

        best_params, best_sharpe = None, float("-inf")
        for params in param_sets:
            try:
                r = run_backtest(train, strategy_cls(**params), product=product,
                                 fee_bps=fee_bps, slippage_bps=slippage_bps)
            except ValueError:
                continue
            if r.n_trades >= MIN_TRAIN_TRADES and r.sharpe > best_sharpe:
                best_params, best_sharpe = params, r.sharpe
        if best_params is None:
            # nothing tradable found in-sample; sit out this fold flat
            fold_start += test_bars
            continue

        test_r = run_backtest(test, strategy_cls(**best_params), product=product,
                              fee_bps=fee_bps, slippage_bps=slippage_bps)
        # Score only the true out-of-sample span (after the prepended warmup).
        oos_start_ts = candles[fold_start + train_bars].ts
        oos_curve = [(ts, eq) for ts, eq in test_r.equity_curve
                     if ts >= oos_start_ts]
        fold_return = fold_maxdd = 0.0
        if oos_curve:
            base = oos_curve[0][1]
            # chain onto the stitched curve; entry point re-based each fold
            start_equity = equity
            peak = base
            for ts, eq in oos_curve:
                result.oos_equity.append((ts, start_equity * eq / base))
                peak = max(peak, eq)
                fold_maxdd = max(fold_maxdd, 1.0 - eq / peak)
            equity = result.oos_equity[-1][1]
            fold_return = oos_curve[-1][1] / base - 1.0

        result.folds.append(WalkForwardFold(
            train_start=train[0].ts,
            test_start=oos_start_ts,
            test_end=test[-1].ts,
            chosen_params=best_params,
            train_sharpe=best_sharpe,
            oos_return=fold_return,
            oos_maxdd=fold_maxdd,
            oos_trades=sum(1 for t in test_r.trade_times if t >= oos_start_ts),
        ))
        fold_start += test_bars

    result.oos_return = equity - 1.0

    if result.folds:
        span_start_ts = result.folds[0].test_start
        span = [c for c in candles if c.ts >= span_start_ts]
        if len(span) >= 3:
            from strategy import BuyAndHold
            bench = run_backtest(span, BuyAndHold(), product=product,
                                 fee_bps=fee_bps, slippage_bps=slippage_bps)
            result.benchmark_return = bench.total_return
    return result
