# Session: v11_profitable_breakthrough
*Időbélyeg: 2026-09-23T23:39:57.812990*

V11 + Optuna + LW=2.0 BREAKTHROUGH: PROFITABLE STRATEGY!

Thresholds: th_long=0.350, th_noise_long=0.202, th_short=0.564, th_noise_short=0.577

Results on OOS test set (6228 bars, 20% of data):
- Long: 1353 trades, 584 wins (43.2%), 3 opposite (0.2%)
- Short: 26 trades, 11 wins (42.3%), 10 opposite (38.5%)
- Total: 1379 trades, 595 wins (43.1%), 13 opposite (0.94%)
- Profit: +386.50$ | Avg/trade: +0.280$

Evolution:
V9: 30.7% opposite, ~33% win rate, unprofitable
V11 (regime labeling): 18.6% opposite, 46.8% accuracy
V11 + Optuna + LW=2.0: 0.94% opposite, 43.1% win rate, +386.5$ profit

Key insight: LW=1.2→2.0 reward adjustment lowered break-even from 45.5% to 33.3%, making 43% win rate profitable.

Short side negligible (26 trades vs 1353 Long). Long-only would be +394.5$ (slightly better).

Files:
- Model: /data/dev/projects/z-ai-copilot/models/lgbm_model_v5_adaptive.pkl
- Thresholds: /data/dev/projects/z-ai-copilot/models/optuna_thresholds_asymmetric_v9.json
- Trainer: /data/dev/projects/z-ai-copilot/src/train_lgbm_fusion_v5.py (GPU, 31 features)
- Optuna: /data/dev/projects/z-ai-copilot/src/optuna_asymmetric_v9.py (LW=2.0, 31 features)