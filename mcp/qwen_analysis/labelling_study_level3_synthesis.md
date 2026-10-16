# Szint 3: XAUUSD CFD Labeling — Végső Szintézis és Konkrét Terv

**Dátum:** 2026-10-09
**Alap:** Dollár bar-ok ($444K, 31,139 bar, V8 CSV) — EZ MEGVAN, ebből indulunk

---

## 1. A KÉRDÉS (amit a modellnek válaszolnia kell)

> **"5 perc (vagy N bar) alatt mi a valószínűsége, hogy XAUUSD CFD 1.5×ATR profit target-et elér vagy meghaladja azt?"**

Ez NEM egy 3-class (Long/Short/Noise) kérdés! Ez egy **bináris kérdés side-onként**:

### Long modell (CUSUM DOWN event-kor):
- **P(TP_hit | side=+1)** = P(ár eléri entry + 1.5×ATR-öt N bar-on belül, mielőtt entry - 1.0×ATR SL-t)
- Alvariánsok:
  - ✅ Jó irány, TP elér → label=1 (take)
  - ❌ Jó irány indul, visszafordul, SL → label=0 (skip)
  - ❌ Rossz irány, SL → label=0 (skip)
  - ⏱️ Timeout (N bar, egyik barrier sem) → label=0 (skip)

### Short modell (CUSUM UP event-kor):
- **P(TP_hit | side=-1)** = P(ár eléri entry - 1.5×ATR-öt N bar-on belül, mielőtt entry + 1.0×ATR SL-t)
- Ugyanazok az alvariánsok, fordítva

### Meta-labeling interpretáció:
- **label=1** → a primary signal (CUSUM direction) HELYES volt, TP hit → TAKE
- **label=0** → a primary signal ROSSZ volt (SL hit) vagy timeout → SKIP

---

## 2. A HELYES PIPELINE (dollar bar-tól éles validációig)

```
┌─────────────────────────────────────────────────────┐
│  1. DOLLAR BAR ($444K) — KÉSZ                        │
│     prado_dollar_bars.py → labeled_dollar_bars_v8.csv│
│     31,139 bar, 122 oszlop                           │
├─────────────────────────────────────────────────────┤
│  2. CUSUM FILTER — ESEMÉNYEK                        │
│     prado_cusum_filter.py → event timestamps        │
│     CUSUM DOWN → Long candidate                     │
│     CUSUM UP → Short candidate                      │
│     Csak event bar-okon címkézünk!                  │
├─────────────────────────────────────────────────────┤
│  3. PRIMARY MODEL → SIDE (+1 Long / -1 Short)       │
│     A CUSUM irány = a side!                         │
│     CUSUM DOWN event → side = +1 (Long)             │
│     CUSUM UP event → side = -1 (Short)              │
│     (Ez a Prado megközelítés: a filter adja a       │
│      side-ot, a meta-model dönt take/skip)          │
├─────────────────────────────────────────────────────┤
│  4. TRIPLE BARRIER (SIDE-AWARE, VOL-ADJUSTED)       │
│     ┌─ Long (side=+1):                              │
│     │  TP = entry + profit_mult × ATR               │
│     │  SL = entry - stop_mult × ATR                 │
│     │  MAX_BARS = 15-30                             │
│     ├─ Short (side=-1):                             │
│     │  TP = entry - profit_mult × ATR               │
│     │  SL = entry + stop_mult × ATR                 │
│     │  MAX_BARS = 15-30                             │
│     └─ Label: 1=TP hit, 0=SL hit vagy timeout       │
│                                                       │
│     ASZIMMETRIKUS: profit_mult=1.5, stop_mult=1.0   │
│     (Prado: "PT > SL gives the signal more room")    │
├─────────────────────────────────────────────────────┤
│  5. FEATURE ENGINEERING (PRE-ENTRY, LEAK-FREE)      │
│     ┌─ Boolean (AlphaPy stílus):                     │
│     │  Above_EMA20, RSI_Oversold, CUSUM_Up,         │
│     │  Trend_Up, Bullish_Bar, MACD_Bullish          │
│     ├─ Scale-free (harness stílus):                  │
│     │  f_ret_1/5/10, f_atr_pct, f_rsi_14,           │
│     │  f_sma20_gap, f_vol_ratio                     │
│     ├─ Trend minőség:                               │
│     │  trend_strength = slope × R²                  │
│     └─ Kontextus-kombinációk:                        │
│        Fade_Short_Setup = CUSUM_Down & RSI_Oversold │
│        Bounce_Long_Setup = CUSUM_Down & Above_EMA20 │
│        Breakout = CUSUM_Down & Stoch_Overbought     │
│                                                       │
│     MINDEN feature .shift(1)-elve — pre-entry!       │
├─────────────────────────────────────────────────────┤
│  6. SAMPLE WEIGHTS (AFML Ch.4)                      │
│     uniqueness = 1 / concurrent_labels              │
│     sample_weight = avg_uniqueness                  │
│     (overlap-ping label-ek kevesebb súly)            │
├─────────────────────────────────────────────────────┤
│  7. TRAINING — 2 KÜLÖN MODELL                      │
│     ┌─ Long modell: csak CUSUM DOWN event bar-ok    │
│     │  X = features[event_bar_ok], y = meta_label   │
│     │  LGBMClassifier (GPU, P4000)                  │
│     │  sample_weight = uniqueness                   │
│     ├─ Short modell: csak CUSUM UP event bar-ok     │
│     │  X = features[event_bar_ok], y = meta_label   │
│     │  LGBMClassifier (GPU, P4000)                  │
│     └─ scale_pos_weight = n_neg / n_pos             │
├─────────────────────────────────────────────────────┤
│  8. VALIDÁCIÓ (HONEST)                              │
│     ┌─ Purged + embargoed walk-forward (5 fold)     │
│     │  Embargo = 3 bar (NEM 3 nap — dollár bar!)    │
│     ├─ Benchmark: take-all ÉS buy-and-hold beta     │
│     ├─ Profit objective (NEM accuracy!)              │
│     │  threshold = argmax sum(net_return | p>th)    │
│     ├─ Coverage floor: min 5% jelet vesz            │
│     └─ Verdict: lehet "NO EDGE" — és ez OK!         │
├─────────────────────────────────────────────────────┤
│  9. ÉLES PREDIKCIÓ                                  │
│     CUSUM DOWN event → Long modell → P(take)        │
│     CUSUM UP event → Short modell → P(take)         │
│     if P(take) >= threshold: TRADE                  │
│     else: SKIP                                      │
└─────────────────────────────────────────────────────┘
```

