# ML Tudásbázis: Cimkézés, Adatmérnökség, Feature Mérnökség

## Dátum: 2026-10-12
## Források: finmlkit, meta-labeling-alpha-filter, triple_barrier, Financial-Time-Series-Trend-Labeling, LGBM-Stock-Prediction, LightGBM-Quant-Model

---

# 1. CIMKÉZÉS (LABELING)

## 1.1 Triple Barrier Method (TBM) — AFM Ch.3

### Alapkoncept
Három barrier egy esemény nyitóára körül:
- **Felső barrier (TP)**: `P₀ × (1 + target_ret × m_up)` — Take Profit
- **Alsó barrier (SL)**: `P₀ × (1 - target_ret × m_low)` — Stop Loss  
- **Vertikális barrier**: Időkorlát (t₀ + Δt) — Timeout

### Label meghatározás
- **+1**: Felső barrier érintve először → nyereség
- **-1**: Alsó barrier érintve először → veszteség
- **0**: Vertikális barrier érintve → timeout

### Két mód: Side vs Meta-labeling
1. **Side labeling** (is_meta=False): Label = sign(ret) → +1 vagy -1
   - Ez PREDIKCIÓ a trend irányára
   - Szimmetrikus barrier-ekkel (m_up = m_low)
2. **Meta-labeling** (is_meta=True): Side megadva (+1/-1), label = 1 ha ret≥min_ret, else 0
   - Ez a PRIMARY model irányát ELFOGADJA vagy ELUTASÍTJA
   - Binary: "should we trade?" nem "which direction?"

### finmlkit tbm.py implementáció (Numba, párhuzamos)
```python
# Log-return térben:
upper_barrier = target * top_mult
lower_barrier = -target * bottom_mult

# Path kiértékelés:
for j in range(t0_idx + 1, t1_idx + 1):
    ret = (log_close[j] - base_price) * side_mult  # side: +1 buy, -1 sell
    if ret >= upper_barrier: touch_idx = j; break  # TP hit
    if ret <= lower_barrier: touch_idx = j; break  # SL hit

# Label:
if is_meta:
    labels[i] = 1 if ret >= min_ret else 0
else:
    labels[i] = sign(ret) if sign(ret) != 0 else 1
```

### KULCS: target (volatility) = dinamikus barrier szélesség
- `target` = EWMA std-dev of returns → ADAPTÍV barrier
- Volatilis piacban szélesebb barrier, nyugodt piacban szűkebb
- Ez a legfontosabb inzight: **fix TP/SL pip = rossz, volatility-adjusted = jó**

### meta-labeling-alpha-filter implementáció
- `apply_triple_barrier_ref()`: Loop-alapú, lassabb
- `apply_triple_barrier()`: Vectorized pandas
- **Side-aware TP/SL**:
  ```python
  if side == 1:  # Long
      tp_level = entry_price * (1 + tp_factor * vol)
      sl_level = entry_price * (1 - sl_factor * vol)
  else:  # Short
      tp_level = entry_price * (1 - tp_factor * vol)  
      sl_level = entry_price * (1 + sl_factor * vol)
  ```
- **Label**: {1=TP hit, -1=SL hit, 0=timeout}
- **Scanning**: `scan_tp_sl_range()` — TP/SL rácskeresés label eloszlás + entrópia alapján
- **Label map**: `{-1: 0, 0: 1, 1: 2}` → 3-osztályos multiclass

### triple_barrier-main (OOP implementáció)
- `Labeler` class: OHLC + Orders → OrderBoxHits
- `TakeProfit`, `StopLoss`, `TimeBarrier`, `DynamicOrder` külön osztályok
- `TradeSide.BUY = 1`, `TradeSide.SELL = -1`
- **Pip-alapú**: `tp = open_price + trade_side.value * tp_width * 10^(-pip_decimal_position)`
- **Dynamic barrier**: exit_signals Series alapján → bármilyen feltétel lehet kilépés

---

## 1.2 Trend Labeling (Wu et al. 2020)

### Alapkoncept
Paraméter: `w` (pl. 0.1 = 10%)
- Ha ár emelkedik > w a lokális mélyponttól → uptrend (+1)
- Ha ár esik > w a lokális csúcstól → downtrend (-1)

