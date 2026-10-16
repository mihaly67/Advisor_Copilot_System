# ML Tudásbázis Kiegészítés: financial-ml-toolkit mélyelemzés

## Dátum: 2026-10-12

---

# 7. FRACTIONAL DIFFERENTIATION (AFM Ch.5)

## Alapkoncept
- **d=1**: Standard differencia → stationáris DE memória megsemmisül
- **d=0**: Nincs differencia → memória megmarad DE nem stationáris
- **0 < d < 1**: Frakcionális differencia → stationáris ÉS memória megmarad!

## Implementáció (feature_engineering.py)
```python
# Fixed-Width Window FFD
def get_weights_ffd(d, threshold=1e-5):
    weights = [1.0]
    k = 1
    while abs(weights[-1]) >= threshold:
        w_k = -weights[-1] * (d - k + 1) / k
        weights.append(w_k)
        k += 1
    return np.array(weights)

# Min d search: find minimum d where ADF test passes
def find_min_d(close, d_range=(0.0, 1.0), step=0.05):
    for d in np.arange(d_range[0], d_range[1], step):
        diff_series = frac_diff_ffd(close, d)
        if adfuller(diff_series)[1] < 0.05:  # stationáris
            return d
```

## KULCS INZIGHT: BTCUSD dollar bar return-ök → d≈0.4 lehet optimális
- d=1 (log return) → túl sok memória elveszik
- d=0.4 → stationáris ÉS megtartja a trend memóriát
- **Ez feature transzformáció, nem címkézés!**

---

# 8. MICROSTRUCTURE FEATURES (AFM Ch.19+)

## Roll Spread
```python
roll_spread = 2 * sqrt(-autocov(lag=1))  # Ha negatív autocov
```
- Bid-ask spread proxy → likviditás mértéke

## Kyle's Lambda (Price Impact)
```python
# Regresszió: |price_change| = lambda × sqrt(volume) + noise
kyle_lambda = regress(|Δp|, √V)[0]
```
- Nagy lambda → nagy price impact → illikvid
- **INFORMÁCIÓ aszimmetria → informed flow**

## Amihud's Lambda
```python
amihud_lambda = mean(|r| / dollar_volume)
```
- Illikviditás mérték

## CUSUM Feature (strukturális törés)
```python
cusum = get_cusum_filter(close)  # True/False: törés detektálva
```

## Volume Features
- `dollar_volume` = close × volume
- `volume_ma_ratio` = volume / volume.rolling(20).mean() → volume surge

---

# 9. ENTROPY FEATURES

## Shannon Entropy
```python
def get_shannon_entropy(close, window=100):
    # Bin returns → histogram → entropy
    returns = close.pct_change()
    for rolling window:
        hist, _ = np.histogram(returns_window, bins='auto')
        prob = hist / hist.sum()
        entropy = -Σ(p × log(p))
```
- Magas entrópia = random/unpredictable
- Alacsony entrópia = structurált/trend

## Lempel-Ziv Complexity
- Kompreszió arány → komplexitás mérték
- Drága → ritkán használjuk

---

# 10. PURGED K-FOLD CV (AFM Ch.7)

## Probléma: Standard K-Fold → leakage!
- Overlapping label-ek → train és test nem független
- Megoldás: **Purging** — távolítsuk el a train-ből azokat a pontokat, amik overlap-pelnek a test label-ekkel

## PurgedKFold
```python
class PurgedKFold(BaseCrossValidator):
    def split(self, X):
        for train_idx, test_idx in standard_kfold:
            # Purge: remove train samples that overlap with test labels
            test_t1 = t1.iloc[test_idx]  # test label end times
            for t0, t1_val in test_t1.items():
                # Remove train samples where [train_t0, train_t1] overlaps [t0, t1_val]
                overlap_mask = (t1_train >= t0) & (train_index <= t1_val)
                train_idx = train_idx[~overlap_mask]
            # Embargo: extra gap after test period
            ...
            yield train_idx, test_idx
```

## CombinatorialPurgedKFold (CPCV)
- N csoport → K teszt csoport → C(N,K) kombináció
- Minden path önálló backtest
- **Több path = stabilabb teljesítmény értékelés**

---

# 11. SEQUENTIAL BOOTSTRAP (AFM Ch.4)

