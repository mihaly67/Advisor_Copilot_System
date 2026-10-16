# 🎯 SCALPER COPILOT MESTERTERV — ALAPOKTÓL

> **Dátum:** 2026.09.20
> **Hely:** /data/LGBM_copilot/
> **Cél:** Merkava EA-hoz illeszthető scalper copilot backend teljes újratervezése
> **Referencia:** Jules LGBM_mlops (csak EA, HUD nélkül), /data/ml repók, xauusd-scalping-ai white paper

---

## MERKAVA EA HIBRID INDIKÁTOR HÍVÁSOK

A `Merkava_Behavioral_Profiler_v3.0_Online.mq5` a `CNavSystem`-en keresztül hívja:

### 1. HybridContextIndicator_v3.28 — PIVOT R/S SZINTEK
```
ctx.path = "Jules\HybridContextIndicator_v3.28"
m_nav_system.GetMicP/R/S()  // Micro pivot (3 depth, 5 dev, 3 back)
m_nav_system.GetSecP/R/S()  // Secondary pivot (4 depth, 5 dev, 3 back)
m_nav_system.GetTerP/R/S()  // Tertiary pivot (7 depth, 5 dev, 3 back)
```

### 2. Jules_Hybrid_Momentum_Pulse_v1.05 — MOMENTUM
```
m_nav_system.GetHybridMACD()  // MACD (FastEMA=3, SlowEMA=6, MACDScale=4.0)
m_nav_system.GetPulse()        // Momentum pulse
m_nav_system.GetWPR()          // WPR (Williams %R)
m_nav_system.GetStochK()      // Stochastic K (k=3, slow=2, d=2)
```

### 3. HybridFlowIndicator_v1.126 — FLOW INDICÁTOROK
```
m_nav_system.GetFlowMFI()    // MFI flow (period=5)
m_nav_system.GetFlowROC()    // ROC flow (period=5)
m_nav_system.GetFlowDelta()  // Delta flow (smooth=3, norm=100, scale=50.0)
```

### 4. Trend EMAs
```
m_nav_system.GetTrendFast()    // EMA(25) — Fast trend
m_nav_system.GetTrendMedium()  // EMA(50) — Medium trend
m_nav_system.GetTrendSlow()    // EMA(150) — Slow trend
m_nav_system.GetTrendSuper()   // EMA(300) — Super trend
```

### 5. Egyéb
```
m_nav_system.GetRSI()         // RSI
p.velocity, p.acceleration    // Price velocity/acceleration (PhysicsEngine)
```

---

## 📊 FÁZIS 1: PRIMARY DATA COLLECTION TIMEFRAME

- **M1 (1-minute) OHLCV + Tick adatok** — "high-frequency granularity for scalping"
- Session filtrálás:
  - London: 08:00-16:00 GMT
  - NYC: 13:30-20:00 GMT
  - Overlap: ~3.5h (max likviditás)
  - Asian: AVOID (kis volumen)

---

## 📊 FÁZIS 2: MULTI-TIMEFRAME FEATURE ENGINEERING

- M1 (MICRO) → Dollar Bars (dynamic threshold: $80K XAUUSD-nél)
- M5 (SHORT-TERM) → 5 perces momentum
- M15 (MEDIUM-TERM) → 15 perces mid-term trend
- H1 (TREND) → 1 órás major trend (MA crossover)

---

## 📊 FÁZIS 3: FEATURE-ÖK (20-25 FEATURE)

## ⚡ FÁZIS 4: SCALPING IDABLAK (EGY SCALPER HALÁLA = 2 ÓRA)

- **LONG POSITIONS:**
  - TP: 15-30 pips (150-300 points)
  - SL: 8-12 pips (80-120 points) — ATR-alapú
  - Max Bars: ≤1.5 óra (90 perc) — "scalper halála = 2 óra"!

- **SHORT POSITIONS (INRADAY SCALPS):**
  - TP: 3-5 pips (30-50 points)
  - SL: 1.5-2 pips (15-20 points) — ATR-alapú
  - Max Bars: ≤45-60 perc — nagyon rövid scalp!

