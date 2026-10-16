# nav_3c_v1.02 — Feature + Hyperparameter Javaslat (2026.09.24.)

## 📊 TRADE FREKVENCIA: ✅ MÁR TELJÜL (208.8/day)
- 478 bars/day, 79s/bar (1.3 min)
- 2719 trades / 13 days = 208.8 trades/day
- Cél 100+/day → bőven felett

## 📊 WR: 50.4% — javítani kell

## 🔬 RAG EREDMÉNYEK:
1. DEMA/TEMA/ZLEMA — zero-lag smoothing (TA-Lib)
2. TRIX — triple-smoothed EMA ROC, "filters out short-period noise"
3. Optuna Bayesian optimization (tensortrade, qlib)
4. LGBM-Stock-Prediction: random search max_depth+num_leaves
5. class_weight / focal_loss for imbalanced (48% Noise)

## OHLC/WICK/SPREAD FEATURE ANALYSIS EREDMÉNYEK:

### TOP 10 Feature |EffSize| alapjan (blokkolás-mentesítő erő):
| Feature | corr_P_L | corr_P_N | EffSize | Típus |
|---|---|---|---|---|
| ATR_Micro | -0.04 | -0.25 | +0.42 | Anti-Noise (volatilitás) |
| Kyle_Vol_Sync | -0.03 | -0.22 | +0.32 | Anti-Noise (ár-impakt) |
| Slope_Close_14 | +0.75 | +0.13 | -0.30 | TREND (király!) |
| Dist_15m | +0.45 | +0.12 | -0.28 | Trend (M15 távolság) |
| Mom10_Direction | +0.67 | +0.12 | -0.27 | Trend (10-bar mom) |
| Trend_EMA_Med_Dist | -0.61 | -0.13 | +0.27 | Trend (EMA távolság) |
| MomScore_14 | +0.65 | +0.11 | -0.26 | Trend (normalizált mom) |
| Trend_EMA_Fast_Dist | -0.47 | -0.11 | +0.22 | Trend (EMA gyors) |
| PastRet_5 | +0.38 | +0.10 | -0.18 | Return (5-bar) |
| Tick_Speed | +0.03 | -0.13 | +0.17 | Anti-Noise (sebesség) |

### Wick/Spread/Spike feature-k (GYENGEK):
- Wick_Upper_ATR: EffSize=+0.09 — gyenge
- Wick_Lower_ATR: EffSize=+0.10 — gyenge
- Wick_Asymmetry: EffSize=-0.02 — használhatatlan
- Avg_Spread: EffSize=-0.04 — gyenge
- Roll_Spread: EffSize=-0.02 — gyenge
- Micro_R_Wick_Rej: EffSize=-0.15 — mérsékelten jó (rejection signal)

## javaslat v1.02

### VEGYÜNK KI (2 feature):
1. RSI_M15 — túl lassú (range 20-81), EffSize=-0.215 (gyenge)
2. Pulse_DF_Curve — EffSize=+0.07 (semmi hatás), skálázási probléma

### TEGYÜNK BE (6 feature):
1. Slope_Close_14 — corr_P_L=0.746 (!!), EffSize=-0.297 (KIRÁLY)
2. Mom10_Direction — corr_P_L=0.672, EffSize=-0.269
3. MomScore_14 — corr_P_L=0.646, EffSize=-0.263
4. Trend_EMA_Medium_Dist — corr_P_L=-0.614, EffSize=+0.268
5. ATR_Micro — corr_P_N=-0.246, EffSize=+0.416 (ANTI-NOISE!)
6. PastRet_5 — corr_P_L=0.380, EffSize=-0.185 (zero lag return)

### Eredmény: 11 - 2 + 6 = 15 feature

### Hyperparameter tuning (Optuna, 100 trials):
- num_leaves: 15-63
- max_depth: 3-8
- learning_rate: 0.01-0.1 (log)
- n_estimators: 200-1000
- min_child_samples: 20-100
- subsample: 0.6-1.0
- colsample_bytree: 0.5-1.0
- reg_alpha: 0-1.0
- reg_lambda: 0-1.0
- class_weight: Noise=0.5 (downweight 48% Noise)

### Threshold:
- th_noise: 0.50 → 0.60 (csak 12% blokkolás)

### Várható eredmény:
- WR: 50.4% → 52-55%
- Trades: 208/day → ~150/day (jobb minőség)
- Phase lag: 7 bar → ~4-5 bar (Slope/PastRet nincs lag)