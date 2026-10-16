# EA Copilot Architektúra Audit — Valóság vs Leírás (2026-09-22)

## Forrás: `/data/ml/EA_Copilot_Architecture.md` vs tényleges fájlok

### 1. Adatgyűjtés (MQL5 Scripts)
- ✅ `Merkava_Master_Data_Miner_v5.mq5` — LÉTEZIK, M1 OHLCV + ZigZag pivot S/R
- ✅ `Tick_Exporter_Script_v3.mq5` — LÉTEZIK, nyers tick export
- ✅ `AI_Labeled_Data_Exporter_v8.1.mq5` — LÉTEZIK, címkézett adat export
- ⚠️ `Scalper_Copilot_Miner_v1.mq5` — Állítólag én írtam (memória ellenőrzendő!)
- ✅ `Feature_Exporter_Script.mq5` — LÉTEZIK (v2.2), de a leírás v4-et említ
- Kimenet: `/home/Jules/LGBM_mlops/Master_csv/raw/Scalper_Copilot_MTF_Data.csv` (4.2M sor, ~850MB)

### 2. Dollar Bar Képzés
- ✅ `prado_dollar_bars.py` — LÉTEZIK, Python alapú
- Küszöb: $444,000 (Mid_Price × Volume akkumuláció)
- Kimenet: `Master_csv/processed/dollar_bars.csv` — LÉTEZIK

### 3. Feature Engineering
- ✅ `fuse_macro_to_dollar_bars.py` — LÉTEZIK
  - ATR_14, ZigZag pivot távolságok (Dist_Micro_R/S, Dist_Sec_R/S, Dist_Ter_R/S)
  - Wick geometria (Upper/Lower_Wick_ATR)
  - Stoch_State_M1 (2-period Stoch - 50) / 50
- Kimenet: `features_dollar_bars.csv` — LÉTEZIK

### 4. Címkézés (Triple Barrier)
- ✅ `dom_labeler_v5.py` — LÉTEZIK (Strict Wick Triple Barrier)
  - PT=1.5×ATR, SL=1.0×ATR, MaxBars=5
  - Intra-bar High/Low kiértékelés (wick-aware)
  - Ambiguitás: ha SL+PT ugyanabban a barban, SL nyer (worst-case)
  - Entry: NEXT bar Open (no lookahead bias)
  - Kimenet: +1 (Long), -1 (Short), 0 (Noise)

### 5. ML Pipeline (LightGBM)
- ✅ `pipeline_master.py` — LÉTEZIK, 5 lépéses master:
  1. prado_dollar_bars.py (Dollar Bar generálás)
  2. dom_labeler_v5.py (Címkézés)
  3. fuse_macro_to_dollar_bars.py (Feature fúzió)
  4. optuna_lgbm_fusion_tuner.py (Hyperparameter tuning - KOMMENTEZVE)
  5. train_lgbm_fusion_v5.py (Betanítás)
- Model: `lgbm_model_fusion_v5_tuned.pkl` (joblib formátum)

### 6. Éles Végrehajtás (Live Copilot)
- ✅ `mt5_live_copilot_v2.00.py` — LÉTEZIK
  - ZMQ PUB socket: tcp://127.0.0.1:5557
  - Dollar Bar threshold: $444,000 (azonos az offline-al!)
  - FIFO buffer: collections.deque(maxlen=200)
  - Warmup: EA küld 15k tick → ~1000 Dollar Bar
  - Predikció: predict_proba(X) → p_long, p_short, p_noise
  - Döntési küszöbök: P_Long>0.33 és P_Noise<0.27 (vagy P_Short>0.33)
  - Signal history: deque(maxlen=3) a stabilitáshoz

### EA (Expert Advisor):
- `Merkava_Behavioral_Profiler_v2.1_Online.mq5` — LÉTEZIK az Experts mappában
- Ez a ZMQ publisher EA (port 5555-5557)

### 3 eltérés a leírástól:
1. `Scalper_Copilot_Miner_v1.mq5` — memória szerint én írtam (ellenőrzendő)
2. `Feature_Exporter_Script` v2.2 nem v4
3. Optuna lépés ki van kommentezve a pipeline_master.py-ban

### Pipeline logika:
```
MT5 MQL5 Scripts → raw CSV (4.2M sor) → prado_dollar_bars.py → dollar_bars.csv
→ dom_labeler_v5.py (Triple Barrier) → fuse_macro_to_dollar_bars.py (30 features)
→ train_lgbm_fusion_v5.py → lgbm_model.pkl → mt5_live_copilot_v2.00.py (ZMQ)
→ PyQt5 HUD (BUY/SELL/HOLD)
```
