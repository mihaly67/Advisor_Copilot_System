# Optuna TB Címkézés Optimalizálás — Eredmény

## Probléma
- Régi: side = bar direction (17s) → 51% irányváltás → contratrend címkézés → WR=40% (random)
- A 17s dollár bar ATR=$22 → TP=$33 → 0.03% mozgás → azonnal teljesül vagy nem = zaj

## Megoldás: Multi-TF ATR + EMA Trend Filter
1. **5 perces ATR** (nem 17s dollár bar ATR) → ATR=$96 → TP=$115, SL=$144 → 0.1% mozgás
2. **5 perces EMA20 slope → side** (trend-követő, NEM contrarian) → EMA up = Long, EMA down = Short
3. **Timeout = -1** (nem SL=0!) — kritikus bug fix

## Optuna Eredmény (80 trial, 39.6s)
- **Legjobb konfig**: PT=1.2 SL=1.5 mb=50 EMA=20, ATR=5m, EMA_RS=5m
- **WR Long**: 60.9%
- **WR Short**: 58.8%  
- **WR EMA filtered**: 68.3%
- **Random WR**: 55.6% (= SL/(TP+SL) = 1.5/2.7)
- **Info (WR-RW)**: +12.7%
- **Expectancy**: +$33/bar

## Top 5 Reális Konfig (Expectancy alapján)
| # | Konfig | WR | RW | Info | TP$ | SL$ | E[$] |
|---|---|---|---|---|---|---|---|
| 1 | 5m PT=1.2 SL=1.5 mb=50 EMA=20 | 68.3% | 55.6% | +12.7% | $115 | $144 | +$33 |
| 2 | 5m PT=1.0 SL=1.5 mb=50 EMA=20 | 73.7% | 60.0% | +13.7% | $96 | $144 | +$33 |
| 3 | 5m PT=1.5 SL=1.5 mb=50 EMA=20 | 59.6% | 50.0% | +9.6% | $144 | $144 | +$28 |
| 4 | 5m PT=1.0 SL=1.5 mb=50 EMA=50 | 71.1% | 60.0% | +11.1% | $96 | $144 | +$27 |
| 5 | 5m PT=1.2 SL=1.5 mb=50 EMA=50 | 65.4% | 55.6% | +9.9% | $115 | $144 | +$26 |

## Fájlok
- `src/optuna_tb_tuner.py` — Optuna kereső
- `src/02_label_triple_barrier.py` — Címkéző (multi-TF ATR + EMA)
- `src/config.py` — Optuna optimalizált paraméterek
- `output/optuna_tb_best.json` — Legjobb paraméterek
- `output/optuna_tb_trials_top10.csv` — Top 10 trial
