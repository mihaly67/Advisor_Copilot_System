# Direction Features — Code Digest

## Dátum: 2026-10-12
## Kontextus: BTCUSD dollar bars, OHLC+volume only (no footprint)

---

## PROBLÉMA: OHLC features CANNOT predict direction

Bebizonyosodott (AUC≈0.53):
- OHLC ráták (O/C, H/C, L/C)
- RSI, StochasticK
- ADX, ATR
- Bollinger szélesség

Ezek **magnitude** információt hordoznak, nem **direction**-t.

---

## MEGOLDÁS: Direction-carrying features

### 1. DF_Curve (CUSUM Direction) — PRIORITÁS 1

**NavSystem eredet**: CUSUM filter sign komponens
**Python proxy**:
```python
def compute_df_curve(close, h=0.05):
    """
    CUSUM direction filter.
    h = threshold (5% of daily vol tipikus)
    Returns: +1 (bull), -1 (bear), vagy folytonos CUSUM érték
    """
    returns = close.pct_change()
    vol = returns.ewm(span=20).std()
    h_val = h * vol
    
    # CUSUM positive (bull) és negative (bear)累计
    s_pos = 0.0
    s_neg = 0.0
    df_curve = pd.Series(index=close.index, dtype=float)
    
    for i in range(1, len(close)):
        s_pos = max(0, s_pos + returns.iloc[i] - h_val.iloc[i])
        s_neg = min(0, s_neg + returns.iloc[i] + h_val.iloc[i])
        df_curve.iloc[i] = s_pos + s_neg  # Net CUSUM = direction
    
    return df_curve
```

**Miért működik**: A CUSUM kumulatív deviációt mér — ha a price szisztematikusan felfelé tér el, s_pos nő. Ez **trend direction** információ, nem csak magnitude.

---

### 2. Flow_Delta (Volume × Close Position) — PRIORITÁS 2

**NavSystem eredet**: Volume flow indicator
**Python proxy**:
```python
def compute_flow_delta(close, high, low, volume):
    """
    Order flow proxy based on close position within bar range.
    close_position = 1.0 → close at high → buying pressure
    close_position = 0.0 → close at low → selling pressure
    """
    close_position = (close - low) / (high - low + 1e-10)
    flow_delta = volume * (close_position - 0.5) * 2  # [-volume, +volume]
    return flow_delta
```

**Miért működik**: Ha a close a high közelében van és nagy volume → buying pressure. Ez **order flow** információ OHLCV-ből proxizálva.

---

### 3. Price-Volume Correlation — PRIORITÁS 4

```python
def compute_pv_correlation(close, volume, window=20):
    """
    Rolling correlation between price changes and volume.
    Positive → volume confirms direction (trend)
    Negative → volume diverges (reversal)
    """
    price_change = close.pct_change()
    vol_change = volume.pct_change()
    pv_corr = price_change.rolling(window).corr(vol_change)
    return pv_corr
```

---

### 4. Momentum Persistence — PRIORITÁS 5

```python
def compute_momentum_persistence(close, window=20):
    """
    Fraction of consecutive same-sign returns.
    High persistence → trending market (direction continues)
    Low persistence → choppy market (direction unreliable)
    """
    returns = close.pct_change()
    sign_same = (np.sign(returns) == np.sign(returns.shift(1))).astype(int)
    persistence = sign_same.rolling(window).mean()
    return persistence
```

---

### 5. Volatility-Adjusted Momentum — PRIORITÁS 6

```python
def compute_vol_adj_momentum(close, window=20):
    """
    Momentum normalized by volatility → risk-adjusted direction signal.
    High positive → strong uptrend relative to noise
    High negative → strong downtrend relative to noise
    """
    momentum = close / close.shift(window) - 1
    vol = close.pct_change().rolling(window).std()
    vol_adj_mom = momentum / (vol + 1e-10)
    return vol_adj_mom
```

---

### 6. Variance Ratio 1:4 — PRIORITÁS 7

```python
def compute_variance_ratio(close, lag=4):
    """
    VR(1,lag) = var(r_lag) / (lag × var(r_1))
    VR > 1 → positive autocorrelation → trending → direction exists
    VR < 1 → negative autocorrelation → mean-reverting → fade
    VR ≈ 1 → random walk → no direction signal
    """
    r1 = close.pct_change()
    r_lag = close.pct_change(lag)
    var_r1 = r1.rolling(20*lag).var()
    var_r_lag = r_lag.rolling(20*lag).var()
    vr = var_r_lag / (lag * var_r1 + 1e-10)
    return vr
```

---

## INTEGRÁCIÓS SORREND

1. **DF_Curve** → a legerősebb direction feature (CUSUM sign)
2. **Flow_Delta** → volume flow proxy
3. **PV_Correlation** → volume confirmation
4. **Momentum_Persistence** → trend vs choppy
5. **Vol_Adj_Momentum** → risk-adjusted direction
6. **Variance_Ratio** → does direction even exist?

## VÁRHATÓ EREDMÉNY
- OHLC-only AUC ≈ 0.53 (baseline)
- +DF_Curve → AUC ≈ 0.56-0.58 (CUSUM direction info)
- +Flow_Delta → AUC ≈ 0.58-0.61 (order flow proxy)
- +összes → AUC ≈ 0.60-0.65 (ha minden jól megy)
