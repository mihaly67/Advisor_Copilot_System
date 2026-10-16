# Jules V5 Pipeline — Teljes Fájltérkép és Adatfolyam (2026.09.25.)

## KÖNYVTÁR STRUKTÚRA

```
scalper-copilot/
├── MQL5_Scripts/
│   ├── Merkava_Data_Miner_Script_v1_05_MTF.mq5  ← CSV1 generátor (M1 OHLCV + indikátorok)
│   └── Merkava_Master_Data_Miner_zigzag_v5.mq5   ← CSV2 generátor (M1 OHLCV + ZigZag pivotok)
├── Micro_LGBM/
│   ├── src/
│   │   ├── pipeline_master.py          ← Orchesztrátor (1→2→3→4→5 lépés)
│   │   ├── prado_dollar_bars.py        ← Tick→Dollar Bar ($444k küszöb)
│   │   ├── dom_feature_engineer_mtf.py ← Dollar Bar→Feature engineering (mikro)
│   │   ├── dom_labeler_v5.py           ← Triple Barrier címkézés (PT=1.5$, SL=1.0$, max=5)
│   │   ├── fuse_macro_to_dollar_bars.py ← Makro pivot fúzió (merge_asof backward)
│   │   ├── train_lgbm_fusion_v5.py     ← LGBM tanítás
│   │   ├── create_meta_dataset.py      ← Meta-label generálás
│   │   ├── optuna_threshold_tuner_v5.py ← 4D küszöb optimalizálás
│   │   ├── sept_oos_bias_test.py       ← OOS bias teszt (Z.ai V8 adaton)
│   │   ├── kaufman_ama.py              ← Kaufman AMA implementáció
│   │   ├── [éles scriptek: mt5_live_copilot_v*.py, copilot_hud.py, stb.]
│   │   └── beta_tools/                 ← Kísérleti scriptek (SHAP, ZigZag tuning)
│   ├── data/
│   │   ├── features_dollar_bars_3MTF_v3.csv   ← 28212 sor, 2026-06-15→2026-09-01 (TELJES mikro adat)
│   │   ├── labeled_dollar_bars_v5_strict.csv   ← 75451 sor, 2026-05-27→2026-07-17 (TELJES labeled)
│   │   ├── fused_features_dollar_bars.csv      ← 4295 sor, 2026-07-20→2026-07-23 (EXAM ONLY!)
│   │   ├── fused_features_dollar_bars_mom.csv  ← ? (momentum variáns)
│   │   ├── fused_v5_offline.csv                ← ? (offline vizualizáció)
│   │   ├── exam_blind_fused.csv                ← 4295 sor (blind exam fúzió)
│   │   ├── meta_labeled_bars_v5.csv            ← Meta-label (LGBM kimenet)
│   │   ├── meta_labeled_fused_v5.csv           ← Meta-label (fused)
│   │   └── meta_labeled_fused_v5_mom.csv       ← 4295 sor, VÉGSŐ adat (P_Long, Meta_Label)
│   └── models/
│       └── lgbm_model_fusion_v5_tuned.pkl      ← A betanított LGBM modell
├── Macro_Regime/
│   ├── src/
│   │   ├── macro_feature_engineer.py   ← ZigZag pivot feature-ök számítása
│   │   ├── macro_labeler.py            ← Makro regime címkézés (lookahead=4!)
│   │   ├── optuna_catboost_tuner.py    ← CatBoost hyperopt
│   │   └── trade_analyzer_meta_regime.py ← Meta-regime szűrés
│   ├── data/
│   │   ├── Master_ZigZag_GCEQ26_M1.csv    ← 79051 sor, 2026-05-03→2026-07-31 (M1+ZigZag pivotok)
│   │   ├── Macro_GCEQ26_PERIOD_M1.csv     ← M1 makro adat (2026-07-19→2026-07-31)
│   │   ├── Macro_GCEQ26_PERIOD_M5.csv     ← M5 makro adat
│   │   └── Macro_GCEQ26_PERIOD_M15.csv    ← M15 makro adat
│   └── models/ ← CatBoost/Ridge modellek (NEM releváns az LGBM pipeline-hez)
└── LightGBM "Feature Fusion".md  ← Dokumentáció
```

## ADATFOLYAM (PONTOS, FORRÁSKÓDBÓL)

