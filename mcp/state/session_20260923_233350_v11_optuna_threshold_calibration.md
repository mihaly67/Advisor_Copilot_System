# Session: v11_optuna_threshold_calibration
*Időbélyeg: 2026-09-23T23:33:50.046574*

V11 Optuna threshold calibration complete.

GPU: P4000 OpenCL setup done (nvidia-opencl-icd 580.178.04, LightGBM device='gpu').

Optuna results (2 runs, 200+200 trials each):
Run 1 (th_short 0.40-0.75): Long 0% opposite, Short 38.1% opposite, total 14.2% opposite, -32$ profit
Run 2 (th_short 0.55-0.75): Long 0% opposite, 0 Short trades (too high threshold), -12.8$ profit

Key thresholds: th_long=0.598, th_noise_long=0.502, th_short=0.718 (effectively Long-only)

Model files:
- /data/dev/projects/z-ai-copilot/models/lgbm_model_v5_adaptive.pkl (V11 GPU trained)
- /data/dev/projects/z-ai-copilot/models/optuna_thresholds_asymmetric_v9.json (calibrated thresholds)

Findings:
- Long threshold calibration is PERFECT: 0% opposite in both runs
- Short side fundamentally broken: model rarely gives Short prob > 0.55
- 40% win rate insufficient (break-even at 45.5% with LW=1.2/LL=-1.0)
- Need either: meta-labeling, higher reward ratio, or better labeling

Next steps options:
1. Meta-labeling (second model to filter trades) — most promising
2. Adjust reward structure (LW=2.0 → break-even 33.3%)
3. Long-conditional labeling (Long preferred when above EMA50)
4. Accept Long-only strategy with 0% opposite