# Fractional Differentiation — Code Digest

## Dátum: 2026-10-12
## Forrás: financial-ml-toolkit/pipeline/feature_engineering.py

---

## PROBLÉMA

- d=0 (no diff): Series nem stationáris → ML tanul trend-et, nem mintát → overfit
- d=1 (full diff): Stationáris DE memória megsemmisül → feature-ek nem emlékeznek trend-re
- **Megoldás**: 0 < d < 1 → stationáris ÉS memória megmarad!

---

## FIXED-WIDTH WINDOW FFD

```python
def get_weights_ffd(d, threshold=1e-5, max_size=10000):
    """Calculate weights for fractional differentiation.
    Formula: w_k = -w_{k-1} * (d - k + 1) / k
    Stop when |w_k| < threshold (weights converge to 0)
    """
    weights = [1.0]
    k = 1
    while abs(weights[-1]) >= threshold and k < max_size:
        w_k = -weights[-1] * (d - k + 1) / k
        weights.append(w_k)
        k += 1
    return np.array(weights)
```

### Weight decay példák:
- d=0.5: w = [1.0, -0.5, -0.125, -0.0625, ...] → lassan csökken
- d=1.0: w = [1.0, -1.0] → ez a standard differencia!
- d=0.0: w = [1.0] → nincs differencia

---

## FFD APPLICATION

```python
def frac_diff_ffd(series, d, threshold=1e-5):
    """Apply fractional differentiation with fixed-width window."""
    weights = get_weights_ffd(d, threshold)
    width = len(weights)
    
    result = pd.Series(index=series.index, dtype=float)
    for i in range(width, len(series)):
        result.iloc[i] = np.dot(weights[::-1], series.iloc[i-width+1:i+1])
    
    return result
```

---

## MINIMUM d SEARCH

```python
def find_min_d(close, d_range=(0.0, 1.0), step=0.05):
    """Find minimum d where ADF test rejects H0 (series is stationary)."""
    from statsmodels.tsa.stattools import adfuller
    
    for d in np.arange(d_range[0], d_range[1] + step, step):
        diff_series = frac_diff_ffd(close, d)
        diff_series = diff_series.dropna()
        
        if len(diff_series) < 100:
            continue
        
        adf_stat, p_value, _, _, _, _ = adfuller(diff_series)
        
        if p_value < 0.05:  # Stationary!
            return d
    
    return d_range[1]  # Fallback: full differencing
```

### BTCUSD dollar bar result várható:
- **d ≈ 0.35-0.45** → stationáris ÉS memória megmarad
- d=1.0 → log return → stationáris de sok memória elveszik
- d=0.0 → raw price → nem stationáris → overfit

---

## INTEGRÁCIÓS PIPELINE

```python
# 1. Find optimal d
d_opt = find_min_d(close, d_range=(0.0, 1.0), step=0.05)

# 2. Apply to feature columns
for col in feature_cols:
    features[f'ffd_{col}'] = frac_diff_ffd(features[col], d=d_opt)

# 3. Use BOTH raw and FFD features
# Raw: interpretálható, domain knowledge
# FFD: stationáris, ML-ready
```

---

## KULCS FELISMERÉS

**Fractional differentiation = feature transzformáció, NEM címkézés!**
- Alkalmazd a feature-ekre, nem a label-ekre
- Célja: stationáris input az ML modelnek
- A memória megőrzése azt jelenti, hogy a model "látja" a trend kontextust
- **d=0.4 feature + direction features + TBM label → teljes pipeline**
