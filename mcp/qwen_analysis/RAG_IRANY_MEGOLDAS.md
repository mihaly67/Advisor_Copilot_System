# RAG + Web kutatás eredményei — Irány-predikció LightGBM-hez

## RAG találatok (336,907 chunk-ból)

### 1. LGBM-Stock-Prediction-main (score: 0.61)
**LightGBM + Triple Barrier labeling pipeline.**

Kulcs feature-ök:
- `past_return_1` to `past_return_10`: `(close - close.shift(n)) / close.shift(n)` — **NYERS % return, ATR normalizálás NÉLKÜL**
- `past_log_return_1` to `past_log_return_10`: `log(close / close.shift(n))` — **nyers log return**
- `momentum_score`: 14-bar linear regression slope × R² (annualizált) — **trend erősség + irány**
- `slope` of close/ema/high/low/open/volume/rsi (14-bar rolling) — **regresszió meredekség**
- `(close/ema)-1, (close/sma)-1` — távolság mozgóátlagtól (signed)
- `upper/close-1, 1-lower/close` — Bollinger sáv távolság
- Future returns (`return_1` to `return_10`) — labeling-hez

### 2. mlfinlab labeling.py (score: 0.64)
**Meta-labeling implementáció (López de Prado):**

- `get_events()`: Triple barrier — pt_sl array [profit_taking, stop_loss], target=volatility
- `get_bins()`: Ha `side_prediction` meg van adva → **bináris label (0/1)** = trade/no-trade
  - Case 1 (nincs side): bin in (-1,1) = irány label
  - Case 2 (side megadva): bin in (0,1) = **meta-label** (felül/fölérendelt modell)
- `barrier_touched()`: top=1, bottom=-1, vertical=0

### 3. Saját MT5_LGBM_TRIPLE_BARRIER_WORKFLOW.md (score: 0.55)
Már megtervezve: M5 + triple barrier + 150+ indikátor + >55% accuracy cél

## Gyökérok azonosítva

**A mi irány-feature-ink ATR-normalizáltak voltak:**
```python
Bar_Direction = (close - open) / (atr_m15 + 1e-9)      # ATR normalizált!
Mom5_Direction = (close - close.shift(5)) / (atr_m15 * 5)  # ATR normalizált!
```

**Probléma**: ATR normalizálás megöli a magnitúdó információt:
- Magas ATR (volatil) → feature érték kicsi még nagy mozgásnál
- Alacsony ATR (csendes) → feature érték nagy kis mozgásnál
- LightGBM nem tud konzisztens küszöböt tanulni

## Implementált javítás

**18 új feature hozzáadva** (`dom_feature_engineer_mtf.py` H. szekció):
- `PastRet_1,2,3,5,10` — nyers % return (ATR nélkül)
- `PastLogRet_1,2,3,5,10` — nyers log return
- `MomScore_14` — regresszió slope × R² (trend erő + irány)
- `Slope_Close_14` — 14-bar linear regression slope
- `AccRet_3` — 3-bar cumulative return
- `RetAccel_1` — return gyorsulás

## V17 eredmények (V6 labeling + 114 feature)

| Feature | SHAP_Total | SHAP_Short | SHAP_Long | L_minus_S |
|---------|-----------|-----------|----------|-----------|
| ATR_Micro | 0.433 | 0.104 | 0.094 | -0.010 |
| Slope_Close_14 | **0.057** | 0.021 | 0.013 | -0.008 |
| RetAccel_1 | 0.027 | 0.011 | 0.007 | -0.002 |
| MomScore_14 | 0.024 | 0.011 | 0.006 | -0.001 |
| PastLogRet_2 | 0.022 | 0.005 | 0.007 | +0.002 |
| PastRet_3 | 0.020 | 0.010 | 0.004 | -0.002 |
| PastLogRet_1 | 0.019 | **0.012** | 0.003 | **-0.009** |

**Eredmények:**
- `Slope_Close_14` bekerült top 10-be! (SHAP=0.057)
- `PastLogRet_1` első irány-diszkrimináló feature (L_minus_S=-0.009)
- Opposite: 43.5% (V13: 42%)
- Win rate: 46.5%
- ATR_Micro továbbra is #1 (Noise-specifikus, SHAP_Noise=0.234)

## Következő lépések

1. **SHAP prune V18** (top 30 feature) — az új feature-ökkel
2. **Meta-labeling**: Elsődleges modell = egyszerű irány szabály, másodlagos = trade/no-trade
3. **--short_zero** teszt: Long-only baseline az új feature-ökkel
