# NavSystem v3 Final Pipeline — Teljes Dokumentáció

**Dátum:** 2026.09.26.  
**Projekt:** z-ai-copilot / NavSystem v3 Advisor  
**Cél:** Adatszivárgás audit → double-shift fix → proxy feature eltávolítás → SHAP pruning → Optuna kalibráció → végleges modell

---

## 1. Adatszivárgás Audit (6 ellenőrzés)

| Check | Eredmény | Akció |
|---|---|---|
| Feature shift | ✅ Nincs klasszikus lookahead | — |
| Pivot interakciók | ✅ Nincs szivárgás | — |
| Oversold WR | ✅ WR(fwd1) > WR(fwd0) — valódi jel | — |
| Nav_Consensus ↔ Slope_Close_14 | 🔴 r=+0.44 proxy label szivárgás | ELTÁVOLÍTVA |
| Label fwd5 WR=80% | ⚠️ Inherent to triple barrier | Elfogadva |
| Double-shift bug | 🔴 build .shift(1) + to_lgbm .shift(1) = 2-bar delay | JAVÍTVA |

## 2. Double-Shift Bug Javítás

**Probléma:** `build_nav_v3_features.py` `.shift(1)` + `navsystem_to_lgbm_features` `.shift(1)` = 2-bar delay  
**Megoldás:** Shift eltávolítva a build scriptből, csak `navsystem_to_lgbm_features` shift maradt  
**Fájl:** `/data/dev/projects/z-ai-copilot/src/build_nav_v3_features.py`

## 3. Proxy Feature Eltávolítás

Eltávolított feature-ök (54→51):
- `Nav_Consensus` — korrelált Slope_Close_14-gyel (r=+0.44)
- `Nav_LongVotes` — konszenzus része
- `Nav_ShortVotes` — konszenzus része

## 4. Iteratív SHAP Pruning

Minden kör: tanítás → SHAP → SHAP=0.0 feature-ek eldobása → újra

| Kör | Feature | Eldobva | OOS WR | OOS P |
|---|---|---|---|---|
| 0 | 51 | — | — | — |
| 1 | 48 | Delta_Direction, MFI_Oversold, MFI_Accel | 46.9% | +2981 |
| 2 | 47 | Delta_Accel | 47.6% | +3037 |
| 3 | 45 | VROC_Direction, VROC_Intensity | 46.7% | +2911 |
| 4 | 43 | MFI_Intensity, WPR_Intensity | 46.7% | +2885 |
| 5 | 42 | WPR_Oversold | 47.6% | +3067 |
| 6 | 39 | WPR_Overbought, Stoch_Direction, MFI_Overbought | 46.2% | +2914 |
| 7 | 36 | Stoch_Overbought, Stoch_Oversold, Delta_Intensity | 46.8% | +2992 |
| 8 | 34 | RSI_Intensity, DF_Intensity | 45.7% | +2833 |
| 9 | 33 | Stoch_Intensity | 46.9% | +2763 |
| 10 | **32** | RSI_Direction | **48.3%** | **+2802** |

**Végállapot: Nincs több SHAP=0.0 feature.** Minden remaining feature > 0.0002 SHAP.

## 5. Végső Modell Eredmények

| Metrika | Érték |
|---|---|
| Feature szám | **32** |
| OOS Win Rate | **48.3%** |
| OOS Profit | **+2802** |
| OOS Trades | 6222 |
| IS Win Rate | 54.7% |
| IS Profit | +1429 |
| IS Trades | 2231 |
| best_iteration | 520 |
| OOS Accuracy | 55.4% |

## 6. Optuna 4D Küszöbök

| Küszöb | Érték | Tartomány |
|---|---|---|
| th_long | **0.42** | 0.30–0.45 |
| th_short | **0.44** | 0.30–0.45 |
| th_noise_long | **0.55** | 0.45–0.60 |
| th_noise_short | **0.56** | 0.45–0.60 |

Optuna: 500 trial, TPE sampler, seed=42, objective=max profit

## 7. 32 Végső Feature

```
DF_Direction, DF_Accel, DF_Long, DF_Short, DF_ZeroCross
MACD_Direction, MACD_Intensity, MACD_Accel
MFI_Direction, WPR_Direction
RSI_Overbought, RSI_Oversold
OS_Long, OS_Short
Dist_Micro_R_ATR, Dist_Sec_R_ATR, Dist_Ter_R_ATR
Dist_Micro_S_ATR, Dist_Sec_S_ATR, Dist_Ter_S_ATR
Micro_R_Wick_Rej, Micro_R_Breakout
Sec_R_Wick_Rej, Sec_R_Breakout
Ter_R_Wick_Rej, Ter_R_Breakout
Micro_S_Wick_Bnc, Micro_S_Breakdown
Sec_S_Wick_Bnc, Sec_S_Breakdown
Ter_S_Wick_Bnc, Ter_S_Breakdown
```