---

## 3. KONKRÉT KÓD FORGÁS (fork-ok a tananyagból)

### 3.1 Triple Barrier (side-aware)
**Forrás:** `financial-ml-toolkit/pipeline/labeling_advanced.py` (133-183 sor)
```python
def triple_barrier_labels(close, volatility, profit_mult, stop_mult,
                           num_bars, side=None):
    # ...
    if trade_side == 1:  # Long
        upper = entry_price * (1 + profit_mult * vol)
        lower = entry_price * (1 - stop_mult * vol)
    else:  # Short
        upper = entry_price * (1 + stop_mult * vol)
        lower = entry_price * (1 - profit_mult * vol)
    
    touch_idx, touch_type = _find_barrier_touch(price_path, upper, lower, len(price_path))
    result.loc[t0, 'label'] = touch_type if trade_side == 1 else -touch_type
```

**XAUUSD CFD adaptáció:**
```python
def triple_barrier_xauusd(close, atr, side, profit_mult=1.5, stop_mult=1.0, max_bars=20):
    """
    Side-aware triple barrier for XAUUSD CFD dollar bars.
    
    Args:
        close: dollar bar close prices (Series)
        atr: ATR14 per bar (Series)
        side: +1 (Long) or -1 (Short) from CUSUM direction
        profit_mult: TP distance in ATR multiples (1.5 = 1.5×ATR)
        stop_mult: SL distance in ATR multiples (1.0 = 1.0×ATR)
        max_bars: vertical barrier (max holding period)
    
    Returns:
        label: 1 (TP hit) or 0 (SL hit / timeout)
        bars_to_hit: how many bars until barrier hit
        ret: return at exit (signed by side)
    """
    for i, bar in event_bars.iterrows():
        entry = bar['close']
        vol = bar['atr14']
        s = bar['side']  # from CUSUM
        
        if s == 1:  # Long
            tp = entry + profit_mult * vol
            sl = entry - stop_mult * vol
        else:  # Short
            tp = entry - profit_mult * vol
            sl = entry + stop_mult * vol
        
        # Scan forward max_bars
        for j in range(1, max_bars + 1):
            price = close[i + j]
            if s == 1 and price >= tp:
                label, bars = 1, j
                break
            elif s == -1 and price <= tp:
                label, bars = 1, j
                break
            elif s == 1 and price <= sl:
                label, bars = 0, j
                break
            elif s == -1 and price >= sl:
                label, bars = 0, j
                break
        else:
            label, bars = 0, max_bars  # timeout
```

