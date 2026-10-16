# Meta-Labeling Harness + Alpha Filter Digest

> Sources:
>   - meta-labeling-harness-main (efenn-dev) — honest take/skip evaluation
>   - meta-labeling-alpha-filter-main (Gautier Petit) — systematic signal refinement
> Generated: 2026-10-14

---

## 1. Meta-Labeling Harness — A NARRATOR vs TRADER probléma

### Kulcs felismerés
> "There are two ways to build a 'trading AI,' and one of them is a trap."

**A CSAPDA (Narrator)**: A modell megkapja a trade kimenetelét (exit price, P&L, MFE/MAE),
és azt értékeli good/bad. Ez **look-ahead bias** — a válasz már az inputban van.
A modell sosem fog pénzt keresni, mert döntéskor ezek az adatok még nem léteznek.

**A HELYES (Trader)**: Meta-labeling — a primer modell jelez, a szekunder modell
csak a **belépéskor elérhető** információ alapján dönt: take/skip.

### Leak-free garanties (unit-tesztelve!)
1. **Temporal wall**: signal bar = last visible bar, `df[df.index < entry_ts]`
2. **Causal features**: jövő mutáció nem változtatja meg a múltbeli feature vektort
3. **News cutoff**: signal bar, nem exit bar
4. **Purged + embargoed walk-forward**: train trade holding window nem nyúlhat át
   a split-en + 3 nap embargo serial-correlation leakage ellen

### P&L objective (NEM accuracy!)
> "A 99%-accurate model that only ever says 'skip' makes no money."

A threshold a **net P&L**-t maximalizálja (min coverage feltétellel),
NEM az accuracy-t. Ez a legfontosabb különbség a classifier tuningtól.

### Eredmény (5 év valós adat)
| Metrika | Single split | Walk-forward CV |
|---------|-------------|-----------------|
| Hit rate | 63% (32%→63%) | ~50% |
| Ann. Sharpe | 1.8 | **< buy-and-hold** |
| Beta vs B&H | — | 1/5 fold veri |

**Tanulság**: A single split flatter, a walk-forward CV őszinte.
A profit nagy része market exposure, nem skill.

---

## 2. Meta-Labeling Alpha Filter — Signal Refinement Pipeline

### Pipeline architektúra
```
Data → Labeling → Features → Base Model → Calibration →
Meta Model → Signal Filter (threshold+gap+TopK) →
Sizing (prob-weighted) → Risk (vol-target+lev-cap) →
Evaluation (PnL + alpha/beta + drawdown)
```

### 4 kulcs elv
1. **"Filter first, trade second"** — predict resolution, not direction
2. **"Calibration before control"** — calibrated probabilities → thresholds meaningful
3. **"Stack on probabilities, not features"** — classwise convex blender (LightGBM + MLP)
4. **"Execution hygiene"** — close→next-close PnL, asymmetric costs, EWMA vol target

### Bizonyított eredmények (Fold-3 OOS, 2020-2024, net of costs)
| Stratégia | Return | Vol | Sharpe | Max DD | Win% | PF |
|-----------|--------|-----|--------|--------|------|----|
| Meta-labeled | 12.17% | 19.51% | 0.62 | -28.07% | 65.75% | 2.92 |
| 50/50 SPY blend | 14.64% | 13.43% | **1.09** | -28.07% | — | — |
| Beta-neutral | 14.20% | 19.36% | 0.73 | — | — | — |

### Signal filtering paraméterek
| Param | Érték | Funkció |
|-------|-------|---------|
| THRESHOLD_LONG | 0.45 | Long P(take) küszöb (asymmetric!) |
| THRESHOLD_SHORT | 0.50 | Short P(take) küszöb |
| MIN_GAP | 0.10 | P(take) - max(P(skip), P(fade)) ≥ gap |
| TOP_K_PER_DAY | 3 | Overtrading guard |
| META_SCORE_MODE | "edge" | Score = P(take) - P(skip) |

### Sizing paraméterek
| Param | Érték | Funkció |
|-------|-------|---------|
| PROB_WEIGHTING | True | Probability-weighted sizes |
| WEIGHT_MODE | "margin" | signal × max(0, P(take) - P(competing)) |
| TARGET_VOL | 0.20 | EWMA(63) vol targeting |
| LEVERAGE_CAP | 3 | Hard gross leverage limit |
| LONG_SIDE_TC | 10 bps | Long transaction cost |
| SHORT_SIDE_TC | 20 bps | Short transaction cost (asymmetric!) |

### Reproducibility
- manifest.json (env + code hash)
- config_snapshot.json (resolved params)
- fold_fingerprints.json (fold dates + hashes)
- run.log.jsonl (timeline)

---

## 3. Scalper Copilot integráció

### Meta-labeling használata scalper-ben
```python
# 1. Train meta-labeler (take/skip döntés)
from meta_labeling_harness import MetaLabeler, PurgedWalkForwardCV
ml = MetaLabeler()
ml.fit(X_train, y_train, X_val, y_val_returns)

# 2. Filter signals
from signal_filter_alpha import filter_signals_with_meta_model
filtered = filter_signals_with_meta_model(signals, ml.model, X,
    th_long=0.45, th_short=0.50, min_gap=0.10, top_k_per_day=3)

# 3. Size positions
from signal_filter_alpha import probability_weighted_sizing
weights, returns = probability_weighted_sizing(
    filtered, ml.model, X, returns,
    weight_mode="margin", target_vol=0.20, leverage_cap=3.0)
```

### Anti-pattern védelem
- **AP02**: Meta-labeling = SIZE filter (NEM direction!) → probability_weighted_sizing
- **AP07**: Look-ahead → strict pre-entry feature wall
- **AP08**: Single split → PurgedWalkForwardCV (5 fold + embargo)
- **AP09**: Accuracy objective → P&L threshold tuning
- **AP15**: Overtrading → top_k_per_day + min_gap

### Leak ellenőrzés (unit test minta)
```python
# Mutate future → assert features unchanged
original_features = compute_features(df)
df_mutated = mutate_bars_after(df, entry_ts, random_change)
mutated_features = compute_features(df_mutated)
assert np.array_equal(original_features, mutated_features)
```
