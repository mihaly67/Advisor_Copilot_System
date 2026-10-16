# Jules CFD v4 — Prado-helyes Pipeline Eredmények

## v4 Pipeline Architektúra

```
Tick CSV → Dollar bars → CUSUM filter → features at events → Triple Barrier → LightGBM
                           ↓
                     Bar_Direction (body%)
                     + NavSystem direction
                     + S/R + momentum + regime
```

## Eredmények (nav_v31 adat, CUSUM 1.5x vol)

| Metrika | OOS | VIZSGA |
|---------|-----|--------|
| WR | 47.8% | **48.8%** |
| Profit | $60 | **$190** |
| Trades | 312 | 867 |
| Long WR | 39.2% | 40.7% |
| Short WR | 53.5% | **55.0%** |
| Gap | -1.0% | **STABIL** |

## Feature Importance (v4)

1. Regime_ADX 11.82%
2. Pulse_DF_Curve 10.04%
3. Trend_EMA_Medium_Dist 9.38%
4. Micro_RSI_14 9.08%
5. Dist_Ter_S 8.95%
6. Price_Velocity 8.82%
7. Dist_Micro_R 8.41%
8. **Bar_Direction 8.31%** ← V4 ÚJ! (v3-ban 0%)
9. Trend_EMA_Fast_Dist 7.88%
10. Dist_Micro_S 7.17%

## v3 vs v4 összehasonlítás

| Metrika | v3 | v4 | Változás |
|---------|----|----|----------|
| VIZSGA WR | 50.4% | 48.8% | -1.6% |
| Short WR VIZSGA | ~47% | **55.0%** | **+8%** |
| Diagnózis | Overfit? | **STABIL** | ✅ |
| Bar_Direction imp. | 0% | **8.31%** | +8.31% |
| Long WR | ~45% | 40.7% | -4.3% |

## Kulcs javulások
1. **Short WR 55%** — végre jobb mint random! (v3: ~47%)
2. **STABIL** — nincs overfit (gap -1.0%)
3. **Bar_Direction 8.31% importance** — a buying/selling pressure végre számít!

## Hátramaradt problémák
1. **Long WR 40.7%** — még mindig rosszabb mint random
2. **Túl kevés train sample** — nav_v31 csak 24K bar → 5,235 CUSUM event
3. **Nincs meta-labeling** — Bar_Sign/CUSUM direction csak feature, nem primary model

## Következő lépések
1. **Full pipeline a 4.15M tick adatból** → több CUSUM event → jobb generalizáció
2. **Meta-labeling**: Primary=Bar_Sign direction, Secondary=ML decides size
3. **M1 window features** — momentum/velocity M1 OHLC-ről (nem dollar bar OHLC-ről)
4. **CUSUM direction as side prediction** → meta-labeler only decides bet size
