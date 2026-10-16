# Szint 2: Feature Engineering, Sample Weights, End-to-End Pipeline

**Dátum:** 2026-10-09

---

## 1. AlphaPy Boolean Transforms (tree-model életmentők!)

A `alphapy/transforms.py`-ban:

| Függvény | Kód | Típus | Jelentés |
|---|---|---|---|
| `abovema(f, c, p)` | `f[c] > MA(f[c], p)` | **bool** | Ár MA felett |
| `belowma(f, c, p)` | `f[c] < MA(f[c], p)` | **bool** | Ár MA alatt |
| `higher(f, c, o)` | `f[c] > f[c].shift(o)` | **bool** | Nőtt az előző o-barhoz képest |
| `lower(f, c, o)` | `f[c] < f[c].shift(o)` | **bool** | Csökkent az előző o-barhoz képest |

**MIÉRT FONTOS:** A LightGBM fa alapú. Egy `Dist_Micro_S=1.5` csak szám — a fa nem tudja,
hogy "support felett = bullish". De `Above_Support=True` egy tiszta boolean split —
a fa azonnal megérti: True esetén bullish, False esetén bearish.

**XAUUSD CFD boolean feature-k (amik kellenek):**
```python
above_ema20 = close > EMA(close, 20)
above_ema50 = close > EMA(close, 50)
above_sma200 = close > SMA(close, 200)
rsi_oversold = RSI(14) < 30
rsi_overbought = RSI(14) > 70
stoch_oversold = StochK < 20
stoch_overbought = StochK > 80
macd_bullish = MACD > MACD_signal
macd_bearish = MACD < MACD_signal
cusum_up = CUSUM_s_pos > 0  # CUSUM up event aktív
cusum_down = CUSUM_s_neg < 0  # CUSUM down event aktív
price_higher_1 = close > close.shift(1)  # zöld bar
price_lower_1 = close < close.shift(1)  # piros bar
trend_up = Slope_Close_14 > 0
trend_down = Slope_Close_14 < 0
```

---

## 2. meta-labeling-alpha-filter Feature Engineering (valós rendszer!)

A `src/features.py`-ban használt feature-k (30 likvid US szimbólum, napi bar):

### Ár/Return
- `price_percentile_63d` = (price - min63) / (max63 - min63)
- `dist_52w` = (price - min252) / (max252 - min252)
- `volatility_63d`, `volatility_21d`, `volatility_zscore`

### Momentum
- `momentum_63d`, `momentum_21d`, `vol_adj_momentum` = mom/vol
- `mom_persistence` = (returns > 0).rolling(63).mean()
- `mom_12m_1m` = 12M momentum - 1M momentum (cross-sectional)

### Kockázat
- `mdd_63` = price / rolling_max - 1 (max drawdown)
- `dsv_63` = downside variance (negatív return-ök négyzete)
- `es95_63` = Expected Shortfall 95% (CVaR)
- `dd_speed_21` = drawdown sebesség

### Trend Minőség
- `slope_63`, `r2_63` = rolling OLS slope és R²
- **`trend_strength_63` = slope × R²** — ERŐS trend = nagy slope ÉS jó fit
- `vol_trend_63` = volatilitás trendje

### Idő extremumoktól
- `time_from_high_63`, `time_from_low_63`
- `time_from_high_252`, `time_from_low_252`

### Makro
- `vix`, **`vix_high = (vix > 25).astype(int)`** — BOOLEAN!
- `ten_year`, `ten_year_minus` (yield curve)
- **`inversion = (T10Y3M < 0).astype(int)`** — BOOLEAN! Yield inversion

### Beta/Korreláció
- `beta_63d` = rolling cov/var (market beta)
- `corr_spy_63d` = rolling correlation
- `beta_instability_63` = beta_21 rolling std

### Naptár
- `month_of_year_sin`, **`is_month_end`**, **`is_month_start`** — BOOLEAN!

### Volumen
- `volume_surge` = volume / volume.rolling(63).mean()