- **ANTI-OVERLABELING:**
  - Min. 0.5 ATR távolság új címke előtt
  - Wick-aware: intra-bar High/Low stop-out

---

## 📊 FÁZIS 5: DYNAMIC DOLLAR BAR THRESHOLD

```python
# XAUUSD-specific threshold (nem $444K!)
XAUUSD_DOLLAR_THRESHOLD = 80000  # $80K

# EMA-based adaptive threshold
---

## 📊 FÁZIS 7: TRIPLE BARRIER LABELING (ATR-BASED)

```python
def triple_barrier_atr_based(df, tp_atr_mult=1.5, sl_atr_mult=1.0,
                            max_bars_long=90, max_bars_short=50):
    df['TP'] = df['Close'] + (df['ATR'] * tp_atr_mult)
    df['SL'] = df['Close'] - (df['ATR'] * sl_atr_mult)
    df['max_bars'] = np.where(df['position_type'] == 'long', max_bars_long, max_bars_short)
    df['min_atr_distance'] = df['ATR'] * 0.5  # anti-overlabeling
```

---

## 📊 FÁZIS 8: DUAL/MULTI SYSTEM ARCHITEKTÚRA (LGBM+MLP SUPERVISOR) — távoli jövő

### Option 1: Stacking Ensemble — **AJÁNLOTT**

```python
# Stage 1: Base Models
lgbm_probs = lgbm_model.predict_proba(features)[0]  # [P_Long, P_Short, P_Noise]
mlp_probs = mlp_model.predict_proba(features)[0]  # MLP meta-advisor

# Stage 2: Stacking Meta-Model (Ridge Regression)
P_Long = lgbm_probs[2] * 0.7 + mlp_probs[2] * 0.3
P_Short = lgbm_probs[0] * 0.7 + mlp_probs[0] * 0.3
P_Noise = lgbm_probs[1] * 0.7 + mlp_probs[1] * 0.3
```

### Option 2: Meta-Learning Regime Detection
- Stage 1: HMM regime (trend/range/breakout)
- Stage 2: Per-regime prediction (LGBM-Trend, LGBM-Range, MLP-Breakout)
- Stage 3: Meta-learner regime-based weights

### Option 3: Transformer Encoder + MLP
- Stage 1: Transformer self-attention on features
- Stage 2: MLP meta-prediction
- Stage 3: Fusion

---

## 📊 FÁZIS 9: WALK-FORWARD VALIDATION

- Purged k-fold CV (k=5, purge=10, embargo=5)
- OOS evaluation: Sharpe, drawdown, profit factor, win rate

---

## 📊 FÁZIS 10: ÉLES COPILON BACKEND

```python
# Unified thresholds (training = evaluation = live)
P_SIGNAL_MIN = 0.350
P_NOISE_MAX = 0.470
P_REGIME_THRESHOLD = 0.6

