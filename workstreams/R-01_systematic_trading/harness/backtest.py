"""Backtest engine: next-bar fills, per-side fees and slippage, metrics.

Execution model
---------------
At bar i's close the strategy emits a target exposure for bar i+1.
The engine rebalances at bar i+1's OPEN, paying (fee + slippage) bps on
the notional traded. Equity is marked at each bar's close. This is the
most pessimistic simple model that stays honest for daily/hourly bars.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from data import Candle
from strategy import Strategy

# Per-side costs in basis points. Coinbase small-account taker ballpark.
DEFAULT_FEE_BPS = 25.0
DEFAULT_SLIPPAGE_BPS = 10.0


@dataclass
class BacktestResult:
    strategy: str
    product: str
    start_ts: int
    end_ts: int
    bars: int
    initial_equity: float
    final_equity: float
    total_return: float          # fraction, e.g. 0.42
    cagr: float                  # annualized, fraction
    max_drawdown: float          # fraction, positive number
    sharpe: float                # annualized, from per-bar returns
    n_trades: int                # position changes (each side counted once)
    total_costs: float           # dollars paid in fees+slippage
    exposure: float              # fraction of bars with position > 0
    equity_curve: list[tuple[int, float]] = field(repr=False, default_factory=list)
    trade_times: list[int] = field(repr=False, default_factory=list)

    def summary_rows(self) -> list[tuple[str, str]]:
        return [
            ("total return", f"{self.total_return * 100:+.1f}%"),
            ("CAGR", f"{self.cagr * 100:+.1f}%"),
            ("max drawdown", f"-{self.max_drawdown * 100:.1f}%"),
            ("sharpe (ann.)", f"{self.sharpe:.2f}"),
            ("trades", str(self.n_trades)),
            ("costs paid", f"${self.total_costs:,.2f}"),
            ("time in market", f"{self.exposure * 100:.0f}%"),
        ]


def run_backtest(candles: list[Candle], strategy: Strategy, *,
                 product: str = "?",
                 initial_equity: float = 1_000.0,
                 fee_bps: float = DEFAULT_FEE_BPS,
                 slippage_bps: float = DEFAULT_SLIPPAGE_BPS) -> BacktestResult:
    if len(candles) < max(strategy.warmup_bars() + 2, 3):
        raise ValueError("not enough candles for this strategy's warmup")

    cost_rate = (fee_bps + slippage_bps) / 10_000.0

    cash = initial_equity
    units = 0.0          # units of the asset held
    n_trades = 0
    trade_times: list[int] = []
    total_costs = 0.0
    bars_in_market = 0
    equity_curve: list[tuple[int, float]] = []
    per_bar_returns: list[float] = []
    prev_equity = initial_equity

    for i in range(len(candles) - 1):
        target = strategy.target_position(candles, i)
        target = min(max(target, 0.0), 1.0)

        nxt = candles[i + 1]
        # Rebalance at next bar's open.
        equity_at_open = cash + units * nxt.open
        target_units = target * equity_at_open / nxt.open
        delta_units = target_units - units
        # 0.5% rebalance band: ignore dust-sized adjustments (e.g. the tiny
        # sell-back that fee drag would otherwise force every few bars)
        if abs(delta_units) * nxt.open > equity_at_open * 5e-3:
            notional = abs(delta_units) * nxt.open
            cost = notional * cost_rate
            cash -= delta_units * nxt.open + cost
            units = target_units
            total_costs += cost
            n_trades += 1
            trade_times.append(nxt.ts)

        equity = cash + units * nxt.close
        if units > 0:
            bars_in_market += 1
        equity_curve.append((nxt.ts, equity))
        per_bar_returns.append(equity / prev_equity - 1.0)
        prev_equity = equity

    final_equity = prev_equity
    total_return = final_equity / initial_equity - 1.0

    seconds = candles[-1].ts - candles[0].ts
    years = max(seconds / (365.25 * 86400), 1e-9)
    cagr = (final_equity / initial_equity) ** (1 / years) - 1.0 if final_equity > 0 else -1.0

    peak, max_dd = -math.inf, 0.0
    for _, eq in equity_curve:
        peak = max(peak, eq)
        max_dd = max(max_dd, 1.0 - eq / peak)

    bars_per_year = len(per_bar_returns) / years
    mean_r = sum(per_bar_returns) / len(per_bar_returns)
    var = sum((r - mean_r) ** 2 for r in per_bar_returns) / max(len(per_bar_returns) - 1, 1)
    std = math.sqrt(var)
    sharpe = (mean_r / std) * math.sqrt(bars_per_year) if std > 0 else 0.0

    return BacktestResult(
        strategy=strategy.describe(),
        product=product,
        start_ts=candles[0].ts,
        end_ts=candles[-1].ts,
        bars=len(candles),
        initial_equity=initial_equity,
        final_equity=final_equity,
        total_return=total_return,
        cagr=cagr,
        max_drawdown=max_dd,
        sharpe=sharpe,
        n_trades=n_trades,
        total_costs=total_costs,
        exposure=bars_in_market / max(len(candles) - 1, 1),
        equity_curve=equity_curve,
        trade_times=trade_times,
    )