### Lépés 1: MQ5 Script 1 → Nyers M1 Tick CSV
**Script:** `Merkava_Data_Miner_Script_v1_05_MTF.mq5`
- **Bemenet:** MT5 tick adat (GCEQ26 szimbólum)
- **Kimenet CSV:** M1 OHLCV + NavSystem indikátorok (RSI, WPR, Stoch, MACD, Pulse, MFI, EMA25/50/150/300) + MTF (EMA50_M5, RSI_M5, MACD_M5, EMA150_M15, RSI_M15)
- **Időtartomány input:** `InpStartDate=2025.03.09`, `InpEndDate=2026.06.13`
- **Leakage védelem:** M5/M15 shift+1 (csak lezárt gyertyák)

### Lépés 2: MQ5 Script 2 → ZigZag Pivot CSV
**Script:** `Merkava_Master_Data_Miner_zigzag_v5.mq5`
- **Bemenet:** MT5 M1 OHLCV (90 nap history)
- **Kimenet CSV:** `Master_ZigZag_GCEQ26_M1.csv`
  - Oszlopok: Time, Open, High, Low, Close, TickVolume, RealVolume, Micro_R, Micro_S, Sec_R, Sec_S, Ter_R, Ter_S
- **ZigZag engine paraméterek:**
  - Micro: depth=12, deviation=5, backstep=3
  - Secondary: depth=50, deviation=30, backstep=12
  - Tertiary: depth=200, deviation=30, backstep=12
- **Pivot extension:** Forward-fill — ha nincs új pivot, az előző marad. Nincs breakout kezelés.
- **Időtartomány:** 2026-05-03 → 2026-07-31 (79051 M1 bar)

### Lépés 3: Python → Dollar Bar OK
**Script:** `prado_dollar_bars.py`
- **Bemenet:** MQ5 tick CSV (Bid/Ask + volume)
- **Kimenet:** Dollar Bars (`Start_Timestamp, End_Timestamp, OHLCV, Bid/Ask_Volume, Total_Dollar_Value, 5m/15m/30m_Close`)
- **Küszöb:** $444,000

### Lépés 4: Python → Mikro Feature Engineering
**Script:** `dom_feature_engineer_mtf.py`
- **Bemenet:** Dollar Bars CSV
- **Kimenet:** `features_dollar_bars.csv` (vagy 3MTF_v3)
- **Feature csoportok:**
  1. **OBI**: OBI_Raw, OBI_ZScore (Ask-Bid imbalance, rolling 100 z-score)
  2. **Velocity/Speed**: Price_Velocity, Tick_Speed (1/bar_duration_sec)
  3. **MTF Distances**: Dist_5m, Dist_15m, Dist_30m ((Close-MTF_Close)/Close*100)
  4. **ATR Proxy**: 15-bar ATR
  5. **Mikro oscillátorok**: RSI_14, MACD_Hist, BB_ZScore, ROC_5, MFI_5
  6. **M15 resampled**: Ugyanezek M15 időtávön (merge_asof backward, leakage-free)
  7. **M30 resampled**: Ugyanezek M30 időtávön
- **MINDEN feature `.shift(1)`** — nincs lookahead a mikro feature-ökben
- **Szűrés:** Csak 08:00-23:59 (éjszakai illikvid szakasz eldobva)

### Lépés 5: Python → V5 Címkézés
**Script:** `dom_labeler_v5.py`
- **Bemenet:** `features_dollar_bars_3MTF_v3.csv` (28212 sor)
- **Kimenet:** `labeled_dollar_bars_v5_strict.csv` (75451 sor)
- **Label logika:**
  - Entry = `Open[i+1]` (NINCS lookahead)
  - PT = 1.5$ (abszolút dollár), SL = 1.0$ (abszolút dollár), max_bars = 5
  - Intra-bar wick kiértékelés (SL+PT egyszerre → SL nyer)
  - 3 osztály: +1 (Long PT hit), -1 (Short PT hit), 0 (Noise)
- **FIGYELEM:** 75451 sor → 2026-05-27→2026-07-17. Ez NEM egyezik a 3MTF v3 28212 sorával!

### Lépés 6: Python → Makro Pivot Fúzió
**Script:** `fuse_macro_to_dollar_bars.py`
- **Bemenet:**
  - Mikro: `features_dollar_bars_3MTF_v3.csv` (28212 sor)
  - Makro: `Master_ZigZag_GCEQ26_M1.csv` (79051 M1 bar)
- **Kimenet:** `fused_features_dollar_bars.csv`
- **Fúzió:** `merge_asof(left_on=End_Timestamp, right_on=Time, direction='backward')`
- **Hozzáadott feature-ök (ZigZag-ból):**
  - `Dist_Micro_R = (Micro_R - Close) / ATR_14`  ← (Level - Close)
  - `Dist_Micro_S = (Close - Micro_S) / ATR_14`  ← (Close - Level)
  - Dist_Sec_R/S, Dist_Ter_R/S (ugyanez a képlet)
  - `Stoch_State_M1 = (Stoch(2,3,3) - 50) / 50`
  - `Upper_Wick_ATR`, `Lower_Wick_ATR`
