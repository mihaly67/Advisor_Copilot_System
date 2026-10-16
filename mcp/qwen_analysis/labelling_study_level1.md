# Szint 1: Labelling Tanulmány — Alapok és Repo-katalógus

**Dátum:** 2026-10-09
**Cél:** Fundamentális megértés: hogyan címkézzünk XAUUSD CFD dollár bar-okon triple barrier-rel, irány-tudatosan

---

## 1. Repo-katalógus — Mit találtunk

### /data/ml/barrier-method-main/ — Triple Barrier (nkonts)
- **BarrierMethod** osztály: vektorizált, pandas/numpy alapú
- `returns`-alapú (NEM irány-tudatos!) — label = -1/0/+1
- `n_barriers` paraméter: többszörös barrierek (±1%, ±2%, stb.)
- `center=True`: returns középpontra vonatkozása
- **TANULSÁG:** Ez csak az alap — NEM tud irányt mondani, csak return-alapú label

### /data/ml/.../FinancialMachineLearning-main/ — Prado AFML implementáció
- **labeling.py** — A HIVATALOS Prado triple barrier:
  - `apply_pt_sl_on_t1()`: `cum_returns = (closing_prices / close[loc] - 1) * events_.at[loc, 'side']`
  - **`side` paraméter** — EZ A KULCS! A return-eket SZOROZZA a side-dal (+1 Long, -1 Short)
  - `get_events()`: ha `side_prediction=None` → side=1.0 (Long-only), szimmetrikus pt_sl
  - ha `side_prediction` megvan → aszimmetrikus pt_sl, side a primary modelből
  - `meta_labeling()`: `out_df.loc[out_df['ret'] <= 0, 'bin'] = 0` — ha a side rossz → label=0 (SKIP)
  - `drop_labels()`: ritka label-ek eldobása
- **trend_search.py** — Trend labeling: OLS t-érték → +1 (uptrend) / -1 (downtrend)
- **tail_set.py** — Vol-adjusted return decile labeling

### /data/ml/.../meta-labeling-harness-main/ — Decision-time meta-labeling (efenni-dev)
- **A LEGHONESTABB megközelítés!**
- `meta_labeler.py`: take/skip döntés, threshold net P&L-re optimalizálva (NEM accuracy!)
- `eval_policy.py`: trader-ként értékel — coverage, hit rate, Sharpe, drawdown
- `cross_validate.py`: purged + embargoed walk-forward CV
- `schema.py`: FEATURE_KEYS = scale-free, strictly pre-entry features
  - Trailing returns: f_ret_1, f_ret_5, f_ret_10, f_ret_21, f_ret_63
  - MA structure: f_sma20_gap, f_sma50_gap, f_sma200_gap
  - Momentum: f_rsi_14, f_macd_hist, f_donchian_pos
  - Volatility: f_atr_pct, f_vol_20, f_vol_ratio
  - Market-relative: f_relret_5, f_beta_63, f_resid_ret_21
  - Categorical: archetype, side, style, regime, market_regime
- **RESEARCH_NOTE.md:**
  - Single split: Sharpe 1.8 → Walk-forward CV: Sharpe 0.16 (!!!)
  - Beta-benchmark: 1/5 fold veri csak a buy-and-hold-ot
  - "Weak, unstable signal-filtering with no demonstrated alpha over beta"
  - **A negatív eredmény jelenti a pontot!**

### /data/ml/.../meta-labeling-alpha-filter-main/ — End-to-end meta-labeling pipeline
- `labeling.py` (15896 bájt) — KÉT implementáció: loop + vektorizált
  - **side = daily_signals.at[date, ticker]** — PRIMARY MODEL adja az irányt
  - `if side == 1: tp = entry*(1+tp*vol), sl = entry*(1-sl*vol)`
  - `else: tp = entry*(1-tp*vol), sl = entry*(1+sl*vol)` — Short: TP lent, SL fent
  - First hit wins, TP before SL same day
- `features.py` (19573 bájt) — Feature engineering
- `modeling.py` (13358 bájt) — Model training
- `evaluation.py` (35313 bájt) — Evaluation
- `sizing.py` (7663 bájt) — Bet sizing (Kelly)

### /data/ml/.../financial-ml-toolkit-main/ — Teljes AFML pipeline
- `labeling.py` (9904 bájt) — Triple barrier (numba JIT-optimized)
  - `_find_first_barrier_hit()` JIT-compiled
  - `get_horizontal_barriers()`: upper = close + vol*profit_mult, lower = close - vol*stop_mult
  - **ASZIMMETRIKUS:** profit_mult ≠ stop_mult (pl. 2.0 vs 1.0)