### 3.2 Meta-Labeling
**Forrás:** `financial-ml-toolkit/pipeline/labeling_advanced.py` (191-206 sor)
```python
def get_meta_labels(primary_signal, triple_barrier_result):
    # signal=1 (Long) AND label=1 (TP hit) → meta=1 (take)
    # signal=-1 (Short) AND label=-1 (TP hit for short) → meta=1 (take)
    # Otherwise → meta=0 (skip)
    meta_labels = ((signals == 1) & (labels == 1)) | ((signals == -1) & (labels == -1))
    return meta_labels.astype(int)
```

**XAUUSD CFD:** Mivel már side-aware triple barrier-t használunk, a meta-label egyszerűen:
```python
# A triple_barrier_xauusd már return-öl label=1 (TP hit) vagy 0 (SL/timeout)
# Ez EGYENESEN a meta-label! Nincs szükség külön meta-labeling lépésre.
meta_label = triple_barrier_label  # 1 = take, 0 = skip
```

### 3.3 Boolean Features (AlphaPy stílus)
**Forrás:** `AlphaPy/alphapy/transforms.py` (53, 123, 760, 837 sor)
```python
def abovema(f, c, p): return f[c] > f[c].rolling(p).mean()  # bool
def belowma(f, c, p): return f[c] < f[c].rolling(p).mean()  # bool
def higher(f, c, o):  return f[c] > f[c].shift(o)           # bool
def lower(f, c, o):   return f[c] < f[c].shift(o)           # bool
```

**XAUUSD CFD konkrét boolean feature-k:**
```python
# Ár vs MA
above_ema20 = close > EMA(close, 20)
above_ema50 = close > EMA(close, 50)

# RSI
rsi_oversold = RSI(14) < 30
rsi_overbought = RSI(14) > 70

# Stochastic
stoch_oversold = StochK < 20
stoch_overbought = StochK > 80

# MACD
macd_bullish = MACD_hist > 0
macd_bearish = MACD_hist < 0

# CUSUM irány (ez adja a side-ot!)
cusum_long = cusum_direction == 1   # DOWN event → Long
cusum_short = cusum_direction == -1  # UP event → Short

# Bar irány
bullish_bar = close > open
bearish_bar = close < open

# Trend
trend_up = Slope_Close_14 > 0
trend_down = Slope_Close_14 < 0
```

### 3.4 Kontextus-kombinációk (ÚJ — a V5-ben nem volt!)
```python
# Ezek a boolean feature-k KOMBINÁCIÓJA — a fa nem tudja automatikusan
fade_short_setup = cusum_short & rsi_overbought & trend_down
bounce_long_setup = cusum_long & rsi_oversold & above_ema50
breakout_long = cusum_long & stoch_overbought & macd_bullish
breakdown_short = cusum_short & stoch_oversold & macd_bearish
trend_resume_long = cusum_long & trend_up & above_ema20
trend_resume_short = cusum_short & trend_down & ~above_ema20
```

### 3.5 Sample Weights (AFML Ch.4)
**Forrás:** `financial-ml-toolkit/pipeline/sample_weights.py`
```python
# Concurrent labels = overlap a triple barrier intervallumok között
concurrent = get_num_concurrent_labels(close, t1)
# Uniqueness = 1 / concurrent
uniqueness = 1.0 / concurrent
# Average uniqueness a label élettartama alatt
avg_uniqueness = get_average_uniqueness(t1, close)
# Ez lesz a sample_weight a tanításnál
sample_weight = avg_uniqueness
```

### 3.6 Purged Walk-Forward CV
**Forrás:** `meta-labeling-harness/cross_validate.py`
```python
# Purge: ha egy train label holding window átnyúlik a test határon → drop
# Embargo: 3 bar (vagy 3 nap) tiltó övezet a split körül
# Walk-forward: expanding window (train növekszik, test mindig forward)
# Benchmark: take-all baseline ÉS buy-and-hold beta
```

