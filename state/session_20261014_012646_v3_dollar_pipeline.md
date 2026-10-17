# Session: v3_dollar_pipeline
*Időbélyeg: 2026-10-14T01:26:46.739092*

SCALPER V3 DOLLAR BAR PIPELINE — TELJES EREDMÉNYEK

KÉRDÉS: TP=$30, 3 perc horizont, dollar bár címkézés

VIZSGÁLAT: TP/horizont sweep BTCUSD-nál ($86K ár)
- $30/3min → AUC 0.51 = ÉRME ❌ (90% signal rate, triviális)
- $30/30s → AUC 0.66 (49% signal, jobb)
- $50/60s → AUC 0.70 ✅ OPTIMUM (40% signal, 19%L/21%S labels)
- $50/120s → AUC 0.62 (63% signal, túl könnyű)
- $100/180s → AUC 0.67 (32% signal)

MAGYARÁZAT: BTC $86K-nál $30=0.035%. 3 perc alatt BTC tipikusan 0.1-0.3% mozog.
Szinte minden pont eléri +$30 és -$30 is 3 percen belül.
"Melyik jön előbb?" → érme.

PIPELINE V3 HYBRID:
- Címkézés: dollar bár ($10M küszöb) → OHLC gyertyák
- Feature-k: MTF tick (S/R, RSI, micro/sec/ter) a bár időpontjában
- LGBM: is_unbalance=True, Optuna optimalizált (leaves=22, lr=0.01)

VÉGSŐ MODELL (5-fold CV):
- Long AUC=0.6715, Short AUC=0.6461
- Labels: Long 19.4%, Short 21.0%, Neutral 59.6%
- Both<0.05: 0.0% (nincs nullázás!)
- Top features: tv_60, tv_20, atr_pct, micro_sqz, rsi_n

FÁJLOK:
- /data/LGBM_copilot/src/scalper_v3_hybrid.py — hibrid pipeline
- /data/LGBM_copilot/src/scalper_v3_optuna.py — Optuna (best AUC=0.70)
- /data/LGBM_copilot/src/scalper_v3_retrain.py — final retrain
- Model: BTCUSD_v3f_long/short_20261014_012426.txt
- Chart: BTCUSD_scalper_2026-10-05_20261014_012613.html