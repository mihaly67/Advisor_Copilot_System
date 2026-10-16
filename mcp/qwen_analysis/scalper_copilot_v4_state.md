# Scalper Copilot v4.0 — Állapotjelentés 2026-10-15

## Feladat
BTCUSD Scalper Copilot v4.0 — multi-horizon (1-3 min) advisory probability pipeline.
NEM robot — tanácsadó copilot. P(Long)/P(Short) valószínűséget ad.

## Verzió történet és AUC összehasonlítás

| Verzió | Feature-k | CV | Reg | 2min L | 2min S | Megjegyzés |
|--------|-----------|-----|-----|--------|--------|------------|
| **V1 (első)** | 35 | KFold(5) | 0.05/0.3 | **0.653** | 0.629 | Legjobb Long, de mean-rev bias |
| V2 | 55→51 | KFold(5) | 0.05/0.3 | 0.649 | 0.631 | +Direction/ICT/Session/VP |
| V3 | 51→22 | WF(5) | 0.15/0.6 | 0.571 | 0.556 | WF valós, chart üres! |
| V4 | 51→22 | KFold(5) | 0.1/0.5 | 0.639 | **0.652** | +HTF Trend Gate |
| V5 | 51→22 | KFold(5) | 0.1/0.5 | 0.639 | 0.652 | HTF EMA bias (KÉSIK!) |
| **V6 (jelenlegi)** | 51→22 | KFold(5) | 0.1/0.5 | 0.639 | 0.652 | CUSUM Direction Bias |

## Jelenlegi pipeline (V6)

### Feature-k (51 összesen, feature selection → 22-23 per horizon)

**Eredeti 35:**
body, upper_wick, lower_wick, bar_range, ret_1-20, rv_5-60, skew_20-60,
rpos_10-60, vol_rel, vol_ma_5-20, vol_ret_5, ema_d_10-60, rsi_14-28,
bar_dt, bar_dt_rel, cum_dir_5-10, atr_pct, noise_class

**Új 16 direction/ICT/session/VP:**
df_curve (CUSUM), flow_delta, pv_corr, mom_persistence, vol_adj_mom,
variance_ratio, fvg_signal, fvg_size, ob_signal, liq_sweep_net,
kill_zone_london/ny/overlap, hour_sin, htf_trend, poc_dist

### Direction Bias (inference időben, nem tréningben!)

```
dc_z = (df_curve / rolling_std).clip(-3, 3)         # CUSUM z-score
vam_z = (vol_adj_mom / rolling_std).clip(-3, 3)     # momentum z-score
trend_strength = ((mom_persistence - 0.5) * 4).clip(0, 1)  # persistence gate
direction = (dc_z × 0.5 + vam_z × 0.3) × (0.3 + 0.7 × trend_strength)
bias = clip(direction × 0.15, -0.25, +0.25)
P(Long)  += bias
P(Short) -= bias
```

Miért CUSUM és nem EMA: nem késik, auto-reset trendváltáskor

### Modell paraméterek
```python
LightGBM: num_leaves=31, lr=0.03, feat_frac=0.8, bag_frac=0.7,
reg_alpha=0.1, reg_lambda=0.5, is_unbalance=True
5-fold CV, early_stopping=50, feature_selection min_pct=0.5%
```

### Top Feature-k (2min Long)
rv_60, bar_dt, hour_sin, skew_60, poc_dist, bar_dt_rel, htf_trend, pv_corr

## Fájlok

| Fájl | Leírás |
|------|--------|
| `/data/LGBM_copilot/src/scalper_copilot_v4.py` | Pipeline (tanítás + predikció + bias) |
| `/data/LGBM_copilot/src/scalper_copilot_chart.py` | 2min chart (1 nap, Plotly) |
| `/data/LGBM_copilot/src/scalper_copilot_chart_mh.py` | 3-horizon chart (1/2/3 min ablak) |
| `/data/LGBM_copilot/models/scalper/BTCUSD_v4_*_20261015_012135.*` | Modellek, meta, predikció |
| `/data/LGBM_copilot/charts/BTCUSD_copilot_v4_2026-10-07.html` | Chart (1.5MB) |

## Problémák amik még vannak

1. **Fa alapból mean-revert** — a CUSUM bias javított, de a fa magatartása nem változott
2. **KFold AUC overfittelt** — valós WF AUC 0.55-0.58 (KFold 0.65 illúzió)
3. **Túl kevés adat** — 4 nap külön vizsga, full dataset elérhető (--full)

## Következő lépések (prioritás sorrendben)

1. **Meta-labeling** (tudástár: digest_meta_labeling.md)
   - Primary: side model (+1/-1) — a jelenlegi modell
   - Meta: filter model P(correct|side) — csak profitábilis trade-k
   - Ez szűri a mean-reversion false szignálokat!

2. **Aszimmetrikus TP/SL labeling** (tudástár: digest_triple_barrier.md)
   - Trend-following: profit_mult=2.0, stop_mult=1.0
   - Ez megtanítja a fának, hogy trendben hagyni kell futni a profitot

3. **CUSUM filter sampling** (tudástár: digest_triple_barrier.md §8)
   - Ne minden bar-on tanítsunk, csak CUSUM event bar-okon
   - Ez eltávolítja a zajszintű neutral bar-okat

4. **Több adat** — --full flag a teljes dataset-re
5. **Sample weights** (AFML Ch.4) — időben távolság alapú súlyozás
6. **Meta-model position sizing** (tudástár: signal_filter_alpha.py)
   - P(take) alapú sizing: margin = max(0, P(take) - max(P(skip), P(fade)))
