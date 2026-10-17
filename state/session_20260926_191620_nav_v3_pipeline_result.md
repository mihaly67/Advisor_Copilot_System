# Session: nav_v3_pipeline_result
*Időbélyeg: 2026-09-26T19:16:20.871966*

NAVSISTEM V3 PIPELINE KÉSZ:
1. navsystem_indicators_v3.py — 3 MQ5 indikátor Python fordítás + LGBM értelmező réteg (38 feature)
2. build_nav_v3_features.py — feature generálás CSV-re (train+oos)
3. train_nav_v3.py — LGBM tanítás 54 feature-rel (36 Nav + 18 pivot)

EREDMÉNY:
- 54 feature, 3-class LGBM
- IS Best: th_L=0.40, th_S=0.35, th_N=0.60, P=+1476
- OOS: 8313 trade, WR=46.8%, P=+3369 (Long:3948, Short:4365)
- Feature importance: Intensity+Accel dominálnak, Direction alacsony

KULCS FELISMERÉS:
- Az indikátor INTENZITÁS (messze a választótól) a legfontosabb — nem az irány
- MACD_Accel = 2532 (momentum gyorsulás!)
- DF_Intensity + DF_Accel = 3357 (DeltaForce erő + gyorsulás)
- Pivot távolságok (Dist_*) = 11730 (összesen!) — a geometria dominál
- Nav_Consensus = 244, OS_Long/Short = 100/125 — a konszenzus segít de nem dominál

TOVÁBBI LÉPÉS:
- SHAP analízis → mely feature-ök OK, melyek noise
- Optuna 4D threshold kalibráció (th_L, th_S, th_N, noise_weight)
- Copilot feature lista frissítés (10 → 54 feature)