REGIME_WEIGHTS = {
    'trend': {'lgbm': 0.7, 'mlp': 0.3},
    'range': {'lgbm': 0.8, 'mlp': 0.2},
    'breakout': {'lgbm': 0.4, 'mlp': 0.6}
}
```

---

## 📊 FÁZIS 11: LIVE BACKEND ARCHITEKTÚRA

- TCP 5555: Macro JSON (pivot R/S, trend EMAs)
- TCP 5556: Tick (bid, ask, DOM, pivots)
- ZMQ PUB 5557: HUD JSON (signal, probabilities)

---

## 📊 FÁZIS 12: PLAYBACK TESZTELÉS

- Multi-day CSV beolvasása (legalább 5 nap)
- Real-time playback felgyorsítva
- Unified thresholds (training=evaluation=live)

---

## ÖSSZEFOGLALÓ — 12 FÁZIS

| Fázis | Tartalom |
|-------|----------|
| 1 | PRIMARY DATA: M1 + London/NYC sessions |
| 2 | MULTI-TIMEFRAME: M1/M5/M15/H1 |
| 3 | FEATURES: 20-25 (pivot, trend, momentum, volatility, volume, regime) |
| 4 | SCALPING IDABLAK: Long ≤1.5h, Short ≤50 perc |
| 5 | DYNAMIC DOLLAR BAR: $80K XAUUSD, EMA-based |
| 6 | GYŰJTŐ SCRIPT: MT5 független |
| 7 | TRIPLE BARRIER: ATR-alapú, anti-overlabeling |
| 8 | DUAL/MULTI SYSTEM: LGBM+MLP stacking ensemble (távoli jövő) |
| 9 | WALK-FORWARD CV: Purged k-fold CV |
| 10 | ÉLES BACKEND: Unified thresholds |
| 11 | LIVE BACKEND: TCP 5555/5556 + ZMQ PUB 5557 |
| 12 | PLAYBACK TESZTELÉS: Multi-day CSV |

---

## JULES RENDSZER KRITIKAI HIBÁI (MIBŐL TANULUNK)

1. **ZigZag repainting leakage** — offline címkézés repainting ZigZag-ot használt
2. **Feature mismatch** — 29 feature tanítva, 10 eval (ellentmondás)
3. **Fixed vs ATR barrier mismatch** — tanítás fixed barriers, éles ATR
4. **Dollar Bar threshold túl magas** — $444K helyett $80K XAUUSD-nél
5. **Max bars túl hosszú** — nem scalper-specifikus

## ÚJ RENDSZER ELŐNYEI

- ✅ Real-time ZigZag (Merkava EA-ból, nem offline repaint)
- ✅ Feature konzisztencia (training=eval=live)
- ✅ ATR-alapú dynamic barriers (nem fixed)
- ✅ $80K Dollar Bar threshold (scalper-specifikus)
- ✅ Max bars ≤1.5h (long), ≤50 perc (short)
- ✅ LGBM+MLP stacking ensemble (multi-system, távoli jövő)
- ✅ Purged k-fold CV (anti-leakage)

ema_volume = df['dollar_volume'].rolling(100).mean()
threshold = ema_volume * 1.5  # 1.5× a 100-perces EMA volumen

# Per-instrument calibration
INSTRUMENT_THRESHOLDS = {
    'XAUUSD': 80000,
    'GBPUSD': 30000,
    'ES_F': 250000,
}
```

---

## 📊 FÁZIS 6: GYŰJTŐ SCRIPT (MQL5 CSV)

- **AI_Data_Collector_v10.0.mq5** — MT5 független gyűjtő script
- Merkava EA-ból veszi a hibrid indikátorokat (NavSystem)
- MT5-ben kiszámítja a feature-öket
- ATR-alapú TP/SL (dynamic!)
- CSV oszlopok: tick_time, bid, ask, zigzag_high/low, dist_to_zigzag, ema_slopes, macd, wpr, stoch_k, atr, atr_tp, atr_sl, max_bars, target_label

### A. PIVOT SZINTEK (3) — Merkava EA-ból:
- Dist_Micro_R/S (Micro pivot távolság — 3 depth, 5 dev, 3 back)
- Dist_Sec_R/S (Secondary pivot távolság — 4 depth, 5 dev, 3 back)
- Dist_Ter_R/S (Tertiary pivot távolság — 7 depth, 5 dev, 3 back)

### B. TREND INDIKÁTOROK (4-6):
- EMA_10_Slope, EMA_25_Slope (TrendFast), EMA_50_Slope (TrendMedium)
- EMA_150_Slope (TrendSlow), EMA_300_Slope (TrendSuper), ADX

### C. MOMENTUM INDIKÁTOROK (3-5):
- RSI, MACD, WPR, Stochastic, ROC

### D. VOLATILITÁS INDIKÁTOROK (3-4):
- ATR, Bollinger Bands Z, Keltner Channels, Price_Velocity

### E. VOLUME INDIKÁTOROK (3-4):
- OBI_ZScore (shift(1).rolling(100)), CVD, VWAP, Total_Volume

### F. HMM REGIME INDIKÁTOROK (2-3):
- HMM_State (GaussianHMM: trend vs range vs breakout)
- MarkovChain_Probabilities, Regime_Confidence (>0.6 = high)