### Ferdeség/Likviditás
- `return_skew_21d`, `return_skew_63d`, `volume_skew_21d`
- `amihud_illiquidity` = log(|return| / volume).rolling(63).mean()

### TA indikátorok (ta könyvtár)
RSI, TRIX, MACD, ADX, CCI, SMA, EMA, KAMA, Stoch, WilliamsR, OBV, VWAP, CMF, ADI, ATR

---

## 3. FreqAI End-to-End (freqtrade)

### data_kitchen.py
- `training_features_list`, `label_list` — feature/label nyilvántartás
- `train_period_days`, `backtest_period_days` — walk-forward ablakok
- `feature_pipeline`, `label_pipeline` — Pipeline objektumok (datasieve)
- Train/test split sklearn-lel

### LightGBMClassifier.py
```python
model = LGBMClassifier(**self.model_training_parameters)
model.fit(
    X=data_dictionary["train_features"].to_numpy(),
    y=data_dictionary["train_labels"].to_numpy()[:, 0],
    sample_weight=train_weights,      # SÚLYOK!
    eval_set=[(test_features, test_labels)],
    eval_sample_weight=[test_weights],
)
```

**KULCS:** `sample_weight` — FreqAI használja! Ez a sample uniqueness weight.

---

## 4. Sample Weights (AFML Chapter 4)

A `financial-ml-toolkit/pipeline/sample_weights.py`-ban:

### `get_indicator_matrix(bar_index, t1)`
- Bináris mátrix: mely bar-ok hatnak melyik label-re
- Ha triple barrier [t0, t1] intervallum, minden bar ebben hat

### `get_num_concurrent_labels(close, t1)`
- Minden időpontra: hány label hat rá (overlap)
- Magas concurrency = sok overlap = kevés uniq információ

### `get_average_uniqueness(t1, close)`
- `uniqueness = 1 / concurrent`
- Átlag uniqueness a label élettartama alatt
- **Magas uniqueness = ritka, informatív label**
- **Alacsony uniqueness = gyakori, overlap-ping label**

### `sequential_bootstrap(ind_matrix, sample_length)`
- Nem-IID sampling: csökkenti a valószínűségét overlap-ping minták húzásának
- AFML Snippet 4.5

### MIÉRT KELL?
- Triple barrier label-ek NEM IID-k! Egy bar több label-re is hat
- Ha nem weight-elünk, az overlapping label-ek dominálják a gradienst
- `sample_weight = average_uniqueness` — ez korrigálja

---

## 5. Összefoglaló: Ami kell a XAUUSD CFD pipeline-hez

### Feature Engineering (input a modellbe)
1. **Boolean feature-k** (AlphaPy stílus): Above_EMA20, RSI_Oversold, CUSUM_Up, Trend_Up
2. **Scale-free feature-k** (meta-labeling-harness stílus): f_ret_1/5/10, f_sma20_gap, f_rsi_14, f_atr_pct
3. **Trend minőség**: slope × R² (trend_strength)
4. **Kockázat**: ATR%, vol_ratio, mdd
5. **Kontextus-kombinációk**: Fade_Short_Setup, Bounce_Long_Setup, Breakout

### Labeling (output amit a modell tanul)
1. **Primary model** → side = +1 (Long) vagy -1 (Short)
2. **Triple barrier (side-aware)**:
   - Long: PT = entry + profit_mult × ATR, SL = entry - stop_mult × ATR
   - Short: PT = entry - profit_mult × ATR, SL = entry + stop_mult × ATR
   - MAX_BARS = 15-30 (idő barrier)
3. **Meta-label**: 1 = take (TP hit), 0 = skip (SL hit vagy timeout)

### Training
1. **Sample weights** = average_uniqueness (concurrency correction)
2. **scale_pos_weight** = neg/pos (class balance)
3. **LGBM GPU** (P4000): device='gpu'

### Validáció
1. **Purged + embargoed walk-forward** (3-5 nap embargo)
2. **Beta benchmark** (buy-and-hold)
3. **Profit objective** (NEM accuracy!)
4. **Coverage floor** (minimum 5% jelet vesz)
