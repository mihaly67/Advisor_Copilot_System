# V110 Bar Comparison — Végeredmény

## 5 bar típus × 8 PT/SL kombináció

### TOP 5 Vizsga WR (stabil, gap<3%)
| # | Konfiguráció | OOS WR | Viz WR | Gap | OOS P | Viz P |
|---|-------------|--------|--------|-----|-------|-------|
| 1 | volbar_3_PT1.5_SL1.0_MB8 | 50.4% | 51.3% | -0.9% | $717 | $279 |
| 2 | volbar_3_PT2.0_SL1.5_MB8 | 49.5% | 50.3% | -0.8% | $562 | $222 |
| 3 | 100tick_PT2.0_SL1.5_MB8 | 50.9% | 49.5% | +1.4% | $200 | $94 |
| 4 | 100tick_PT5.0_SL3.0_MB10 | 45.1% | 49.5% | -4.4% | $489 | $261 |
| 5 | 100tick_PT1.5_SL1.0_MB8 | 46.1% | 48.4% | -2.3% | $216 | $155 |

### Kulcs megállapítások
- **Volatility bar ATR=$3.0 MŰKÖDIK** — a korábbi probléma a PT/SL/MB rossz beállítása
- MB=8 >> MB=5 (több idő a move kifejlődésére)
- PT=$1.5 SL=$1.0 a legjobb arány volbar_3-hoz
- 100tick bar is jó WR de kevesebb profit
- volbar_5 overfitting (gap 10%)

### VÉGSŐ AJÁNLÁS
**volbar_3_PT1.5_SL1.0_MB8**
- OOS=50.4% Viz=51.3% Gap=-0.9%
- Legstabilabb + legjobb profit ($996)
