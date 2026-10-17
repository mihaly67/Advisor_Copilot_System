# Session: simple_tp_lgbm_v1
*Időbélyeg: 2026-10-12T18:04:58.746432*

SIMPLE TP LGBM TRÉNING KÉSZ (SL NÉLKÜL!)

Script: /data/dev/LGB_copilot_system/src/04_train_simple_tp.py
Modellek: /data/dev/LGB_copilot_system/models/

Pipeline: 36 feature + Simple TP labels → 3 LightGBM bináris modell
Split: 70/15/15 (idősor), Purged 5-Fold CV (embargo=5)

EREDMÉNYEK (test set):
┌────────┬──────────┬──────────┬──────────┬──────────────────────┐
│ Modell │ AUC      │ WR@0.5   │ Brier    │ Legjobb threshold    │
├────────┼──────────┼──────────┼──────────┼──────────────────────┤
│ LONG   │ 0.5994   │ 62.3%    │ 0.2299   │ 78.6% @ 0.7 (n=2307) │
│ SHORT  │ 0.5981   │ 63.6%    │ 0.2288   │ 83.6% @ 0.8 (n=750)  │
│ EMA    │ 0.5912   │ 67.6%    │ 0.2154   │ 80.6% @ 0.75 (n=470) │
└────────┴──────────┴──────────┴──────────┴──────────────────────┘

CV AUC (Long, 5-fold): 0.6247 ± 0.0192
Val AUC: Long=0.706, Short=0.671, EMA=0.694

Problémák:
1. AUC alacsonyabb test-en mint val-en (overfitting)
2. Early stop túl korán (53-95 fa a 800-ból) → underfitting gyanú
3. Recall magas (0.94-0.98) de precision alacsony → modell túl lazán jósol pozitívat

Top 5 Feature (EMA): Tick_Speed, Ter_S, Ter_R, Return_1bar, Sec_S

Következő lépések:
1. Erősebb regularizáció / több fa / kisebb lr
2. Optuna hyperopt a 3 modellre
3. Feature selection (csak top feature-ök)
4. Look-ahead bias ellenőrzés
5. Élő predikció integráció (predict server)