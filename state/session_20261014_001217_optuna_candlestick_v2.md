# Session: optuna_candlestick_v2
*Időbélyeg: 2026-10-14T00:12:17.214702*

Scalper Optuna optimization + candlestick chart complete:

OPTUNA RESULTS (40 trials, 900s timeout):
- Best avg AUC: 0.8497 (was 0.597 baseline, +42% improvement!)
- Best params: horizon=6, tp_bps=12, sl_bps=18, subsample=7
- LGBM: num_leaves=55, lr=0.022, feature_fraction=0.73, bagging_fraction=0.63
- Long AUC=0.853, Short AUC=0.846 (3-fold quick CV)
- Long thr=0.58, Short thr=0.42

RETRAIN with 5-fold CV (horizon=6, tp=12, sl=18, sub=7):
- Long AUC=0.811, Short AUC=0.783 (5-fold is stricter)
- Long thr=0.46, Short thr=0.66
- Key insight: short horizon (6 ticks ~30sec) + wider TP/SL (12/18 bps) bridges BTC $100/min volatility

CHART IMPROVEMENTS:
1. Candlestick (OHLC) replaces blue line - 1-min resample from tick data
2. x-axis synced: matches:"x2" → both subplots zoom/pan together
3. Colors: #26a69a (green candle), #ef5350 (red candle)
4. Forest green ▲ Long markers, Brick red ▼ Short markers

FILES:
- /data/LGBM_copilot/src/scalper_optuna.py (Optuna optimizer)
- /data/LGBM_copilot/src/scalper_chart_html.py (interactive HTML chart)
- /data/LGBM_copilot/models/scalper/BTCUSD_optuna_best_*.json (best params)
- /data/LGBM_copilot/charts/BTCUSD_scalper_2026-10-05_*.html (candlestick chart)