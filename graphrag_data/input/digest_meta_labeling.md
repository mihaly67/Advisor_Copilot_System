# Meta-Labeling — Code Digest

## Dátum: 2026-10-12

---

## KONCEPT: KÉT MODEL LAYER

```
┌─────────────────────────────────────────────┐
│  PRIMARY MODEL (side model)                 │
│  Input: features → Output: side (+1 vagy -1)│
│  Ez dönti el: LONG vagy SHORT?              │
├─────────────────────────────────────────────┤
│  META MODEL (size/filter model)             │
│  Input: features → Output: P(correct) ∈ [0,1]│
│  Ez dönti el: VEGYÜK-E A TRADE-T?          │
│  Ha P > threshold → trade, else → skip      │
└─────────────────────────────────────────────┘
```

## LABELING PIPELINE

```python
# Step 1: Primary model predicts side
side = primary_model.predict(features)  # +1 or -1

# Step 2: TBM with side → does this trade profit?
tbm_labels = triple_barrier_labels(close, side=side, ...)
# +1 = TP hit (profitable for this side)
# -1 = SL hit (loss for this side)
#  0 = timeout

# Step 3: Meta-label = was primary correct?
meta_label = 1 if (side==1 and tbm==1) or (side==-1 and tbm==-1) else 0
# meta_label = 1 → primary was RIGHT → should have traded
# meta_label = 0 → primary was WRONG → should have skipped
```

## IMPLEMENTÁCIÓ (financial-ml-toolkit)

```python
# labeling.py
def get_meta_labels(primary_signal, triple_barrier_result):
    common_idx = primary_signal.index.intersection(triple_barrier_result.index)
    signal = primary_signal.loc[common_idx]
    labels = triple_barrier_result.loc[common_idx, 'label']
    meta_labels = ((signal == 1) & (labels == 1)) | ((signal == -1) & (labels == -1))
    return meta_labels.astype(int)

# labeling_advanced.py
def get_meta_labels(side, labels_df):
    # Same logic, slightly different interface
    side_labels = labels_df['label']
    meta = pd.Series(index=side.index, dtype=int)
    meta.loc[(side == 1) & (side_labels == 1)] = 1
    meta.loc[(side == -1) & (side_labels == -1)] = 1
    meta.loc[meta.isna()] = 0
    return meta.astype(int)
```

## POSITION SIZING A META-MODEL SEGÍTSÉGÉVEL

```python
# Inference time:
side = primary_model.predict(features)           # +1 or -1
p_correct = meta_model.predict_proba(features)   # P(meta=1)

# Option 1: Hard filter
if p_correct > 0.5:
    position = side * base_size
else:
    position = 0  # Skip trade

# Option 2: Prob-weighted sizing
position = side * p_correct * base_size  # Size proportional to confidence

# Option 3: Vol-targeting with meta
vol = get_volatility(close)
target_vol = 0.15  # Annual target
size = side * p_correct * (target_vol / vol)  # Vol-adjusted meta sizing

# Option 4: Lambda-blend (conservative)
lambda_ = 0.3
size = side * (lambda_ * p_correct + (1 - lambda_) * 1.0) * base_size
# Even if meta says 0, still trade at 30% of base (lambda hedge)
```

## SIDE-AWARE THRESHOLD

```python
# Different thresholds for long vs short
if side == 1:  # Long
    threshold_long = 0.6   # Require 60% confidence for long
    if p_correct > threshold_long:
        position = side * base_size
elif side == -1:  # Short
    threshold_short = 0.55  # Require 55% for short (shorts often easier in crypto)
    if p_correct > threshold_short:
        position = side * base_size
```

## KULCS FELISMERÉS

**Meta-labeling NEM irány-predikció!**
- Primary model = irány (+1/-1) — ez a "side model"
- Meta model = trade filter (0/1) — ez a "size model"
- **SOHA** ne keverd össze a kettőt!
- A meta model azért bináris, mert a side-t már a primary adja

## BTCUSD SPECIFIKUS

- Primary: LightGBM → features → side (+1/-1)
- Meta: LightGBM → features → P(correct|side)
- Threshold: dinamikus, EWMA vol alapú
- Minimum trade frequency: legalább 10% tick-ben trade (különben túl konzervatív)