## Probléma: Standard bootstrap → IID feltételezés sérül
- Overlapping label-ek → nem IID
- Megoldás: **Sequential Bootstrap** — csökkentjük az overlapping minták valószínűségét

```python
def sequential_bootstrap(ind_matrix, sample_length):
    # Average uniqueness = mennyire egyedi az observation
    avg_uniqueness = ind_matrix.mean() / ind_matrix.sum()
    
    # Sample with replacement, weighted by uniqueness
    for phi in range(sample_length):
        prob = avg_uniqueness / avg_uniqueness.sum()
        draw = np.random.choice(len(prob), p=prob)
        sample.append(draw)
        # Update: reduce uniqueness of overlapping observations
        ...
```

---

# 12. ORTHOGONAL FEATURES (AFM Ch.8)

## Probléma: Korrelált feature-ek → overfitting
- Megoldás: **Feature orthogonalizáció** (PCA vagy CCA)

```python
def get_orthogonal_features(df, variance_thresh=0.95):
    # PCA → keep components explaining variance_thresh% variance
    pca = PCA(n_components=variance_thresh)
    orth = pca.fit_transform(df)
    return pd.DataFrame(orth, index=df.index)
```

## Használat: Raw features + orthogonal features együtt
- Raw: interpretálható, domain knowledge
- Orthogonal: nem-korrelált, overfitting ellen

---

# 13. TREND SCANNING LABELS (AFM Ch.17)

## Alapkoncept
- Lineáris regresszió rolling ablakban: y = α + β×t
- t-value of β → label (sign = irány, |t| = konfidencia)

```python
def trend_scanning_labels(close, lookback=50):
    for each bar:
        # Rolling OLS: close = α + β×index
        slope, intercept, r_value, p_value, std_err = linregress(range(lookback), close_window)
        label = sign(slope) if |t-value| > threshold else 0
```

## KULCS: Ez egy alternatív címkézési módszer!
- Sign(slope) = trend irány (+1/-1)
- |t-value| = trend konfidencia → használható mint weight!
- **Nem kell TP/SL → egyszerűbb mint TBM**

---

# 14. ÖSSZEFOGLALÓ: MELYIK MODSZERT MIKOR?

## Címkézés választás:
| Módszer | Irány? | Bonyolultság | Ami kell |
|---------|--------|-------------|----------|
| TBM Side Labeling | ✅ +1/-1 | Közepes | **BTCUSD primary** |
| TBM Meta-Labeling | ❌ 0/1 | Magas | **BTCUSD meta** |
| Trend Labeling (Wu) | ✅ +1/-1 | Alacsony | Alternatíva |
| Trend Scanning | ✅ +1/-1 | Alacsony | Alternatíva |
| Forward Return sign | ✅ +1/-1 | Minimális | Baseline |

## Feature választás BTCUSD-re:
| Feature | Irány-infó? | Adat kell | Prioritás |
|---------|------------|-----------|-----------|
| DF_Curve (CUSUM sign) | ✅✅ | OHLC | **1** |
| Flow_Delta (vol×close_pos) | ✅✅ | OHLC+Vol | **2** |
| Tick_Imbalance × Vol | ✅ | OHLC+ticks | **3** |
| Price-Vol Correlation | ✅ | OHLC+Vol | **4** |
| Momentum Persistence | ✅ | OHLC | **5** |
| Vol-Adj Momentum | ✅ | OHLC | **6** |
| Variance Ratio 1:4 | ⚠️ | OHLC | **7** |
| Frac Diff (d≈0.4) | ⚠️ | OHLC | **8** |
| RSI / StochK | ⚠️ | OHLC | 9 |
| Kyle Lambda | ⚠️ | OHLC+Vol | 10 |
| ADX | ❌ | OHLC | Magasság csak |

## Sample Weights pipeline:
1. Average Uniqueness → overlapping súly
2. Return Attribution → hozam súly
3. Time Decay → friss = fontos
4. Class Balance → label egyensúly
5. Vertical Touch → timeout súly csökkentés

## Cross-Validation:
- **PURGED K-FOLD** kötelező! (nem standard K-fold)
- Embargo = extra gap train/test között
- CPCV = több path → stabilabb