### Algoritmus (auto_labeling)
```python
# Init: FP = első ár, Cid = 0 (irány)
# Első mozgás: átlép w*FP küszöböt → Cid = +1 vagy -1

# Fő ciklus:
if Cid > 0:  # uptrend-ben
    x_H = max(x_H, current_price)  # frissít csúcs
    if price < x_H - x_H * w and LT < HT:  # w%-ot esett csúcstól
        # Minden bar HT és LT között → label = +1
        Cid = -1  # vált downtrend-re
if Cid < 0:  # downtrend-ben
    x_L = min(x_L, current_price)  # frissít mélypont
    if price > x_L + x_L * w and HT <= LT:  # w%-ot emelkedett mélyponttól
        # Minden bar HT és LT között → label = -1
        Cid = 1  # vált uptrend-re
```

### Fő jellemzők
- **Minden bar címkézett**: nincs "no trend" kategória
- **Irány-tudatos**: +1 = bull, -1 = bear — PONT EZ KELL NEKÜNK!
- **w paraméter sensitivity**: kisebb w = finomabb trend, nagyobb w = makro trend
- **Hátrány**: csak close-ot használ, nem OHLC; nincs időkorlát

---

## 1.3 CUSUM Filter (AFM Snippet 2.4)

### Symmetric CUSUM — ESEMÉNY DETEKCIÓ
```python
s_pos = max(0, s_pos + log_return)
s_neg = min(0, s_neg + log_return)

if s_neg < -threshold:  # alsó küszöb átlépve
    s_neg = 0; event!
elif s_pos > threshold:   # felső küszöb átlépve
    s_pos = 0; event!
```

### Kulcs: ez NEM címkézés, hanem MINTAVÉTEL
- Csak azokat a pontokat jelöli meg, ahol "valami történt"
- Ezek lesznek a TBM event_indx-ek
- Threshold = volatility → adaptív mintavétel

### NavSystem DF_Curve → CUSUM-alapú irány!
- `m_val_dfcurve`: diff > 0 → bull, diff < 0 → bear
- Ez CUSUM filter irány-komponense!

---

## 1.4 Sample Weights (AFM Ch.4)

### Average Uniqueness
- Overlapping label-ek súlyozása
- `weight[i] = mean(1 / concurrency[t] for t in event[i]:touch[i])`
- concurrency[t] = hány label fedi az időpontot

### Return Attribution
- `weight[i] = |Σ log_ret[t] / concurrency[t]|` az event intervallumon
- Nagyobb hozamú label = nagyobb súly

### Time Decay
- `last_weight ∈ [-1, 1]` → legújabb = 1.0, legrégebbi = last_weight
- Ha negatív: a legrégebbi adat ELDOBJA (0 súly)

### Class Balance Weights
- `class_weight[c] = total_weights / (n_classes × sum_weights_class_c)`
- Egyensúlyozza a label eloszlást

### Vertical Touch Weights
- Ha vertikális barrier érintve, de közel volt TP/SL → ne büntessük
- `max_rb_ratio`: mennyire volt közel a path egy barrier-hez

---

## 1.5 Labeling Döntési Fa (MIHEZ?)

```
Van-e irány predikció? 
├── NEM → Side labeling (TBM, sign(ret)) → +1/-1
│   └── Szimmetrikus barrier, target=volatility
└── IGEN → Meta-labeling 
    ├── Primary model: irány döntés (+1/-1)
    └── Meta model: "kereskedjünk-e?" (0/1)
        └── Aszimmetrikus TP/SL, side-aware
```

### BTCUSD Dollar Bar esetünkre:
- **Jelenlegi**: Long/Short model = meta-labeling (AUC=0.615) de NEM irány-tudatos
- **Kell**: 
  1. Side model: trend irány → +1/-1 (TBM side labeling VAGY trend labeling)
  2. Meta model: "kereskedjünk-e a predicted side-on?" → 0/1
  3. Direction rule: NO TRADE against predicted direction

---

# 2. ADATMÉRNÖKSÉG (DATA ENGINEERING)

## 2.1 Bar Construction (finmlkit/bar/)

### Dollar Bars
- Threshold alapú: Σ(volume × price) ≥ threshold → új bar
- Előny: volatilitás-adaptív, kevesebb mikroszerkezet zaj
- finmlkit implementálja: `bar/base.py` (36K), `bar/data_model.py` (51K)

