# Simple TP Címkézés (SL nélkül) — Eredmény

Gyorsító: SL = zaj forrás. Az ár oscillál és SL-t talál → contratrend címkézés.
SL nélkül: **eléri-e a TP-t X percen belül?** IGEN/NEM — tiszta bináris.

## Eredmények ($30 TP, 5 perc, 5m EMA20)

| Modell | WR | Info (vs 50% random) |
|---|---|---|
| **Long** | 58.9% | +8.9% |
| **Short** | 59.4% | +9.4% |
| **EMA filtered** | **64.1%** | **+14.1%** |

## Grid Search Top 5

| Config | Long% | Short% | EMA% | Info |
|---|---|---|---|---|
| $20 TP, 30 bar, 5m EMA20 | 76.9% | 77.3% | 80.6% | +30.6% |
| $25 TP, 30 bar, 5m EMA20 | 71.9% | 72.3% | 76.0% | +26.0% |
| $30 TP, 30 bar, 5m EMA20 | 67.2% | 67.6% | 71.6% | +21.6% |
| **$30 TP, 18 bar, 5m EMA20** | **58.9%** | **59.4%** | **64.1%** | **+14.1%** |
| $40 TP, 30 bar, 5m EMA20 | 58.5% | 58.9% | 63.3% | +13.3% |

## Config
```python
SIMPLE_TP_DIST = 30.0    # $ TP distance
SIMPLE_TP_MAX_BARS = 18  # ~5 perc
SIMPLE_TP_EMA_PERIOD = 20
SIMPLE_TP_EMA_RS_SEC = 300  # 5m EMA
```
