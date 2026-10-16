# Session: ensemble_lgbm_et_v1.04_20260924_2330
*Időbélyeg: 2026-09-24T23:36:02.855067*

# nav_3c_v1.04 ENSEMBLE EREDMÉNY (LGBM + ExtraTrees, 2026.09.24. 23:30)

## PLAFON TÖRVE: 52.3% → 54.3% (max profit) vagy 55.1% (max WR)

## Modell: 15 feature, LGBM v1.04 + ExtraTrees (soft voting)
- LGBM: 500 fa, max_depth=4, lr=0.060, noise_weight=0.575
- ET: 500 fa, max_depth=8, max_features='sqrt', same noise_weight

## Eredmények:
### Max Profit (WR>53%):
- Blend 0.7 LGBM / 0.3 ET
- th_l=0.25, th_s=0.50, th_n=0.35
- WR=54.3%, Profit=+1626, 2589 trades (199/day), Opp=0, L:1089 S:1500

### Max WR:
- Blend 0.4 LGBM / 0.6 ET
- th_l=0.28, th_s=0.55, th_n=0.35
- WR=55.1%, Profit=+1454, 2227 trades (171/day), Opp=0

### Önálló modellek:
- LGBM v1.04: 52.3% WR, +2215 profit, 299/day (max profit, max frequency)
- ExtraTrees: 49.0% WR, +2269 profit, 371/day, 148 Opp (gyenge egyedül)

## Kulcs meglátás:
- ET önállóan gyenge (49% WR, 148 Opp)
- DE más döntéshatárt húz (random split point vs LGBM leaf-wise)
- Soft voting: P(P_L) = w1*LGBM_P_L + w2*ET_P_L
- th_noise=0.35 a kulcs (magasabb threshold → kevesebb de pontosabb szignál)
- Trade-off: magasabb WR (54-55%) de kevesebb trade (171-199 vs 299) és alacsonyabb profit

## ET Feature Importance (eltér LGBM-től!):
1. Stoch_D (0.289) — LGBM: 280
2. WPR_14 (0.176) — LGBM: 126
3. Stoch_K (0.163) — LGBM: 134
4. Slope_Close_14 (0.076) — LGBM: 318
5. Micro_RSI_14 (0.072) — LGBM: 305

ET más feature-eket preferál (Stoch_D, WPR_14, Stoch_K) — ezért komplementer!

## Fájlok:
- models/nav_3c_v1.04/model.pkl (LGBM)
- models/nav_3c_v1.04/et_model.pkl (ExtraTrees)
- models/nav_3c_v1.04/ensemble_metrics.json
- src/optuna_v104_gpu.py (400 trial GPU script)