- **ATR_14 a ZigZag M1 adaton** — NEM a dollar bar adaton!

### Lépés 7: Python → LGBM Tanítás
**Script:** `train_lgbm_fusion_v5.py`
- **Bemenet:** `fused_features_dollar_bars.csv` + `labeled_dollar_bars_v5_strict.csv`
- **Merge:** `pd.merge(left_index=True, right_index=True)` ← **INDEX ALAPÚ!**
- **Valódi feature lista** (amik megvannak a fused CSV-ben):
  1. Tick_Speed
  2. Dist_Micro_R, Dist_Micro_S
  3. Dist_Sec_R, Dist_Sec_S
  4. Dist_Ter_R, Dist_Ter_S
  5. Stoch_State_M1
  6. Upper_Wick_ATR, Lower_Wick_ATR
  **= 10 FEATURE** (a 27-ből csak 10 van meg a fused CSV-ben!)
- **Split:** `train_test_split(shuffle=False, test_size=0.2)` — időrendi
- **LGBM:** n_estimators=781, lr=0.0142, num_leaves=57, max_depth=6, min_child_samples=24

### Lépés 8: Python → Meta-Label Generálás
**Script:** `create_meta_dataset.py`
- LGBM → P_Long, P_Short, P_Noise
- 4D threshold: TH_LONG=0.35, TH_SHORT=0.36, TH_NOISE_MAX=0.47
- Meta_Label: 1 (TP), 0 (FP), -1 (no signal)

## IDŐTARTOMÁNYOK ÖSSZEHASONLÍTÁSA

| Adat | Sorok | Eleje | Vége | Megjegyzés |
|---|---|---|---|---|
| features_3MTF_v3 | 28212 | 2026-06-15 | 2026-09-01 | Teljes mikro adat |
| labeled_v5_strict | 75451 | 2026-05-27 | 2026-07-17 | Teljes labeled (MÁS IDŐTARTOMÁNY!) |
| ZigZag_M1 | 79051 | 2026-05-03 | 2026-07-31 | Teljes pivot adat |
| fused | 4295 | 2026-07-20 | 2026-07-23 | EXAM ONLY (3 nap!) |
| meta_labeled_v5_mom | 4295 | 2026-07-20 | 2026-07-23 | Végső adat = EXAM |

## KRITIKUS PROBLÉMÁK

### PROBLÉMA 1: A fused CSV CSAK EXAM ADAT!
A `fused_features_dollar_bars.csv` csak 4295 sor (júl 20-23). A `train_lgbm_fusion_v5.py` ezen tanul!
Ez azt jelenti: a modell **3 nap adaton** tanult és **0 nap OOS** validáción.

### PROBLÉMA 2: Index merge NEM időalapú!
`pd.merge(df, df_labels[['Target_Label']], left_index=True, right_index=True)`
- Fused: 4295 sor (júl 20-23)
- Labeled: 75451 sor (máj 27-júl 17)
- A merge a fused első 4295 sorához a labeled első 4295 sorát rendeli — ami **máj 27-jún** eleji label-ek!
- **A feature-ök július 20-23-ról vannak, a label-ek május 27-ről!**

### PROBLÉMA 3: 3MTF v3 vs Labeled időtartomány nem fedi egymást
- 3MTF v3: 2026-06-15 → 2026-09-01
- Labeled: 2026-05-27 → 2026-07-17
- Nincs teljes átfedés!

### PROBLÉMA 4: A ZigZag csak 2026-07-31-ig tart
Ha új adatot gyűjtünk (szeptember), a ZigZag scriptet újra kell futtatni.

## KÉT CSV AMIT GYŰJTENI KELL

### CSV 1: MQ5 MTF Data Miner
**Script:** `Merkava_Data_Miner_Script_v1_05_MTF.mq5`
**Tartalom:** M1 OHLCV + NavSystem indikátorok + MTF indikátorok
**Cél:** Ebből lesznek a Dollar Bar-ok + mikro feature-ök
**Időtartomány:** 5 nap (OOS heti adat)

### CSV 2: MQ5 ZigZag Data Miner
**Script:** `Merkava_Master_Data_Miner_zigzag_v5.mq5`
**Tartalom:** M1 OHLCV + Micro_R/S, Sec_R/S, Ter_R/S (forward-filled pivotok)
**Cél:** Ebből lesznek a makro pivot feature-ök
**Paraméterek:** InpLookbackDays=90 (elég a pivot history-hoz)
