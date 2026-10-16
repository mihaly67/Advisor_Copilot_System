# Session: copilot_v4_multi_horizon_done
*Időbélyeg: 2026-10-14T19:02:44.168555*

SCALPER COPILOT v4.0 — MULTI-HORIZON PIPELINE KÉSZ (2026-10-14)

## Amit építettünk
BTCUSD Scalper Copilot v4.0 — tanácsadó (nem robot!)
3 horizont (60s, 120s, 180s) × 2 irány (Long, Short) = 6 LightGBM modell

## Modell eredmények
| Horizon | Long AUC | Short AUC | Long thr_ad | Short thr_ad |
|---------|----------|-----------|-------------|--------------|
| 1min    | 0.5937   | 0.6022    | 0.201       | 0.443        |
| 2min    | 0.6529   | 0.6290    | 0.403       | 0.362        |
| 3min    | 0.6024   | 0.6040    | 0.382       | 0.382        |

A 2min a legjobb horizont! (Long AUC=0.653, Short AUC=0.629)

## Címkézés
- Dollar bar: $10M threshold → 68717 bars
- TP=$50 szimmetrikus, SL=$50
- 1min: Long 18.2%, Short 19.7%, Neutral 62.1%
- 2min: Long 29.0%, Short 31.2%, Neutral 39.8%
- 3min: Long 35.3%, Short 37.7%, Neutral 27.0%

## Top 5 features (minden horizont)
rv_60 (60-bar realized vol), bar_dt (bar time delta), bar_dt_rel, rv_20, skew_60

## Zaj szint
- Noise = ATR(14)/Close → mean=0.0001 (dollar bar-okon)
- Adaptív threshold = base_thr * (1 + noise * 50)
- Mivel noise nagyon alacsony, adaptive ≈ base

## Fájlok
- /data/LGBM_copilot/src/scalper_copilot_v4.py — training pipeline
- /data/LGBM_copilot/src/scalper_copilot_chart.py — interaktív HTML chart
- /data/LGBM_copilot/models/scalper/BTCUSD_v4_*_20261014_185802.* — 6 modell + meta
- /data/LGBM_copilot/charts/BTCUSD_copilot_v4_2026-10-0{5,6,7}.html — 3 nap vizualizáció

## Chart felépítés
- FELSŐ ablak (70%): Candlestick OHLC + Long ▲ / Short ▼ jelzések + noise szint sáv
- ALSÓ ablak (30%): 3 sáv (1min/2min/3min)
  - Minden sáv: P(Long) zöld, P(Short) piros, threshold szaggatott, noise vonal szürke
- Plotly.js standalone, dark theme, interaktív zoom/pan

## Következő lépések
1. Noise level javítás: tick-alapú ATR használata dollar bar ATR helyett
2. ICT features integráció (FVG, OrderBlock, LiqSweep) a tudástárból
3. VolumeA Profile POC feature hozzáadás0. Volume Profile P(POC feature hozzáadás
4. Session/KillZone time-of-day feature
5. Walk-forwardA validáció (time-based split)
6. Signal quality pipeline: multi-confirmation, fresh trigger, cooldown