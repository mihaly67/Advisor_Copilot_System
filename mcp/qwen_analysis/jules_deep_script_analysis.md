# Jules Rendszer Mély Script-elemzés — Teljes Visszafejtés

**Dátum**: 2026-10-03 | **Státusz**: KÉSZ | **Kihagyva**: LSTM, CatBoost, Kaufman AMA

---

## 1. PIPELINE (pipeline_master.py)
1. prado_dollar_bars.py → Tick → Dollar Bar ($444K)
2. dom_labeler_v5.py → Triple Barrier (PT=$1.5, SL=$1.0, max=5, strict wick)
3. fuse_macro_to_dollar_bars.py → ZigZag + Wick + Stoch → fúzió
4. train_lgbm_fusion_v5.py → LGBM tréning (fix hiperparaméterek)

## 2. DOLLAR BAR MOTOR (prado_dollar_bars.py)
- threshold=444000, Dollar_Value=Total_Trade_Vol*Mid_Price
- Iteratív akkumuláció, ha >= threshold → bar lezárul
- Forward-fill MTF: 5m, 15m, 30m Close a bar végére
- **Adaptív időzés**: aktív ~1-3 perc, illikviden 10+ perc → EZ szünteti meg a lagot

## 3. A 10 FEATURE (fuse_macro_to_dollar_bars.py)
| Feature | Formula | Jelentés |
|---------|---------|----------|
| Dist_Micro_R/S | (Micro_R - Close) / ATR_14 | Távolság legközelebbi R/S |
| Dist_Sec_R/S | (Sec_R - Close) / ATR_14 | Távolság másodlagos R/S |
| Dist_Ter_R/S | (Ter_R - Close) / ATR_14 | Távolság harmadlagos R/S |
| Upper_Wick_ATR | (High - max(O,C)) / ATR_14 | Csalókanégy-felső |
| Lower_Wick_ATR | (min(O,C) - Low) / ATR_14 | Csalókanégy-alsó |
| Stoch_State_M1 | (Stoch_K - 50) / 50 | Momentum [-1, +1] |
| Tick_Speed | len(bar_ticks) | Tick sűrűség proxy |
**V4→V5 evolúció**: 27+ feature → 10. A 6 ZigZag Dist mindent kódol.

## 4. LABELER (dom_labeler_v5.py)
- Entry = Open of NEXT bar (no lookahead!)
- PT=$1.5, SL=$1.0, max_bars=5
- Intra-bar SL/PT vizsgálat, ambiguitás→SL nyer (worst-case)
- Aszimmetria: PT/SL = 1.5x

## 5. TRAINER (train_lgbm_fusion_v5.py)
n_estimators=781, lr=0.0142, num_leaves=57, max_depth=6, min_child_samples=24, colsample_bytree=0.566, class_weight=balanced


## 8. MACRO REGIME (Macro_Regime/src/)
- macro_feature_engineer.py: 6 Dist + Stoch_State_M1 M1 ZigZag CSV-ből
- macro_labeler.py: Dynamic ATR threshold → Uptrend/Downtrend/Range
- trade_analyzer_meta_regime.py: EMA-50/200 Hard Filter (Uptrend→Short blokkolva)

## 9. TESZT SCRIPTEK
- evaluate_blind_exam_v5.py: Blind exam Jul 23, 2D threshold: 0.494/0.351
- sept_oos_bias_test.py: OOS Jul 24-Sep 1 → lookahead bias teszt
- live_forward_test_analyzer.py: RAW vs Stoch-filtered → "Sacrificed Wins / Saved Losses"
- optuna_threshold_tuner_v5.py: 3 threshold tuning [0.30-0.60], profit-based

## 10. JULES 7 ALAPELVE
| # | Elv | Bizonyíték |
|---|------|-----------|
| 1 | A bar típus a feature | $444K adaptív időzés |
| 2 | Tíz elég | 27+→10, 6 Dist mindent kódol |
| 3 | Hard filter > soft feature | Stoch+EMA utólag, fizikai szabály |
| 4 | Meta-ellenőrzés | KIHAGYVA v1-hez |
| 5 | O(1) él | dict+deque, nincs Pandas, ~1ms |
| 6 | Aszimmetria mindenhol | PT/SL=1.5, P_L/P_S=0.35/0.36 |
| 7 | Az EA az igazság | Python nem számol ZigZag-ot |

## 11. Z.ai IMPLEMENTÁCIÓS TERV
### Implementálandó:
1. **Dollar Bar Engine**: $444K, O(1) OHLC akkumuláció
2. **10 Feature**: 6 Dist + 2 Wick + Stoch + Tick_Speed
3. **LGBM UJRA tanítani** dollar bar adaton! Fix hiperparaméterek: 781/0.0142/57/6/24/0.566
4. **Döntés**: 4D threshold + Stoch filter + stability
5. **O(1) architektúra**: dict+Lock, nincs Pandas

### Kihagyva: ❌ LSTM, CatBoost, Kaufman AMA

### NYITOTT KÉRDÉS: Z.ai honnan kapja a ZigZag pivotokat és Stoch_K-t?
- Opció A: Saját ZigZag Pythonban (lassabb, független)
- Opció B: Z.ai EA küldi (mint Jules)
- Opció C: Pre-computed + merge_asof (offline)

## 6. DÖNTÉS LOGIKA — 3 rétegű védelem
### 6a. 4D Aszimmetrikus Threshold
P_LONG_MIN=0.350, P_SHORT_MIN=0.360 (ASZIMMETRIKUS!), P_NOISE_MAX=0.470
+ p_long > p_short (Long) vagy p_short > p_long (Short)

### 6b. Stochastic Hard Filter
signal==1 and stoch_state<0.0 → Long blokkolva (Stoch<50)
signal==-1 and stoch_state>0.0 → Short blokkolva (Stoch>50)

### 6c. Stability Filter
signal_history=deque(maxlen=3), is_stable=(len==3 and len(set)==1)

## 7. ÉLŐ RENDSZER (mt5_live_copilot_v2.00.py)
### 2 Thread: MacroReceiver(TCP:5555), TickReceiver(TCP:5556)
### O(1) trükkök: bar_open/high/low globális, macro_cache dict+Lock, deque(maxlen=15) ATR
### Tick→Bar→Inferencia:
TICK→mid_price=(bid+ask)/2→dollar_vol=mid*vol→current_dollar_volume+=dollar_vol
→O(1) high/low update→if >=$444K: bar lezárul→ATR deque-ból→10 feature dict→predict_proba→4D threshold→Stoch filter→stability→signal→ZMQ PUB:5557
