# BTCUSD Scalper Copilot v4.0 — Összefoglaló

## Dátum: 2026-10-14

## Amit építettünk
BTCUSD Scalper Copilot v4.0 — tanácsadó (NEM robot!)
3 horizont (60s/120s/180s) × 2 irány (Long/Short) = 6 LightGBM modell

## Modell eredmények
| Horizon | Long AUC | Short AUC | L thr_ad | S thr_ad | Label Long% | Label Short% |
|---------|----------|-----------|----------|----------|-------------|--------------|
| 1min    | 0.594    | 0.602     | 0.212    | 0.467    | 18.2%       | 19.7%        |
| 2min    | **0.653**| **0.629** | 0.425    | 0.382    | 29.0%       | 31.2%        |
| 3min    | 0.602    | 0.604     | 0.403    | 0.403    | 35.3%       | 37.7%        |

**Legjobb horizont: 2min** (Long AUC=0.653, Short AUC=0.629)

## Top 5 features (minden horizont)
1. rv_60 — 60-bar realized volatilitás
2. bar_dt — bar idő-delta (milyen sűrűn jön bar)
3. bar_dt_rel — bar_dt relatív az átlaghoz
4. rv_20 — 20-bar realized volatilitás
5. skew_60 — 60-bar return ferdeség

## Zaj szint
- Noise = max(realized_vol_60, ATR_pct) — normalizált volatilitás
- Mean: 0.0012, Std: 0.0004
- Low (<0.002): 96.2%, Medium: 3.7%, High (>0.005): 0.1%
- Adaptív threshold = base_thr × (1 + noise × 50)

## Chart
- Felső ablak: Candlestick OHLC + Long ▲ / Short ▼ + noise sáv
- Alsó ablak: 3 sáv (1min/2min/3min) P(Long)/P(Short) + threshold + noise vonal
- Plotly.js standalone, dark theme, interaktív
- 4 nap generálva: 2026-10-05 → 2026-10-08

## Fájlok
- Pipeline: /data/LGBM_copilot/src/scalper_copilot_v4.py
- Chart: /data/LGBM_copilot/src/scalper_copilot_chart.py
- Modellek: /data/LGBM_copilot/models/scalper/BTCUSD_v4_*_20261014_190329.*
- HTML: /data/LGBM_copilot/charts/BTCUSD_copilot_v4_2026-10-0{5,6,7,8}.html
