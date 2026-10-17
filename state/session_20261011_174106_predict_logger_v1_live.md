# Session: predict_logger_v1_live
*Időbélyeg: 2026-10-11T17:41:06.844182*

# Predict Logger V1 — KÉSZ ÉS FUT!

## Fájl: /data/dev/projects/z-ai-copilot/src/predict_logger.py (~335 sor)
## PID: futásban (nohup), log: /tmp/predict_logger.out

## Indítás:
```bash
cd /data/dev/projects/z-ai-copilot/src
nohup python3 predict_logger.py BTCUSD > /tmp/predict_logger.out 2>&1 & disown
```

## Log fájlok:
- `/tmp/btcusd_predict_log.csv` — minden bar completion 1 sor (idő, ár, MLP, LGBM, ENS, signal, conf, top5 features)
- `/tmp/btcusd_feature_log.csv` — minden feature érték bar-onként (feature drift elemzéshez)
- `/tmp/predict_logger.out` — konzol output (BAR, STAT, hibák)

## CSV oszlopok:
time, time_str, bar_n, price, p_mlp, p_lgbm, p_ens, signal, ml_dir, conf,
lgbm_long, lgbm_short, p_mlp_ema10, p_lgbm_ema10, p_ens_ema10,
p_mlp_range50, p_lgbm_range50, p_ens_range50, top5_feat, top5_contrib,
feat_min, feat_max, feat_mean

## EA formátum (5556 Tick port):
TICK|time_msc|bid|ask|pos_types|OHLC|PnL|0|0|0|0|0|0|0|0|R-mic|S-mic|R-sec|S-sec|R-ter|S-ter
- pos_types: "-1,-1,-1,-1" (vesszős, fixelve)
- OHLC: "83054.78,83062.38,83061.84,83056.46" (vesszős, fixelve)

## Javítások ezen a verzión:
1. MIN_BARS_FOR_PREDICT: 20→10 (seed után azonnal predikció)
2. CSV seed: dollar_bars_full_BTCUSD.csv utolsó 200 bar buffer seed
3. 5555 JSONDecodeError: bid,ask formátum fallback
4. 5556 TICK parser: pos_types (vesszős), pos_price/OHLC (vesszős), P&L (vesszős) fix
5. RAW debug log: első 3 üzenet portonként

## Élő eredmények (7 bar, 18:33-18:39 UTC):
- MLP: [0.127-0.358] μ=0.202 — soha > 0.5
- LGBM: [0.119-0.481] μ=0.280 — MAJDNEM eléri 0.5-et!
- ENS: [0.125-0.335] μ=0.225 — mindig SHORT

## Feature Drift — fő ok:
- vol_ratio_f = 50.8 (élő) vs [0,5] (tanítási) → 10x drift
- Slope_3_atr_f = ±5.0 (clip határ)
- body_atr_f = 5.0 (clip határ)
- velocity_atr_f = -5.0 (clip határ)
- vol_ratio_f dominál: contribution = 498

## Következő lépések:
1. Több bar (30+) → LGBM tartomány stabilizálódik?
2. Feature clip lazítás ±5→±10 vagy log transform vol_ratio
3. LGBM-only mód (w_lgbm=1.0) teszt
4. Platt scaling / isotonic regression kalibráció
5. Scaler újra tanítás élő adaton
