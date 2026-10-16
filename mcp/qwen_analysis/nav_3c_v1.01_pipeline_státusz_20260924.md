# NavSystem 3C Pipeline v1.01 — Projekt Státusz (2026.09.24.)

## 🎯 Cel
NavSystem indikátorok CSAK, 3-osztályos LGBM, Optuna nélkül, küszöbcserélés vizsgálat.

## 📊 Adat
- **CSV:** `labeled_dollar_bars_v8.csv` (31,139 bar, 122 oszlop, $444K threshold)
- **Label:** Target_3C = Side(+1/-1) + Target_Meta(0/1) → Short(-1)/Noise(0)/Long(+1)
  - Short: 26.1%, Noise: 48.4%, Long: 25.5%
- **Train/Test:** 80/20 (24,911 / 6,228)

## 🏋️ Modell: nav_3c_v1.01
- **Feature-k (14 NavSystem):** Pulse_MACD_Hist, Pulse_DF_Curve, Flow_MFI_5, Flow_Delta_10, Flow_VROC_5, WPR_14, Stoch_K, Stoch_D, RSI_Fast_5, RSI_M15, Micro_RSI_14, Regime_Long_Context, Regime_Short_Context, Trade_Flow_Imb
- **LGBM params:** multiclass, num_class=3, 500 trees, lr=0.05, depth=6, num_leaves=31
- **Küszöbök:** th_long=0.35, th_short=0.50, th_noise_long=0.30, th_noise_short=0.50

## 📈 Eredmények
- **Trades:** 1523 (Long:104, Short:1419)
- **Wins:** 781 (51.3%)
- **Opposite:** 20 (1.3%)
- **Profit:** +820
- **Avg/trade:** 0.538
- **Classification:** Short 51% prec, Noise 50%, Long 49% (accuracy 50%)

## 🔴 Küszöbcserélés Bug Analízis

### Régi threshold-ok (v5, short_zero=True Long-only modell):
- th_long=0.350, th_short=0.564, th_noise_long=0.202, th_noise_short=0.577
- Eredmény: Long:491, Short:58 (LONG-biased)
- **A threshold-ok Long-only modellhez kalibrálódtak!**

### Új threshold-ok (nav_3c_v1.01, 3-class):
- th_long=0.35, th_short=0.50, th_noise_long=0.30, th_noise_short=0.50
- Eredmény: Long:104, Short:1419 (SHORT-biased!)

### Kulcs felismerés:
**A NOISE threshold-ok dominálják a Long/Short egyensúlyt!**
- th_noise_long (alacsony) → szigorú → kevés Long
- th_noise_short (magas) → engedékeny → sok Short
- th_long/th_short maguk kevésbé hatnak
- **NEM egyszerű felcserélés** — a noise filter a szabályozó

### Konklúzió:
1. Régi Optuna threshold-ok nem transferálhatók 3-class-ra
2. Noise threshold a kulcs az egyensúlyhoz
3. User vizsgálja a viz_nav_3c_v1.01.html-t

## 📁 Fájlok
| Fájl | Útvonal |
|---|---|
| Train script | `src/train_lgbm_nav_3c_v1.01.py` |
| Viz script | `src/viz_nav_3c_v1.01.py` |
| Modell | `models/nav_3c_v1.01/model.pkl` |
| Features | `models/nav_3c_v1.01/features.txt` |
| Metrics | `models/nav_3c_v1.01/metrics.json` |
| Feat Importance | `models/nav_3c_v1.01/feature_importance.csv` |
| Viz HTML | `docs/viz_nav_3c_v1.01.html` |

## 🔢 Új Verzionálási Konvenció
- Script: `script_rövidítés_vX.YY.py` (pl. `train_lgbm_nav_3c_v1.01.py`)
- Modell: `models/rövidítés_vX.YY/` (model.pkl, features.txt, metrics.json, feature_importance.csv)
- HTML: `docs/viz_rövidítés_vX.YY.html`
- Rövidítések: nav_3c, nav_bin, full_3c, meta

## 📊 Feature Importance (nav_3c_v1.01)
1. Stoch_D (4094)
2. Flow_Delta_10 (3961)
3. Pulse_MACD_Hist (3915)
4. Pulse_DF_Curve (3790)
5. Trade_Flow_Imb (3604)
6. RSI_M15 (3415)
7. Micro_RSI_14 (3142)
8. RSI_Fast_5 (2885)
9. Flow_MFI_5 (2731)
10. WPR_14 (2689)
11. Flow_VROC_5 (2686)
12. Stoch_K (782) — alacsony!
13. Regime_Short_Context (107) — nagyon alacsony
14. Regime_Long_Context (44) — nagyon alacsony

## Korábbi hiperparaméterezési tapasztalatok (hivatkozás)
- Optuna 4D aszimmetrikus: Long-only modellhez kalibrálva, nem transferálható
- SHAP pruning 82→8: profit nem nőtt jelentősen
- 114 feature → 8 feature (v5): 47.8% WR
- **NavSystem 14 feature: 51.3% WR (jobb!)**
- V8 meta-labeling a legjobb labeling módszer