---

## 4. MI VÁLTOZIK A RÉGI V5-HEZ KÉPEST?

| Elem | Régi V5 (hibás) | Új (Prado-helyes) |
|---|---|---|
| **Label** | Szimmetrikus TB (PT=SL=2×ATR) → ~50/50 random | **Side-aware TB** (PT=1.5×ATR, SL=1.0×ATR) → aszimmetrikus, irány-tudatos |
| **Irány** | Nincs! A modell próbál irányt predikálni random label-ből | **CUSUM direction = side** → a filter adja az irányt |
| **Feature-k** | Csak float (Dist_Micro_S=1.5) — a fa nem érti | **Boolean + float**: Above_EMA20, RSI_Oversold, CUSUM_Up |
| **Kontextus** | Nincs | **Kombinációk**: Fade_Short_Setup, Bounce_Long_Setup |
| **Model** | 1 modell próbál mindent | **2 modell**: Long (CUSUM DOWN) és Short (CUSUM UP) |
| **Sample weight** | scale_pos_weight csak | **Uniqueness + scale_pos_weight** |
| **Validáció** | Single split OOS | **Purged walk-forward CV + beta benchmark** |
| **Objective** | Accuracy | **Net P&L (profit objective)** |

---

## 5. IMPLEMENTÁCIÓ SORREND

### Phase 1: Labeling (EZ AZ ELSŐ ÉS LEGFONTOSABB!)
1. `cusum_filter_events.py` — CUSUM filter a dollár bar-okon → event timestamps + direction
2. `triple_barrier_side_aware.py` — side-aware TB a CUSUM event-eken
   - Fork: `financial-ml-toolkit/pipeline/labeling_advanced.py`
   - Paraméterek: profit_mult=1.5, stop_mult=1.0, max_bars=20
3. `verify_labels.py` — label eloszlás vizualizáció
   - Ellenőrzés: Long TP% vs SL%, Short TP% vs SL%
   - HA TP% ≈ 50% mindenhol → fundamentális probléma (feature-k nem prediktívek)

### Phase 2: Feature Engineering
4. `features_boolean.py` — AlphaPy stílusú boolean feature-k
5. `features_scalefree.py` — harness stílusú scale-free feature-k
6. `features_context.py` — kontextus-kombinációk
7. `verify_leakfree.py` — .shift(1) audit minden feature-en

### Phase 3: Training
8. `sample_weights_uniqueness.py` — AFML Ch.4 concurrency weights
9. `train_long_model.py` — LGBM GPU, CUSUM DOWN event-ek
10. `train_short_model.py` — LGBM GPU, CUSUM UP event-ek

### Phase 4: Validáció
11. `purged_walkforward_cv.py` — 5 fold, 3 bar embargo
12. `eval_vs_beta.py` — take-all és buy-and-hold benchmark
13. `profit_threshold.py` — threshold optimalizálás net P&L-re

### Phase 5: Élesítés
14. HUD update — 2 modell predikció, P(take) threshold
15. Copilot update — CUSUM event → side → model → take/skip

---

## 6. FORK-OK ÖSSZEFOGLALÁSA

| Mit | Honnan | Sorok | Cél |
|---|---|---|---|
| Triple barrier (side-aware) | financial-ml-toolkit/labeling_advanced.py | 91-184 | A labeling mag |
| Meta-labeling | financial-ml-toolkit/labeling_advanced.py | 191-206 | Take/skip label |
| CUSUM filter | financial-ml-toolkit/labeling_advanced.py | 213-240 | Event sampling |
| Boolean transforms | AlphaPy/transforms.py | 53-858 | Tree-friendly features |
| Pre-entry features | meta-labeling-harness/decision_features.py | 60-235 | Leak-free features |
| Sample weights | financial-ml-toolkit/sample_weights.py | 22-120 | Uniqueness weights |
| Purged CV | meta-labeling-harness/cross_validate.py | teljes | Honest validation |
| Profit objective | meta-labeling-harness/meta_labeler.py | 120-165 | Threshold tuning |
| Primary models | financial-ml-toolkit/primary_models.py | 33-150 | Side generators |
