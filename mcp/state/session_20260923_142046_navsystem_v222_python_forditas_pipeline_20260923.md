# Session: navsystem_v222_python_forditas_pipeline_20260923
*Időbélyeg: 2026-09-23T14:20:46.602038*

# NavSystem v2.22 Indikátorok → Python Fordítás + Pipeline Feature Terv
*Időbélyeg: 2026-09-23*

## NavSystem v2.22 Összetevők (4 indikátor modul)

### 1. PULSE (Hybrid MACD) — `m_handle_hybrid_macd`
- **MQL5:** `iCustom(path_hybrid, ...)` — Hybrid_Momentum_Pulse_v1.05
- **Kimenet:** m_val_macd (buffer 0), m_val_dfcurve (buffer 2)
- **Python fordítás:**
  - MACD: `ta.trend.MACD(close, window_slow=26, window_fast=12, window_sign=9).macd_diff()`
  - DF Curve (Keltner + BB skalázott MACD): `ta.volatility.BollingerBands` + `ta.volatility.KeltnerChannel` → skálázott diff
  - **De:** A Scalper_Copilot_Miner már tartalmazza `RSI_M15` és `ATR_M15`-t → a Pulse MACD-t Python is tudja számolni a dollar bar Close-n

### 2. FLOW (HybridFlowIndicator v1.126) — `m_handle_flow`
- **MQL5:** `IndicatorCreate(IND_CUSTOM, ...)` — HybridFlowIndicator_v1.126
- **Kimenet:** m_val_flow_mfi (buffer 0), m_val_flow_delta (buffer 2), m_val_flow_roc (buffer 4)
- **Python fordítás:**
  - **MFI (Money Flow Index):** `ta.volume.MFIIndicator(high, low, close, volume, window=f_mfi_period).money_flow_index()`
  - **Delta End:** Python implementáció kell — (Close-Low)/(High-Low) pozíció × volume akkumulált
  - **VROC (Volume Rate of Change):** `((volume_curr - volume_prev) / volume_prev) * 100`
  - **Megjegyzés:** A `dom_feature_engineer_mtf.py` már számol `Micro_MFI_5`-öt és `M15_MFI_5`/`M30_MFI_5`-öt

### 3. CONTEXT (HybridContextIndicator v3.28) — `m_handle_context`
- **MQL5:** `iCustom(ctx.path, ...)` — HybridContextIndicator_v3.28
- **Kimenet (13 mező):**
  - ZigZag Pivot: Micro_R/S, Sec_R/S, Ter_R/S (buffer 0-5)
  - ZigZag Pivot Price: Micro_P, Sec_P, Ter_P (buffer 10-12)
  - Trend MA: Fast, Medium, Slow, Super (buffer 6-9)
- **Python fordítás:**
  - **ZigZag S/R:** MÁR BENNE VAN a Scalper_Copilot_Miner CSV-ben! (Micro_R/S, Sec_R/S, Ter_R/S)
  - **Trend MA:** `ta.trend.EMAIndicator(close, window=tr_fast/medium/slow/super).ema_indicator()`
  - **Pivot Price (P):** A ZigZag pivot pontok ára — ez új, a Scalper_Copilot_Miner NEM gyűjti
  - **Megjegyzés:** A Pivot Price (Micro_P, Sec_P, Ter_P) jelzi, hol van a pivot, nem csak a S/R szintet

