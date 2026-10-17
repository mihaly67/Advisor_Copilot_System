# Session: jules_reverse_engineering_complete
*Időbélyeg: 2026-10-04T09:12:00.593273*

Jules rendszer teljes visszafejtése — 2026-10-04

# JULES RENDSZER ARCHITEKTÚRA (Dollar Bar, Tick-szintű)

## 1. DOLLAR BAR ENGINE (prado_dollar_bars.py)
- Threshold: $444,000
- Tick-szintű: NEM vár gyertya zárásra, bármikor bekövetkezhet
- Mid_Price = (Bid + Ask) / 2
- Dollar_Value = (Bid_Volume + Ask_Volume) × Mid_Price
- Ha cumulative_dollar_val >= 444000 → bar lezárul, Close = aktuális Mid_Price
- Forward-fill MTF: 5m_Close, 15m_Close, 30m_Close a bar végén

## 2. FEATURE ENGINEERING (dom_feature_engineer_mtf.py)
### Mikro (Dollar Bar szintű):
- OBI_ZScore (100-as rolling Z-score), shift(1)
- Tick_Speed = 1/Bar_Time_Seconds, shift(1)
- Price_Velocity = diff(1)/Bar_Time_Seconds, shift(1)
- ATR_Proxy (15 periódus), shift(1)
- Micro: RSI_14, MACD_Hist, BB_ZScore, ROC_5, MFI_5 (mind shift(1))

### Makro konfluencia:
- Dist_5m, Dist_15m, Dist_30m (Close - MTF_Close)/Close*100, shift(1)
- M15: RSI_14, MACD_Hist, BB_ZScore, ROC_5, MFI_5 (resample + merge_asof backward)
- M30: ugyanezek (resample + merge_asof backward)

### Trading hours szűrés: 08:00-23:59

## 3. MAKRO FÚZIÓ (fuse_macro_to_dollar_bars.py)
### ZigZag Geometria (MQL5 EA → Python):
- Dist_Micro_R/S, Dist_Sec_R/S, Dist_Ter_R/S (pivot távolság / ATR_14)
- Upper_Wick_ATR, Lower_Wick_ATR (wick / ATR_14)
- Stoch_State_M1 = (Stoch_K - 50) / 50 → normalized [-1, 1]
- merge_asof(direction='backward') → NEM lookahead

## 4. V5 STRICT WICK LABELER (dom_labeler_v5.py)
- Triple barrier: PT=1.5$, SL=1.0$, max_bars=5
- Entry = OPEN of NEXT bar (no lookahead)
- Intra-bar wick evaluation (High/Low alapú)
- Intra-bar ambiguity: SL wins over PT (konzervatív)
- Output: -1=Short, 0=Noise, 1=Long

## 5. LGBM V5 FUSION MODEL (train_lgbm_fusion_v5.py)
### 10 Feature:
1. Tick_Speed
2. Dist_Micro_R (ATR-normalized)
3. Dist_Micro_S (ATR-normalized)
4. Dist_Sec_R
5. Dist_Sec_S
6. Dist_Ter_R
7. Dist_Ter_S
8. Stoch_State_M1 (normalized [-1,1])
9. Upper_Wick_ATR
10. Lower_Wick_ATR

### LGBM Paraméterek:
- n_estimators=781, learning_rate=0.0142
- num_leaves=57, max_depth=6
- min_child_samples=24, colsample_bytree=0.566
- class_weight='balanced'
- objective='multiclass', random_state=42
- 3-class: 0=Short, 1=Noise, 2=Long

## 6. JULES THRESHOLD LOGIC (mt5_live_copilot_v2.00.py)
- P_LONG_MIN = 0.350
- P_NOISE_MAX_LONG = 0.470
- P_SHORT_MIN = 0.360
- P_NOISE_MAX_SHORT = 0.470
- Long: p_long > 0.350 AND p_noise < 0.470 AND p_long > p_short
- Short: p_short > 0.360 AND p_noise < 0.470 AND p_short > p_long

## 7. STOCHASTIC HARD FILTER
- Block Long if Stoch_State_M1 < 0 (Stoch_K < 50)
- Block Short if Stoch_State_M1 > 0 (Stoch_K > 50)

## 8. STABILITY FILTER
- window=3 (deque(maxlen=3))
- is_stable = (len(signal_history)==3 and len(set(signal_history))==1)
- Csak stabil jelek mennek át a HUD-ra

## 9. MAKRO REGIME FILTER (trade_analyzer_meta_regime.py)
- EMA crossover: fast=50, slow=200
- Hard filter: Block Shorts in Uptrend, Block Longs in Downtrend

## 10. ÉLES PIPELINE
- TCP port 5555: Makro receiver (MT5 ZigZag JSON)
- TCP port 5556: Tick receiver (MT5 tick stream)
- ZMQ port 5557: HUD publisher (valós idejű kijelző)
- Dollar bar accumulation O(1): persistent bar_open/high/low

## KIZÁRANDÓ (LSTM/CatBoost nyomok):
- nn_meta_advisor.py, nn_meta_model.py
- lstm_feature_importance.csv, lstm_importance_heatmap.png
- macro_catboost_M1_zigzag.cbm
- optuna_catboost_tuner.py, catboost_info/

## ADATOK:
- fused_features_dollar_bars.csv: 4296 sor (exam/blind)
- labeled_dollar_bars_v5_strict.csv: 75452 sor (historical)
- Model: lgbm_model_fusion_v5_tuned.pkl (12 MB)

## MCP BRIDGE: FUT (PID 5809, server.py)
