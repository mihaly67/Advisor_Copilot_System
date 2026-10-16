# Predict Logger V1 — BTCUSD Élő Diagnózis

**Dátum**: 2026-10-11 17:41 UTC
**Fájl**: `/data/dev/projects/z-ai-copilot/src/predict_logger.py`
**CSV**: `/tmp/btcusd_predict_log.csv` + `/tmp/btcusd_feature_log.csv`

## Státusz: ✅ FUT

## Élő Predikciók (7 bar)

| Idő | Ár | MLP | LGBM | ENS | Signal |
|-----|-----|-----|------|-----|--------|
| 18:33 | 83169.98 | 0.198 | 0.167 | 0.189 | 🔴 SHORT |
| 18:34 | 83127.32 | 0.209 | **0.481** | 0.291 | 🔴 SHORT |
| 18:35 | 83193.09 | 0.131 | **0.479** | 0.236 | 🔴 SHORT |
| 18:36 | 83177.73 | 0.215 | 0.256 | 0.227 | 🔴 SHORT |
| 18:37 | 83184.28 | 0.175 | 0.178 | 0.176 | 🔴 SHORT |
| 18:38 | 83219.81 | 0.127 | 0.119 | 0.125 | 🔴 SHORT |
| 18:39 | 83222.22 | 0.358 | 0.283 | 0.335 | 🔴 SHORT |

## Diagnózis

### MLP: 🔴 KALIBRÁCIÓS HIBA
- Tartomány: [0.127 - 0.358], μ=0.202
- Soha nem éri el 0.5-öt
- RankGauss scaler rosszul transzformálja az élő adatot

### LGBM: 🟡 MAJDNEM JÓ
- Tartomány: [0.119 - 0.481], μ=0.280
- **Majdnem eléri 0.5-öt!** (0.481 @ 18:34)
- Mozgása nagyobb mint MLP-é
- w_lgbm = 0.30 → ha 1.0-re növeljük, a signal LONG is lehetne!

### ENS: 🔴 SHORT BIAS
- w_mlp=0.70 → MLP húzza le az ensemble-t
- Ha LGBM-only → signal változhatna

### Feature Drift
| Feature | Élő érték | Várható | Probléma |
|---------|----------|---------|----------|
| vol_ratio_f | 50.8 | [0,5] | 🚨 10x drift |
| Slope_3_atr_f | ±5.0 | [-2,2] | 🚨 clip határ |
| body_atr_f | 5.0 | [0,2] | 🚨 clip határ |
| velocity_atr_f | -5.0 | [-2,0] | 🚨 clip határ |

## EA Formátum (5556 port)
```
TICK|time_msc|bid|ask|pos_types|OHLC|PnL|0|0|0|0|0|0|0|0|R-mic|S-mic|R-sec|S-sec|R-ter|S-ter
```
- pos_types: `-1,-1,-1,-1` (vesszős)
- OHLC: `83054.78,83062.38,83061.84,83056.46` (előző bar)

## Következő lépések (prioritás sorrend)
1. **LGBM-only mód** — w_lgbm=1.0, signal = LGBM > 0.5 = LONG
2. **Feature clip lazítás** — ±5 → ±10
3. **Platt scaling** — kalibráció sigmoid után
4. **vol_ratio_f log transform** — np.log1p(vol_ratio)
5. **Scaler újra tanítás** — élő adaton
