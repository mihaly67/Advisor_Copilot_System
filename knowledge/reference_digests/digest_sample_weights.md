# Sample Weights & Cross-Validation — Code Digest

## Dátum: 2026-10-12
## Forrás: financial-ml-toolkit/pipeline/sample_weights.py

---

## 1. CONCURRENT LABELS (AFML Ch.4)

### Probléma
TBM label-ek **overlap**-pelnek! Egy bar befolyásolhat több label-t.
Standard ML feltételezi: IID → de financial label-ek korreláltak.

### Indicator Matrix
```python
def get_indicator_matrix(bar_index, t1):
    """Binary matrix: which bars influence which labels."""
    ind_matrix = pd.DataFrame(0, index=bar_index, columns=range(len(t1)))
    for i, (t0, t1_val) in enumerate(t1.items()):
        mask = (bar_index >= t0) & (bar_index <= t1_val)
        ind_matrix.loc[mask, i] = 1
    return ind_matrix
```

### Concurrent Count
```python
def get_num_concurrent_labels(close, t1):
    """For each bar, how many labels span over it?"""
    concurrent = pd.Series(0, index=close.index)
    for t0, t1_val in t1.items():
        mask = (close.index >= t0) & (close.index <= t1_val)
        concurrent.loc[mask] += 1
    return concurrent
```

---

## 2. AVERAGE UNIQUENESS

```python
def get_average_uniqueness(t1, close):
    """Uniqueness = 1/concurrent_labels. Average over label's lifespan."""
    concurrent = get_num_concurrent_labels(close, t1)
    uniqueness = 1.0 / concurrent.replace(0, np.nan)
    avg_uniqueness = pd.Series(index=t1.index, dtype=float)
    for t0, t1_val in t1.items():
        mask = (close.index >= t0) & (close.index <= t1_val)
        avg_uniqueness.loc[t0] = uniqueness.loc[mask].mean()
    return avg_uniqueness
```

### BTCUSD: Dollar bar ~1M USD → num_bars=50 → 50M USD overlapping
- Tipikus concurrency: 10-20 overlapping label
- Uniqueness: 0.05-0.10 → nagyon nem IID!

---

## 3. SEQUENTIAL BOOTSTRAP

```python
def sequential_bootstrap(ind_matrix, sample_length=None):
    """Sample with replacement, weighted by uniqueness.
    Reduces probability of drawing overlapping observations."""
    avg_uniqueness = ind_matrix.mean() / ind_matrix.sum()
    for phi in range(sample_length):
        prob = avg_uniqueness / avg_uniqueness.sum()
        draw = np.random.choice(len(prob), p=prob)
        sample.append(draw)
        # Update: reduce uniqueness of overlapping observations
```

### Használat: bootstrapped average uniqueness → sample_weight

---

## 4. RETURN ATTRIBUTION WEIGHTS

```python
def get_sample_weights_by_return(close, t1, num_bars=None):
    """Weight samples by absolute return attribution.
    Larger moves = more important to classify correctly."""
    returns = close.pct_change()
    weights = pd.Series(index=t1.index, dtype=float)
    for t0, t1_val in t1.items():
        mask = (close.index >= t0) & (close.index <= t1_val)
        weights.loc[t0] = abs(close.loc[t1_val] / close.loc[t0] - 1)
    return weights
```

---

## 5. TIME DECAY

```python
def get_time_decay_weights(t1, close, decay=0.5):
    """Exponential decay: recent samples weighted higher."""
    last_date = t1.max()
    weights = pd.Series(index=t1.index, dtype=float)
    for t0, t1_val in t1.items():
        age = (last_date - t0).total_seconds()
        max_age = (last_date - t1.index[0]).total_seconds()
        weights.loc[t0] = decay ** (age / max_age)
    return weights
```

---

## 6. PURGED K-FOLD (AFML Ch.7)

```python
class PurgedKFold(BaseCrossValidator):
    def __init__(self, n_splits=5, t1=None, pct_embargo=0.01):
        self.t1 = t1  # Label end times
        self.pct_embargo = pct_embargo
    
    def split(self, X):
        for train_idx, test_idx in standard_kfold:
            # PURGE: remove train samples overlapping test labels
            test_t1 = self.t1.iloc[test_idx]
            test_start = X.index[test_idx[0]]
            test_end = test_t1.max()
            
            # Remove from train: samples where [t0, t1] overlaps test
            purge_mask = (self.t1.iloc[train_idx] >= test_start) & \
                         (X.index[train_idx] <= test_end)
            train_idx = train_idx[~purge_mask]
            
            # EMBARGO: extra gap after test period
            embargo_size = int(len(X) * self.pct_embargo)
            embargo_end = test_idx[-1] + embargo_size
            train_idx = train_idx[train_idx < test_idx[0] - embargo_size]
            
            yield train_idx, test_idx
```

### BTCUSD: `pct_embargo=0.01` → 1% of data = ~50 bars gap

---

## 7. COMBINATORIAL PURGED CV (CPCV)

```python
class CombinatorialPurgedKFold:
    def __init__(self, n_groups=6, k_test_groups=2, t1=None):
        # N groups → K test → C(N,K) combinations
        # Each combination = one "path" (train/test split)
        # More paths = more stable evaluation
```

### CPCV vs Standard K-Fold
- K-Fold: 5 splits → 5 backtest
- CPCV (6,2): C(6,2)=15 paths → 15 backtest → **sokkal stabilabb**

---

## PIPELINE: SAMPLE WEIGHTS ÖSSZEÁLLÍTÁSA

```python
# 1. Average uniqueness
uniqueness = get_average_uniqueness(t1, close)

# 2. Return attribution
return_weights = get_sample_weights_by_return(close, t1)

# 3. Time decay
time_weights = get_time_decay_weights(t1, close, decay=0.5)

# 4. Combine
sample_weight = uniqueness * return_weights * time_weights

# 5. Normalize
sample_weight = sample_weight / sample_weight.mean()

# 6. Class balance (optional)
# If label imbalance: upweight minority class
pos_count = (labels == 1).sum()
neg_count = (labels == -1).sum()
scale_pos = neg_count / pos_count
sample_weight[labels == 1] *= scale_pos
```

### LightGBM integráció
```python
model = lgb.LGBMClassifier(...)
model.fit(X_train, y_train, sample_weight=sample_weight_train)
```