### 4. MOMENTUM (Hybrid Momentum WPR+Stoch v1.04) — `m_handle_test_mom`
- **MQL5:** `iCustom(mom.path, ...)` — Hybrid_Momentum_WPR_Stoch_v1.04
- **Kimenet:** m_val_wpr, m_val_stoch_k
- **Python fordítás:**
  - **WPR (Williams' %R):** `ta.momentum.WilliamsRIndicator(high, low, close, lbp=wpr_period).williams_r()`
  - **Stoch %K:** `ta.momentum.StochasticOscillator(high, low, close, window=stoch_k, smooth_window=stoch_d).stoch()`
  - **Megjegyzés:** A `fuse_macro_to_dollar_bars.py` már számol `Stoch_State_M1`-et

### 5. RSI (natív) — `m_handle_rsi`
- **MQL5:** `iRSI(symbol, period, 5, PRICE_CLOSE)`
- **Kimenet:** m_val_rsi (period=5)
- **Python fordítás:** `ta.momentum.RSIIndicator(close, window=5).rsi()`
- **Megjegyzés:** Ez RSI(5) — gyors RSI, NEM az RSI_M15 (14) ami a Scalper_Copilot_Miner-ben van

---

## Teljes Feature Lista — Pipeline-ba kerülő

### A. MQ5-ből jövő (Scalper_Copilot_Miner CSV — forward-fill dollar barra)
| Feature | CSV oszlop | Megjegyzés |
|---|---|---|
| MTF 1m/5m/15m/30m Close | 1m_Close, 5m_Close, 15m_Close, 30m_Close | Makró távolság számításhoz |
| ATR M15 | ATR_M15 | Volatilitás proxy |
| RSI M15 | RSI_M15 | Makró momentum |
| ZigZag Micro R/S | Micro_R, Micro_S | Mikro támaszt/ellenállás |
| ZigZag Sec R/S | Sec_R, Sec_S | Szekunder támaszt/ellenállás |
| ZigZag Ter R/S | Ter_R, Ter_S | Tercier támaszt/ellenállás |
| Spread | Spread | Likviditás proxy |

### B. Python számolta — Dollar Bar szintű (dom_feature_engineer_mtf.py)
| Feature | Python kód | Könyvtár |
|---|---|---|
| OBI Raw | `(Ask_Vol - Bid_Vol) / Total_Vol` | numpy |
| OBI ZScore | rolling(100) z-score | numpy+pandas |
| Bar Time Seconds | `(End - Start).total_seconds()` | pandas |
| Price Velocity | `Close.diff() / Bar_Time` | numpy |
| Tick Speed | `1 / Bar_Time` | numpy |
| Dist 5m/15m/30m | `(Close - MTF_Close) / Close * 100` | numpy |
| ATR Proxy | rolling(15) ATR on OHLC | ta.volatility |
| Micro RSI(14) | `RSIIndicator(Close, 14)` | ta.momentum |
| Micro MACD Hist | `MACD(Close).macd_diff()` | ta.trend |
| Micro BB ZScore | `(Close - BB_mid) / BB_std` | ta.volatility |
| Micro ROC(5) | `ROCIndicator(Close, 5)` | ta.momentum |
| Micro MFI(5) | `MFIIndicator(H,L,C,V,5)` | ta.volume |

### C. Python számolta — NavSystem v2.22 fordítás (ÚJ!)
| Feature | MQL5 eredeti | Python kód | Könyvtár |
|---|---|---|---|
| Pulse MACD | Hybrid_Pulse MACD | `MACD(Close).macd_diff()` | ta.trend |
| Pulse DF Curve | Keltner+BB scaled | `(BB_upper - Keltner_upper) / ATR` | ta.volatility |
| Flow MFI | HybridFlow MFI | `MFIIndicator(H,L,C,V,period)` | ta.volume |
| Flow Delta | Delta End | `(C-L)/(H-L) power × Vol akkumulált` | numpy |
| Flow VROC | Volume ROC | `(Vol_curr - Vol_prev) / Vol_prev * 100` | numpy |
| RSI Fast (5) | iRSI(5) | `RSIIndicator(Close, 5)` | ta.momentum |
| WPR | Williams %R | `WilliamsRIndicator(H,L,C,period)` | ta.momentum |
| Stoch %K | Stochastic K | `StochasticOscillator(H,L,C,window,smooth)` | ta.momentum |
| Trend Fast MA | EMA fast | `EMAIndicator(Close, window)` | ta.trend |
| Trend Medium MA | EMA medium | `EMAIndicator(Close, window)` | ta.trend |
| Trend Slow MA | EMA slow | `EMAIndicator(Close, window)` | ta.trend |
| Trend Super MA | EMA super | `EMAIndicator(Close, window)` | ta.trend |

### D. Python számolta — Geometria (fuse_macro → most beépül)
| Feature | Python kód | Könyvtár |
|---|---|---|
| Dist_Micro_R/S ATR-norm | `(Micro_R - Close) / ATR_14` | numpy |
| Dist_Sec_R/S ATR-norm | `(Sec_R - Close) / ATR_14` | numpy |
| Dist_Ter_R/S ATR-norm | `(Ter_R - Close) / ATR_14` | numpy |
| Upper Wick ATR | `(High - max(Open,Close)) / ATR` | numpy |
| Lower Wick ATR | `(min(Open,Close) - Low) / ATR` | numpy |
| Stoch State M1 | `(Stoch_K - 50) / 50` | ta.momentum |

### E. M15/M30 Makró resample (Python — dom_feature_engineer_mtf.py)
| Feature | Python kód |
|---|---|
| M15/M30 RSI(14) | resample('15min'/'30min') → RSI |
| M15/M30 MACD Hist | resample → MACD |
| M15/M30 BB ZScore | resample → BB |
| M15/M30 ROC(5) | resample → ROC |
| M15/M30 MFI(5) | resample → MFI |

**DE:** Ha az MQ5-ből jövő RSI_M15 és ATR_M15 pontosabb, akkor ezek **HELYETTESÍTHETIK** a resample verziót! SHAP majd eldönti.

---

## Összes feature szám: ~45-50
- A (MQ5-ből): 13 oszlop
- B (Python mikro): 12 feature
- C (NavSystem fordítás): 12 feature
- D (Geometria): 7 feature
- E (Makró resample): 10 feature (vagy kevesebb, ha MQ5 helyettesít)

**SHAP + Optuna majd kiválasztja a ~20-30 legfontosabbat.**

---

## Könyvtár requirements
A pipeline-ben használt: `ta` (pandas-ta / technical-analysis)
- `ta.momentum.RSIIndicator` ✅
- `ta.trend.MACD` ✅
- `ta.volatility.BollingerBands` ✅
- `ta.volume.MFIIndicator` ✅
- `ta.momentum.StochasticOscillator` ✅
- `ta.momentum.WilliamsRIndicator` ✅ (ha nincs: `talib.WILLR`)
- `ta.trend.EMAIndicator` ✅
- `ta.momentum.ROCIndicator` ✅
- `ta.volatility.AverageTrueRange` ✅

Alternatíva: `talib` (TA-Lib C wrapper, 150+ indikátor, gyorsabb)
- Ha a `ta` könyvtár nem elég (pl. WPR hiányzik): `talib.WILLR(high, low, close, timeperiod)`

---

## Pipeline módosítás terv

### 1. prado_dollar_bars.py módosítása
- Bemenet: Scalper_Copilot_MTF_Data.csv (18 oszlop)
- Forward-fill dollar barra: MTF Close + ATR_M15 + RSI_M15 + ZigZag 6 oszlop + Spread
- Kimenet: dollar_bars.csv (~20 oszlop)

### 2. dom_feature_engineer_mtf.py módosítása
- Bemenet: dollar_bars.csv
- Új feature-ök hozzáadása a NavSystem v2.22 fordítás alapján:
  - Pulse: MACD + DF Curve
  - Flow: MFI + Delta + VROC
  - RSI Fast(5), WPR, Stoch %K
  - Trend MA: EMA fast/medium/slow/super
  - Geometria: ZigZag dist ATR-norm, Wick ATR, Stoch State
- Kimenet: features_dollar_bars.csv (~50 oszlop)

### 3. dom_labeler_v5.py — NEM VÁLTOZIK
- Triple Barrier: PT=1.5$, SL=1.0$, max_bars=5

### 4. train_lgbm_fusion_v5.py — NEM VÁLTOZIK (feature lista bővül)
- Új feature-ök hozzáadása a features listához

### 5. SHAP + Optuna — ÚJ LÉPÉS
- SHAP feature importance → heatmap
- Redundáns feature-ök azonosítása és kiszűrése
- 4D aszimmetrikus küszöb kalibráció

### 6. fuse_macro_to_dollar_bars.py — KIESŐ
- A ZigZag geometria beépül a dom_feature_engineer_mtf.py-ba