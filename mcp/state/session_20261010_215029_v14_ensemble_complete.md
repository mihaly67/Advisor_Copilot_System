# Session: v14_ensemble_complete
*Időbélyeg: 2026-10-10T21:50:29.755161*

V14 ENSEMBLE PIPELINE KÉSZ (áramszünet recovery)

EREDMÉNYEK:
- MLP:  valAUC=0.821  params=14,849  d/p=16.9  perm_z=44.5
- LGBM: valAUC=0.833  best_iter=500  (27 feature, azonos MLP-vel!)
- ENS:  valAUC=0.839  w_mlp=0.65  w_lgbm=0.35
- OOS:  valAUC=0.810 ± 0.009 (purged CV)

ENSEMBLE JAVULÁS:
- MLP alone: 0.821 → Ensemble: 0.839 (+0.018, +2.2%)
- LGBM alone: 0.833 → Ensemble: 0.839 (+0.006)
- w_mlp=0.65 optimal (MLP dominál, de LGBM segít)

TOP FEATURE IMPORTANCE (MLP permutation):
1. consecutive_f +0.225 — egymás utáni irányú barok
2. trend_micro +0.172 — 3-bar irány
3. PastRet_2_f +0.125 — 2-bar return
4. body_sign_f +0.103 — bar irány
5. delta_pivot_dist +0.063 — PIVOT FEATURE!

TOP LGBM FEATURE IMPORTANCE:
1. delta_pivot_dist 2068 — PIVOT DOMINÁL!
2. delta_sr_zone_micro 1536
3. PastRet_2_f 1134
4. consecutive_f 1098
5. body_atr_f 990

KIMENTVE:
- models/v14/mlp_meta_v12.pt (MLP modell)
- models/v14/lgbm_v14.pkl (LGBM modell)
- models/v14/features.txt (27 feature név)
- models/v14/ensemble_config.json (ensemble config)

KÖVETKEZŐ LÉPÉS: MLP signal → ZMQ → EA integráció