# Session: v11_shap_visualization_complete
*Időbélyeg: 2026-09-23T23:47:24.234046*

V11 SHAP + Visualization complete.

SHAP Top 5 features:
1. Regime_ADX (SHAP=1.128) — dominates Short side (2.523), regime-conditional labeling validates
2. Regime_Trending (0.356) — Short dominant (0.915)
3. ATR_Micro (0.075)
4. Regime_Slope (0.039)
5. Kyle_Lambda (0.028)

3 regime features in top 4 — regime-conditional labeling is the key architectural decision.

Feature pruning: 4 features to drop (Amihud_Illiq, Bar_Duration_Sec, RSI_Fast_5, WPR_14) — all redundant (|r|>0.85). Keep 27/31.

Visualization: predictions_visualization.html with Optuna thresholds applied (th_L=0.35, th_S=0.56). 543 Long, 38 Short, 1419 Noise signals on 2000-bar test set.

6 HTML files generated in /data/dev/projects/z-ai-copilot/docs/:
- shap_heatmap.html, shap_long_vs_short.html, shap_dependence_long.html
- shap_beeswarm.html, feature_correlation.html
- predictions_visualization.html

V11 pipeline complete: Dollar Bar → 31 features → regime labeling → GPU training → Optuna thresholds → SHAP validated → visualization.

All metrics: 43.1% win rate, 0.94% opposite, +386.5$ profit on OOS.