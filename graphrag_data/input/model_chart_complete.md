# Működő Modell + Chart + Predictor — Complete
**Dátum:** 2026-10-13

## Eredmények

### Modell
| Metrika | Érték |
|---------|-------|
| Instrument | BTCUSD |
| AUC | 0.515 |
| Accuracy | 55.6% |
| Take rate | 38.15% |
| Events | 10,585 |
| Features | 33 |
| Training data | 110K M1 bars (2.5 hónap) |
| Side model | RSI momentum |

### Pipeline Chain
1. Scalper EA MTF data → CSV
2. Resample 1min + MTF indicators
3. RSI momentum side model
4. Triple Barrier meta-labeling (PT=2σ, SL=1σ)
5. 33 MTF features
6. Sample weights (vectorized)
7. LightGBM 5-fold CV
8. Model + chart + predictor export

### Fájlok
- `src/train_mtf_v3.py` — teljes pipeline
- `src/copilot_chart.py` — ár + P(Take) chart
- `src/copilot_predict.py` — EA predictor
- `models/BTCUSD_mtf_model_*.txt` — LightGBM modell
- `models/BTCUSD_ea_config.json` — EA integráció
- `charts/BTCUSD_copilot_*.png` — chart