- `labeling_advanced.py` (13455 bájt) — Haladó labeling:
  - **side paraméter** a triple_barrier_labels()-ben
  - `if trade_side == 1: upper=entry*(1+profit*vol), lower=entry*(1-stop*vol)`
  - `else: upper=entry*(1+stop*vol), lower=entry*(1-profit*vol)` — Short: upper=SL, lower=TP
  - `result['label'] = touch_type if trade_side == 1 else -touch_type` — Short label invertálva!
  - **get_meta_labels()**: `((signals==1) & (labels==1)) | ((signals==-1) & (labels==-1))` → 1=take, 0=skip
  - **cusum_filter()** — CUSUM event sampling
  - **trend_scanning_labels()** — OLS t-érték alapú trend labeling
  - **Parkinson volatility** — high-low range alapú vol
  - **AdvancedLabeler** osztály — teljes pipeline
- `meta_model.py` (18565 bájt):
  - **PrimaryModel ABC** — generate_signals() → {1, -1, 0}
  - **SMACrossover** — fast/slow SMA crossover → signal
  - **MetaModel** — RandomForest, meta_labels (1=correct, 0=wrong)
- `primary_models.py` (11984 bájt):
  - RSIMeanReversion, BollingerBreakout, MACDCrossover, MomentumRotation
- `sample_weights.py` (22530 bájt) — Concurrency/uniqueness weights
- `backtester.py` (23264 bájt) — Backtest engine

---

## 2. FUNDAMENTÁLIS MEGÉRTÉS — A 5 KULCSFELISMERÉS

### K1: A TRIPLE BARRIER IRÁNY-TUDOS (side-aware)
- **HELYTELEN:** Csak return-alapú label (barrier-method: r > barrier → 1, r < -barrier → -1)
- **HELYES:** `side` paraméter → Long: TP fent, SL lent | Short: TP lent, SL fent
- A Prado implementáció: `cum_returns * side` — a return-eket megszorozza a side-dal

### K2: META-LABELING = KÉT MODEL (Primary + Secondary)
1. **Primary model** → OLDAL (Long/Short) — irány-prediktor
   - Pl.: SMA crossover, RSI mean-reversion, CUSUM filter direction
   - Ez határozza meg a TP/SL barrier pozícióját!
2. **Secondary model** → TAKE/SKIP — meta-címke
   - Label: 1 ha a primary signal helyes volt (TP hit), 0 ha rossz (SL hit)
   - Ez szűri a gyenge jeleket

### K3: A LABEL NEKÜNK: "5 perc alatt mi a valószínűsége hogy 1.5×TPR elér?"
Ez pontosan a **primary model** kérdése! A válasz:
- **Long modell:** P(TP_hit | CUSUM_DOWN event, 5perc ablak, 1.5×ATR TP, 1.0×ATR SL)
- **Short modell:** P(TP_hit | CUSUM_UP event, 5perc ablak, 1.5×ATR TP, 1.0×ATR SL)
- A meta-labeling erre válaszol: 1 = vedd a jelet, 0 = hagyd

### K4: LEAK-FREE KÖVETELMÉNYEK
- **Features:** CSAK pre-entry bar-ok (df[df.index < entry_ts])
- **Label:** forward outcome, SOHA nem feature
- **Split:** purged + embargoed walk-forward (3 nap embargo)
- **Cost-aware:** label vonja le a költséget (10 bps + slippage)

### K5: ÉRTÉKELÉS = TRADER, NEM CLASSIFIER
- **Objective:** net P&L, NEM accuracy
- **Benchmark:** take-all ÉS buy-and-hold beta
- **Coverage floor:** nem elég ha 99% accurate de csak 3% jelet vesz
- **Verdict:** lehet "NO EDGE" — és ez a helyes eredmény!

---

## 3. A HELYES PIPELINE (amit meg kell építeni)

```
Dollar Bar-ok ($444K)
    ↓
CUSUM Filter → event-ek (mikor kereskedjek)
    ↓
Primary Model → side = +1 (Long) vagy -1 (Short)
    ↓
Triple Barrier (side-aware, vol-adjusted, aszimmetrikus)
    PT = entry ± profit_mult × ATR × side
    SL = entry ∓ stop_mult × ATR × side
    Max_bars = 15-30
    ↓
Meta-Label → 1 (take) vagy 0 (skip)
    ↓
Secondary Model (LGBM) → P(take) threshold
    ↓
Trade execution: csak ha P(take) >= threshold
```

---

## 4. AMI MÉG KELL (Szint 2)
- AlphaPy boolean feature-k (abovema, belowma, higher, lower)
- FreqAI end-to-end pipeline
- AFS_BM-Algorithm részletes vizsgálata
- Sample weights (concurrency, uniqueness, time-decay)
- Feature engineering minták a reference repókból