### FootprintData
- Bar-on belüli tick szintű adat: buy_volume, sell_volume price_level-önként
- Volume Profile számításhoz kell
- **VPIN**: Volume-synchronized Probability of Informed Trading

## 2.2 Sampling / Event Detection

### CUSUM Filter (sampling/filters.py)
- Esemény-időpontok detekciója → ezek lesznek a TBM bemenetek
- Nem minden bar → csak a "szignifikáns" változások
- Threshold = dinamikus (pl. EWMA volatility)

### Z-Score Peak Filter (nem implementált)
- Outlier események detekciója rolling z-score alapján

## 2.3 Data Pipeline (meta-labeling)

### Teljes pipeline:
1. Price data letöltés (yfinance)
2. S&P500 PIT szűrés (point-in-time komponens szűrés)
3. Monthly momentum → daily signals (strategy.py)
4. Triple barrier labeling → Y labels
5. Feature engineering → X features
6. Model training → meta-model
7. Signal filtering → filtered_signals
8. Position sizing → executed weights + P&L

---

# 3. FEATURE MÉRNÖKSÉG (FEATURE ENGINEERING)

## 3.1 finmlkit Feature System (legteljesebb)

### Arhitektúra
- `Feature` class: fluent interface, operátor overloading
  - `price / sma20` → automatikus composíció
  - `feature.rolling(20).mean()` → chain-elt transzformáció
- `BaseTransform` → `SISOTransform`, `MISOTransform`, `SIMOTransform`
- Pandas és Numba backend (auto-fallback)

### Transzformációk (transforms.py, 67K)

#### Price/Return
- `Identity`, `Lag`, `ReturnT` (idő-ablakos return, irregular TS!), `PctChange`
- `LogReturn`, `CumReturn`

#### Volatility
- `EWMST`: EWMA std-dev (adjust=True, bias=False)
- `RealizedVol`: √(Σ ret²) rolling ablakban
- `Bollinger%B`: (price - SMA) / (2 × σ)
- `ParkinsonRange`: √(2/π × ln(H/L)) — hatékonyabb vol. estimator
- `ATR`: Average True Range
- `VarianceRatio14`: var(1-bar) / var(4-bar) — trending vs mean-reversion detekció

