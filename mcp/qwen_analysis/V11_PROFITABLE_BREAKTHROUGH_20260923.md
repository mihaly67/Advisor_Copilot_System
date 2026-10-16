# V11 PROFITABLE BREAKTHROUGH — Optuna + LW=2.0
*2026-09-23 23:39*

## Final Results (OOS Test Set, 6228 bars)

| Metrika | V9 eredeti | V11 + Optuna + LW=2.0 |
|---|---|---|
| Trades | ~3000 | 1379 |
| Win rate | ~33% | **43.1%** |
| **Opposite** | **30.7%** | **0.94%** (13/1379) |
| **Profit** | — | **+386.50$** |
| Avg/trade | — | +0.280$ |

## Long (domináns oldal):
- 1353 trades, 584 wins (43.2%), 3 opposite (0.2%)
- th_long=0.350, th_noise_long=0.202

## Short (marginal):
- 26 trades, 11 wins (42.3%), 10 opposite (38.5%)
- th_short=0.564, th_noise_short=0.577

## Thresholds (JSON):
```json
{
  "th_long": 0.350,
  "th_noise_long": 0.202,
  "th_short": 0.564,
  "th_noise_short": 0.577,
  "long_trades": 1353, "long_wins": 584, "long_opposite": 3,
  "short_trades": 26, "short_wins": 11, "short_opposite": 10,
  "total_profit": 386.5,
  "total_win_rate": 0.431,
  "total_opposite_rate": 0.009
}
```

## Key Insight: Reward Structure
- LW=1.2 → break-even 45.5% → 43% win rate = LOSS
- LW=2.0 → break-even 33.3% → 43% win rate = PROFIT
- Profit = 0.431×2.0 + 0.569×(-1.0) = +0.293/trade (excl opposite)

## Reward config:
```python
LW, LL = 2.0, -1.0   # Long win/loss (break-even 33.3%)
SW, SL = 2.0, -1.0   # Short win/loss
OPP = -1.5            # opposite penalty
```

## Architecture Summary:
1. Dollar Bar aggregáció ($444k küszöb)
2. 8 microstructure features (VPIN, Kyle Lambda, Roll Spread, etc.)
3. 8 regime features (EMA50, ADX, Z-score, slope, momentum, context)
4. Regime-conditional labeling: Short only when ADX<20
5. LightGBM GPU (P4000 OpenCL), class_weight={0:1.5, 1:0.5, 2:1.3}
6. 31 features total
7. Optuna 2-phase asymmetric threshold calibration (200+200 trials)
8. LW=2.0 reward structure

## Files:
- Model: /data/dev/projects/z-ai-copilot/models/lgbm_model_v5_adaptive.pkl
- Thresholds: /data/dev/projects/z-ai-copilot/models/optuna_thresholds_asymmetric_v9.json
- Trainer: /data/dev/projects/z-ai-copilot/src/train_lgbm_fusion_v5.py
- Optuna: /data/dev/projects/z-ai-copilot/src/optuna_asymmetric_v9.py