## 8. 19 Eldobott Feature (SHAP=0.0)

```
Delta_Direction, Delta_Accel, Delta_Intensity  (Delta teljes haszontalan)
MFI_Oversold, MFI_Accel, MFI_Intensity, MFI_Overbought  (MFI csak Direction marad)
VROC_Direction, VROC_Intensity  (VROC teljes haszontalan)
WPR_Intensity, WPR_Oversold, WPR_Overbought  (WPR csak Direction marad)
Stoch_Direction, Stoch_Overbought, Stoch_Oversold, Stoch_Intensity  (Stoch teljes haszontalan)
RSI_Intensity, RSI_Direction  (RSI csak Overbought/Oversold marad)
DF_Intensity  (DF csak Direction/Accel/Long/Short/ZeroCross marad)
```

## 9. SHAP Top 10 (32 feature modell)

| Feature | SHAP |
|---|---|
| Sec_R_Breakout | 0.4959 |
| Dist_Sec_R_ATR | 0.4765 |
| Micro_R_Breakout | 0.4303 |
| Dist_Micro_S_ATR | 0.4240 |
| Ter_S_Wick_Bnc | 0.2019 |
| DF_Short | 0.1890 |
| Dist_Sec_S_ATR | 0.1712 |
| Micro_R_Wick_Rej | 0.1707 |
| MACD_Direction | 0.1439 |
| Dist_Ter_S_ATR | 0.1230 |

**Domináns csoportok:** Pivot távolság (Dist_*) + Pivot struktúra (Breakout/Wick) + MACD + DF

## 10. Modell Paraméterek

```python
LGBMClassifier(
    objective='multiclass', num_class=3,
    n_estimators=800, learning_rate=0.05,
    num_leaves=63, max_depth=7,
    min_child_samples=50,
    subsample=0.8, colsample_bytree=0.8,
    reg_alpha=0.1, reg_lambda=0.1,
    random_state=42
)
# Early stopping: 50 rounds
# Sample weight: class 1 (Noise) = 0.7
# Label: y+1 (Short=0, Noise=1, Long=2)
```

## 11. Label Paraméterek

```python
label_dataset(df, pt_mult=1.5, sl_mult=1.0, max_bars=15, slope_anchor_th=1.0)
# Profit: LW=2.0, LL=-1.0, SW=2.0, SL=-1.0
```

## 12. Mentés Helye

```
/data/dev/projects/z-ai-copilot/models/nav_v3_final/
├── model.pkl              (LGBM model, joblib)
├── features.txt           (32 feature, soronként)
├── shap_importance.csv    (feature, shap)
├── feature_importance.csv (feature, importance)
└── metrics.json           (összes metrika + küszöbök)
```

## 13. Kapcsolódó Fájlok

| Fájl | Leírás |
|---|---|
| `/data/dev/projects/z-ai-copilot/src/build_nav_v3_features.py` | Feature builder (double-shift fixelt) |
| `/data/dev/projects/z-ai-copilot/src/navsystem_indicators_v3.py` | Indikátor definíciók |
| `/data/dev/projects/z-ai-copilot/src/jules_labeler_v3.py` | Triple barrier labeler |
| `/data/dev/projects/z-ai-copilot/Master_csv/processed/nav_v3_fix_train.csv` | Tanító adat |
| `/data/dev/projects/z-ai-copilot/Master_csv/processed/nav_v3_fix_oos.csv` | OOS adat |
| `/data/dev/projects/z-ai-copilot/docs/viz_v5.html` | 5 napos Plotly vizualizáció |
| `/tmp/nav_v3_final.py` | Végső tanító+SHAP+Optuna script |

## 14. KÖVETKEZŐ TASK

1. **Session csatlakoztatás** Jules munkája alapján
2. **HUD integráció** — `start_hud_v1.17.sh` (Jules már elkészítette)
3. **Nav_v3_final modell bekötése** a HUD-ba (ZMQ pipeline)
4. **OOS forward-return equity curve** validáció
5. **navsystem_indicators_v3.py frissítése** — NAV_FEATURES_V3 lista szűkítése 32 feature-re

---

*Dokumentálta: Cline (Z.ai Copilot), 2026.09.26.*