#### Momentum
- `ROC`: Rate of Change
- `RSI` (Wilder's smoothing)
- `StochK`: Stochastic %K
- `CusumTestRolling`: Strukturális törés detekció

#### Volume/Flow
- **VPIN**: Volume-synchronized Probability of Informed Trading
  - `|Σ(V_buy - V_sell)| / Σ(V_buy + V_sell)` rolling ablakban
  - **KULCS INZIGHT**: VPIN > 0.5 → informed trading → trend folytatódik
- **FlowAcceleration**: `log(recent_volume_sum / past_volume_sum)`
  - Volume gyorsulás = flow belépés
- **VolumeProfile**: POC, HVA, LVA árak rolling ablakban
  - POC = Point of Control (legtöbb volume ár)
  - HVA/LVA = High/Low Value Area (68.3% volume tartomány)
  - **KULCS**: POC feletti volume % → irány-tudatos feature!

#### Trend
- `ADX`: Average Directional Index (trend erősség, NEM irány)
  - +DI, -DI → DX → ADX (Wilder's smoothing)

#### Correlation
- `RollingPriceVolumeCorrelation`: ár return vs volume korreláció
  - Pozitív = volume ár-emelkedéssel → buying pressure
  - Negatív = volume ár-eséssel → selling pressure
  - **KULCS INZIGHT**: Ez irány-információt hordoz!

#### Structural Break
- `CusumTestRolling`: CUSUM strukturális törés teszt

#### Time
- `TimeCues`: hét napja, hónap napja, stb. szinuszos kódolás

---

## 3.2 meta-labeling Feature Engineering (features.py)

### Feature kategóriák (50+ feature):

#### Core Price/Return
- `price_percentile` (63-day rolling), `dist_52w` (52-week high/low távolság)
- `volatility_63d`, `volatility_21d`, `volatility_zscore`
- `vov_63` (vol-of-vol)

#### Momentum
- `momentum_63d`, `momentum_21d`, `momentum_63_21d` (acceleration)
- `vol_adj_momentum` = momentum / volatility → **kockázat-korrigált momentum**
- `mom_persistence` = % pozitív return 63 napon → **trend kitartás**
- `mom_12m_1m` (12M - 1M momentum = értékelési momentum)

#### Risk/Downside
- `mdd_63` (max drawdown 63 nap)
- `dsv_63` (downside variance)
- `es95_63` (Expected Shortfall 95%)
- `dd_speed_21` (drawdown sebesség)

#### Technical Indicators (`ta` library)
- RSI, MACD, OBV, ATR, BBands, ADX, CCI, Williams%R, MFI, Stoch, TSI, Force Index

#### Volume
- `amihud_illiquidity` = |return| / volume
- `volume_surge` = volume / volume.rolling(63).mean()

#### Cross-Sectional (cs_rank, cs_zscore)
- `cs_rank_mom21d`, `cs_rank_mom63d`, `cs_rank_price_percentile`
- `cs_z_volatility`, `cs_z_beta`, `cs_z_corr_spy`, `cs_z_rsi`, `cs_z_obv`

#### Market/Regime
- `corr_spy_63d`, `beta_63d`, `beta_instability_63`
- `vix`, `10yTbill`, `yield_curve_slope`, `yc_inversion`
- `bollinger_zscore` (price vs 63d BBands)

#### Skewness
- `return_skew_21d`, `return_skew_63d`, `volume_skew_21d`

### Post-processing
1. Drop rows with ≥10% NaN
2. Forward fill (limit=10) + backward fill
3. Median fill remaining NaN
4. **Correlation pruning**: drop features with corr > 0.95
5. Explicit drops: `is_month_start`, `is_month_end`, `yc_inversion`

---

## 3.3 LGBM-Stock-Prediction Feature Engineering

### Feature típusok:
- **Momentum Score**: `annualized_slope × R²` (log-price regresszió)
  - **KULCS**: slope × R² → erős + konzisztens trend = magas score
- **Past returns**: 1,2,3,4,5,10 napos (simple és log)
- **Future returns (labels)**: 1,2,3,4,5,10 napos
- **RSI** (Wilder's 14)

---

## 3.4 LightGBM-Quant-Model Features

### Feature típusok:
- `close_open_ratio` = |close/open| — gap detekció
- `rolling_average_close_mean/std` — trend és vol
- `rolling_average_vol_mean/std` — volume szint
- `moving_average_7_day` — rövid MA
- `ewma` (span=30) — exponenciális MA
- `sharpe` — risk-adjusted return
- `bollinger_bands` — vol. envelope
- `force_index` — price × volume momentum
- `true_strength_index` — double-smoothed momentum
- TF-IDF news headline score — **szöveges feature!**

---

# 4. IRÁNY-TUDATOS FEATURE-K (DIRECTION FEATURES) — KULCS SZÁMUNKRA

## 4.1 Milyen feature-k hordozhatnak irány-információt?

### ✅ IGAZÁN IRÁNY-TUDATOS (flow/microstruktúra)
1. **VPIN** (finmlkit): Volume-synchronized Probability of Informed Trading
   - Nagy VPIN → informed flow → irány folytatódik
   - SZÜKSÉG: volume_buy és volume_sell (footprint adat)
2. **Flow Acceleration** (finmlkit): Volume gyorsulás
   - `log(recent_vol / past_vol)` → flow belépés detekció
3. **Price-Volume Correlation** (finmlkit): Rolling corr(price_return, volume)
   - Pozitív = buying pressure, Negatív = selling pressure
4. **Volume Profile POC** (finmlkit): Point of Control ár
   - POC felett = bull, POC alatt = bear (support/resistance)
5. **OBV** (On-Balance Volume): Akkumulált signed volume
6. **Force Index** (price_change × volume): Irány × erő

### ⚠️ KÖZVETETT IRÁNY-INFORMÁCIÓ
7. **RSI / StochK**: Overbought/oversold → revertálás irány
8. **MACD**: Trend + momentum irány
9. **Momentum persistence** (% pozitív return): Trend kitartás
10. **Bollinger %B**: Hol az ár a band-en belül
11. **Beta/Corr_SPY**: Relatív erősség vs piac
12. **Variance Ratio 1:4**: Trending (>0.25) vs mean-reversion (<0.25)

### ❌ NEM IRÁNY-TUDATOS (csak volatilitás/magnitúdó)
13. ADX (trend ERŐSSÉG, nem irány)
14. ATR, Parkinson Range, Realized Vol (volatilitás)
15. Vol-of-Vol (volatilitás volatilitása)
16. Amihud Illiquidity (likviditás)

## 4.2 BTCUSD Dollar Bar Specifikus

### Amink VAN:
- OHLC (open, high, low, close)
- Volume (dollar volume)
- Tick_Imbalance (bar-on belüli tick irányegyensúly)
- NavSystem DF_Curve (CUSUM irány) — MQL5-ből
- NavSystem Flow_Delta (volume × close_position pressure) — MQL5-ből

### Amink KELL (proxy-kkal):
1. **DF_Curve Python proxy**: CUSUM filter sign → bull/bear
   - Implementáció: s_pos = max(0, s_pos+ret), s_neg = min(0, s_neg+ret)
   - Direction = sign(s_pos) if s_pos > threshold else sign(s_neg) if s_neg < -threshold
2. **Flow_Delta Python proxy**: volume × (close_position - 0.5) × 2
   - close_position = (close - low) / (high - low)  [0,1]
   - Pozitív = buying pressure, Negatív = selling pressure
3. **Price-Volume Correlation**: rolling corr(pct_change, volume) — NEM kell footprint
4. **Momentum Persistence**: (returns > 0).rolling(20).mean() — trend kitartás
5. **Vol-Adj Momentum**: momentum / volatility — kockázat-korrigált irány
6. **Variance Ratio 1:4**: trending vs mean-reversion detekció

### Amink NEM lesz (footprint hiány):
- VPIN (volume_buy/sell kell)
- Volume Profile POC (price level volumen kell)

---

# 5. META-LABELING PIPELINE (teljes)

## 5.1 Architecture
```
Primary Model (signal) → Triple Barrier Label → Meta-Model (filter) → Sizing → Execution
```

### Primary Model: strategy.py
- Monthly momentum (12M - 1M) → long/short signal
- Signal = {-1, 0, +1}

### Triple Barrier: labeling.py
- Signal × volatility → TP/SL szintek
- Label = {+1, -1, 0} (TP hit, SL hit, timeout)

### Meta-Model: modeling.py
- Feature X + Label Y → LightGBM multiclass
- Predikció: P(+1), P(0), P(-1)
- Csak a P(+1) > threshold signal-eket tartja

### Signal Filter: signals.py
- Side-aware threshold (hosszú: 0.45, rövid: 0.50 — rövid szigorúbb)
- Min gap: P(+1) - max(P(0), P(-1)) ≥ min_gap
- Top-K per day: legjobb K signal naponként
- Score mode: "prob" | "edge" | "logit_edge"

### Position Sizing: sizing.py
- Prob-weighting: signal × P(+1) VAGY signal × margin VAGY signal × tanh(0.5×logit)
- Vol targeting: scale = target_vol / realized_vol
- Leverage cap
- λ-blend: W[t] = prev + λ × (W_target - prev) → churn csökkentés
- Min trade filter: |Δw| < ε → ne kereskedj
- Cost model: long_tc = 10bps, short_tc = 20bps

---

# 6. KONKRÉT AKCIÓTERV BTCUSD COPILOTHoz

## 6.1 Címkézés javítás
1. **TBM Side Labeling**: TBM szimmetrikus barrier → +1/-1 (nem 0/1!)
   - target = EWMA volatility (adaptív barrier szélesség)
   - Vertikális barrier = max holding period (pl. 20 bar)
2. **TBM Meta-Labeling**: Ha side model megvan → meta-model 0/1
3. **Trend Labeling** (Wu et al.): w=0.5% → +1/-1 (alternatíva)

## 6.2 Feature javítás (irány-tudatos)
1. **DF_Curve proxy** (CUSUM sign) → már van NavSystem-ből, Python implementáció
2. **Flow_Delta proxy** (volume × close_position) → már van NavSystem-ből
3. **Price-Volume Correlation** (rolling corr)
4. **Momentum Persistence** (% pozitív return)
5. **Vol-Adj Momentum** (momentum / vol)
6. **Variance Ratio 1:4** (trending vs MR)
7. **Tick_Imbalance** × volume → flow proxy

## 6.3 Direction Rule
- If predicted_side = +1 → only Long trades allowed
- If predicted_side = -1 → only Short trades allowed
- If meta-model confidence < threshold → no trade

## 6.4 Sample Weights
- Average Uniqueness → overlapping label súlyozás
- Return Attribution → nagy hozamú label prioritás
- Class Balance → label egyensúly
