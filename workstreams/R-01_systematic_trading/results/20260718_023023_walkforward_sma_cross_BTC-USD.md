# Walk-forward — SmaCross on BTC-USD

- Data: 2022-07-20 → 2026-07-18 (1460 bars, granularity 86400s)
- Windows: train 365 bars → test 90 bars, rolled
- Costs: 25 bps fee + 10 bps slippage per side
- Folds completed: 12

## OUT-OF-SAMPLE (the honest number)
- Strategy stitched OOS return: **+18.4%**
- Buy & hold over same span:    **+114.2%**

| fold test span | chosen params | train sharpe | OOS return | OOS maxDD | OOS trades |
|---|---|---|---|---|---|
| 2023-07-20 → 2023-10-17 | fast=50,slow=60 | 1.50 | -6.2% | -11.8% | 2 |
| 2023-10-18 → 2024-01-15 | fast=30,slow=60 | 1.57 | +50.2% | -11.3% | 0 |
| 2024-01-16 → 2024-04-14 | fast=30,slow=60 | 1.58 | +25.9% | -15.4% | 2 |
| 2024-04-15 → 2024-07-13 | fast=10,slow=60 | 2.05 | -7.3% | -10.0% | 3 |
| 2024-07-14 → 2024-10-11 | fast=10,slow=60 | 1.89 | -22.7% | -26.0% | 5 |
| 2024-10-12 → 2025-01-09 | fast=30,slow=100 | 1.26 | +46.6% | -12.8% | 0 |
| 2025-01-10 → 2025-04-09 | fast=30,slow=100 | 1.27 | -6.8% | -16.9% | 1 |
| 2025-04-10 → 2025-07-08 | fast=10,slow=100 | 0.76 | +15.8% | -9.6% | 1 |
| 2025-07-09 → 2025-10-06 | fast=10,slow=100 | 1.78 | -6.8% | -17.5% | 4 |
| 2025-10-07 → 2026-01-04 | fast=20,slow=100 | 0.96 | -11.7% | -13.7% | 1 |
| 2026-01-05 → 2026-04-04 | fast=20,slow=60 | 0.56 | -18.7% | -21.0% | 3 |
| 2026-04-05 → 2026-07-03 | fast=50,slow=60 | -0.65 | -12.1% | -26.1% | 4 |

Param stability check: if chosen params jump around every fold,
the edge is noise, not signal.
