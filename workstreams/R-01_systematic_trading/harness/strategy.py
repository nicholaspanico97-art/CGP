"""Strategy interface and reference strategies.

Contract: a Strategy sees candles [0..i] (history up to and including
bar i's close) and returns a target position for the NEXT bar as a
fraction of equity: 1.0 = fully long, 0.0 = flat. The engine fills at
bar i+1's open — a strategy can never trade the bar it just observed.

Long/flat only for now (spot venue, no shorting). Fractions in between
are allowed for sizing rules later.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from data import Candle


class Strategy(ABC):
    #: parameter grid used by walk-forward optimization: {param: [values]}
    param_grid: dict[str, list] = {}

    def __init__(self, **params):
        self.params = params

    @abstractmethod
    def target_position(self, candles: list[Candle], i: int) -> float:
        """Target exposure [0..1] to hold during bar i+1."""

    def warmup_bars(self) -> int:
        """Bars of history required before signals are valid."""
        return 0

    def describe(self) -> str:
        p = ",".join(f"{k}={v}" for k, v in sorted(self.params.items()))
        return f"{type(self).__name__}({p})"


class BuyAndHold(Strategy):
    """The benchmark every strategy must beat."""

    def target_position(self, candles: list[Candle], i: int) -> float:
        return 1.0


class SmaCross(Strategy):
    """Long when fast SMA > slow SMA, flat otherwise.

    Deliberately boring: it exists to exercise the harness and to be
    the honesty check — if the harness makes THIS look brilliant,
    something in the harness is lying.
    """

    param_grid = {
        "fast": [10, 20, 30, 50],
        "slow": [60, 100, 150, 200],
    }

    def __init__(self, fast: int = 20, slow: int = 100):
        if fast >= slow:
            raise ValueError("fast period must be < slow period")
        super().__init__(fast=fast, slow=slow)
        self.fast = fast
        self.slow = slow

    def warmup_bars(self) -> int:
        return self.slow

    def target_position(self, candles: list[Candle], i: int) -> float:
        if i + 1 < self.slow:
            return 0.0
        closes = [c.close for c in candles[i + 1 - self.slow : i + 1]]
        sma_slow = sum(closes) / self.slow
        sma_fast = sum(closes[-self.fast:]) / self.fast
        return 1.0 if sma_fast > sma_slow else 0.0


STRATEGIES: dict[str, type[Strategy]] = {
    "buy_hold": BuyAndHold,
    "sma_cross": SmaCross,
}
