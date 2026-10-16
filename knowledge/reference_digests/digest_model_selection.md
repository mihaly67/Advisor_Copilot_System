# Model Selection Digest — Meta-Labeling, Ensemble, Threshold Optimization

> Source: MlFinLab (AFML), EA31337, CSA-15, EURUSD_Scalper, our V3 pipeline
> Generated: 2026-10-14 | For LGBM Copilot Knowledge Space

---

## Model Architecture Decision

### Option 1: Single Direction Model (Current V3)
- One LightGBM predicting side (+1/-1)
- **Our results**: AUC 0.7035, Long=0.6715, Short=0.6461
- **Pros**: Simple, fast, easy to debug
- **Cons**: No bet sizing, no trade filtering, no position management

### Option 2: Meta-Labeling Pipeline (MlFinLab AFML Ch.3)
- **Stage 1**: Primary model → direction (+1 Long / -1 Short)
- **Stage 2**: Secondary model → take (1) or skip (0)
- **CRITICAL**: Stage 2 is SIZE FILTER, not direction predictor
- **Output**: trade = side if size==1, else NO_TRADE

#### Meta-Labeling Benefits
- Built-in trade filtering: skip low-confidence signals
- Position sizing: `size_proba` → confidence-weighted lot size
- Asymmetric barriers: profit_mult > stop_mult gives signal more room
- **Expected improvement**: +2-5% in precision, -10-20% in trade count (quality over quantity)

#### Meta-Labeling Anti-Patterns
- **AP02**: Using meta-labeling for direction → binary 0/1 cannot express Long/Short
- **AP03**: Symmetric TP=SL → ~50/50 → random, must be asymmetric (PT>SL)

### Option 3: Long/Short Split Models
- Separate LightGBM for Long and Short
- **Our V3 result**: Long AUC 0.6715, Short AUC 0.6461
- Different thresholds: Long 0.45, Short 0.50 (shorts riskier)
- Different top features per side
- **AP11**: Same threshold for both → shorts need higher confidence

### Option 4: Ensemble Voting (EA31337)
- 30+ simple strategies vote independently
- Weighted by recent performance (adaptive)
- Min agreement: 60% of models must agree
- **Pros**: Robust, no single point of failure
- **Cons**: Complex, slower, more hyperparameters

---

## Labeling Method Comparison

| Method | Signal Rate | Best For | Complexity | Our Status |
|--------|-------------|----------|------------|------------|
| Fixed Time Horizon | High | Simple, fast | Low | ❌ |
| **Triple Barrier** | Medium | Balanced | Medium | ✅ Current |
| Trend Scanning | Variable | Adaptive | High | ❌ NEW |
| **Meta-Labeling** | Configurable | Best accuracy | High | ❌ NEW |

### Trend Scanning (MlFinLab)
- OLS regression on price → t-value sign as label
- |t-value| as sample weight (stronger trend = higher weight)
- **Advantage**: No fixed TP/SL needed — labels adapt to market dynamics
- **When to try**: If Triple Barrier labels are too rigid

---

## Feature Count vs Model Performance

### Current V3
- 5 features: tv_60, tv_20, atr_pct, micro_sqz, rsi_n
- AUC: 0.7035
- Room for improvement with ICT features

### Projected with ICT Features
| Feature Set | Count | Expected AUC | Source |
|-------------|-------|-------------|--------|
| Current V3 | 5 | 0.7035 | ✅ Actual |
| + FVG + OB | 8 | 0.72-0.73 | BAKOME |
| + POC + Session | 12 | 0.73-0.74 | NQ1 + BAKOME |
| + HTF + FreshTrigger | 15 | 0.74-0.75 | CSA-15 |
| + Meta-Labeling | 15+2 models | 0.75-0.77 | MlFinLab |

### Feature Selection Pipeline
1. Start with 8-12 features (direction + volatility + regime)
2. Add ICT features (FVG, OB, POC) → expect +0.02-0.04 AUC
3. Add session features → expect +0.01-0.02 AUC
4. SHAP pruning: drop features with importance < 0.01
5. Correlation pruning: remove features with corr > 0.95
6. **SWEET SPOT: 15-20 features after pruning**

---

## Threshold Optimization

### Methods
| Method | Logic | When |
|--------|-------|------|
| Fixed 0.5 | Baseline only | Never optimal |
| **Side-aware** | Long=0.45, Short=0.50 | Default for scalper |
| ROC Optimal | argmax(TPR - FPR) | Balanced long/short |
| **Profit Optimal** | Grid search → max OOS profit | Production |
| Meta-labeling | size_model proba > 0.55-0.65 | Meta pipeline active |

### Side-Aware Thresholds
- Long threshold: 0.45 (slightly lower — more long trades)
- Short threshold: 0.50 (higher — shorts are riskier)
- **AP11**: Same threshold for both → suboptimal

---

## Scoring Systems from Advisor Repos

### CSA-15 (8-point, min 6)
1. Squeeze momentum direction
2. RSI overbought/oversold
3. MACD confirmation
4. Volume surge
5. HTF trend alignment
6. Bollinger band position
7. Stochastic confirmation
8. EMA cross
→ Signal if ≥6/8 conditions met

### EURUSD Scalper (7-point, min 4)
1. EMA cross
2. EMA trend alignment
3. RSI filter
4. BB squeeze
5. MACD
6. Stochastic
7. Volume surge
→ Signal if ≥4/7, strong if ≥6/7 (2.5x lot boost)

### Key Insight
- Multi-confirmation scoring ≈ our approach but with explicit minimum
- **Recommendation**: Add `min_confirmation_score` parameter to signal generation
- Default: 0.6 (between CSA-15's 0.75 and EURUSD's 0.57)

---

## Walk-Forward Validation

### Why PurgedKFold is Not Enough
- PurgedKFold prevents leakage in CV
- But doesn't test sequential performance degradation
- Walk-forward: train on [0,T], test on [T,T+Δ], shift, repeat

### Implementation
```python
for fold in range(n_folds):
    train_end = initial_train + fold * step
    test_end = train_end + test_window
    model.fit(X[:train_end], y[:train_end])
    preds = model.predict(X[train_end:test_end])
    # Track OOS metrics per fold → check for degradation
```

### When to Retrain
- If latest fold AUC drops > 10% from average → retrain
- If feature importance shifts > 20% → retrain with fresh data
