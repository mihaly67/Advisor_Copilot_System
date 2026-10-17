# Session: direction_features_integrated
*Időbélyeg: 2026-10-14T23:50:43.937900*

Scalper Copilot v4.0 — DIRECTION + ICT + SESSION + VP feature-k beépítve

ÚJ FEATURE-K (20 → 49 total, régi 35):
DIRECTION (6): df_curve(CUSUM folytonos), flow_delta, pv_corr, mom_persistence, vol_adj_mom, variance_ratio
ICT (5): fvg_signal, fvg_size, ob_signal(folytonos), liq_sweep_net(folytonos)
SESSION (5): kill_zone_london, kill_zone_ny, kill_zone_overlap, hour_sin, htf_trend
VP (2): poc_dist(folytonos)

AUC ÖSSZEHASONLITAS:
               Régi(35)  Új(49)   Delta
1min Long      0.594     0.698   +0.104 🟢
1min Short     0.602     0.608   +0.006
2min Long      0.653     0.649   -0.004
2min Short     0.629     0.610   -0.019 🔴
3min Long      0.602     0.591   -0.011
3min Short     0.604     0.570   -0.034 🔴

KULCS FELISMERES:
- 1min Long óriási javulás (+0.104!) — direction feature-k hatása
- 2min/3min Short romlott — valószínűleg overfitting vagy zaj feature-k
- A top új feature-k: hour_sin(#4), poc_dist(#5), htf_trend(#7), pv_corr(#8), variance_ratio(#15)
- df_curve folytonos formában aktív (imp=204), de gyenge
- ob_signal és liq_sweep_net is aktív (imp=41/40), de nagyon gyenge

TOVÁBBI LÉPÉSEK:
1. Feature selection — csak >0.5% importance feature-ket tartani
2. Regularizáció növelése (reg_alpha=0.1, reg_lambda=0.5)
3. Walk-forward validáció
4. Meta-labeling a szignál szűréshez