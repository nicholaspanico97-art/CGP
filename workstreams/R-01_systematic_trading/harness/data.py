"""OHLCV data fetcher — Coinbase Exchange public API, with local CSV cache.

Public endpoint, no API key, US-accessible:
  GET https://api.exchange.coinbase.com/products/{product}/candles
      ?granularity={sec}&start={iso}&end={iso}
Returns at most 300 candles per request, newest first, as
[epoch, low, high, open, close, volume]. We paginate backwards and
normalize to chronological Candle rows.
"""

from __future__ import annotations

import csv
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

import requests

API_BASE = "https://api.exchange.coinbase.com"
MAX_CANDLES_PER_REQ = 300
VALID_GRANULARITIES = {60, 300, 900, 3600, 21600, 86400}

CACHE_DIR = Path(__file__).resolve().parent.parent / "data_cache"


@dataclass(frozen=True)
class Candle:
    ts: int  # epoch seconds, bar open time
    open: float
    high: float
    low: float
    close: float
    volume: float


def _cache_path(product: str, granularity: int) -> Path:
    return CACHE_DIR / f"{product}_{granularity}.csv"


def _read_cache(path: Path) -> list[Candle]:
    if not path.exists():
        return []
    with path.open(newline="") as f:
        return [
            Candle(int(r["ts"]), float(r["open"]), float(r["high"]),
                   float(r["low"]), float(r["close"]), float(r["volume"]))
            for r in csv.DictReader(f)
        ]


def _write_cache(path: Path, candles: list[Candle]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ts", "open", "high", "low", "close", "volume"])
        for c in candles:
            w.writerow([c.ts, c.open, c.high, c.low, c.close, c.volume])


def _fetch_window(product: str, granularity: int,
                  start: datetime, end: datetime) -> list[Candle]:
    resp = requests.get(
        f"{API_BASE}/products/{product}/candles",
        params={
            "granularity": granularity,
            "start": start.isoformat(),
            "end": end.isoformat(),
        },
        timeout=30,
    )
    resp.raise_for_status()
    rows = resp.json()
    return [Candle(int(r[0]), float(r[3]), float(r[2]),
                   float(r[1]), float(r[4]), float(r[5])) for r in rows]


def fetch_ohlcv(product: str, granularity: int, days: int,
                refresh: bool = True) -> list[Candle]:
    """Return chronological candles covering the last `days` days.

    Cached rows are reused; only missing history / new bars are fetched.
    """
    if granularity not in VALID_GRANULARITIES:
        raise ValueError(f"granularity must be one of {sorted(VALID_GRANULARITIES)}")

    path = _cache_path(product, granularity)
    by_ts = {c.ts: c for c in _read_cache(path)}

    now = datetime.now(timezone.utc)
    target_start = now - timedelta(days=days)

    if refresh or not by_ts:
        # Walk backwards from now until we cover target_start or run out of history.
        cursor_end = now
        step = timedelta(seconds=granularity * MAX_CANDLES_PER_REQ)
        while cursor_end > target_start:
            cursor_start = max(cursor_end - step, target_start)
            # Skip windows fully covered by cache (except the newest window,
            # which may have grown since last fetch).
            covered = all(
                int(t) in by_ts
                for t in range(int(cursor_start.timestamp()) // granularity * granularity,
                               int(cursor_end.timestamp()), granularity)
            )
            if not covered or cursor_end == now:
                batch = _fetch_window(product, granularity, cursor_start, cursor_end)
                if not batch and cursor_end != now:
                    break  # ran out of history
                for c in batch:
                    by_ts[c.ts] = c
                time.sleep(0.15)  # stay well under public rate limits
            cursor_end = cursor_start

    candles = sorted(by_ts.values(), key=lambda c: c.ts)
    _write_cache(path, candles)

    start_ts = int(target_start.timestamp())
    return [c for c in candles if c.ts >= start_ts]
