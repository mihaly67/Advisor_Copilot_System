# Session: jules_cfd_v3_complete
*Időbélyeg: 2026-10-07T22:11:42.084120*

## Jules CFD v3 Pipeline - COMPLETE

### Changes from v2 (correct) to v3:
1. **Wick KI** (Upper_Wick_ATR, Lower_Wick_ATR) - removed, not significant, noise
2. **Stoch KI** (Stoch_State_M1) - removed, anti-directional on CFD
3. **Micro 2x suly → Ter 2x suly** - SHAP shows Ter_R best S/R for Long (32.9% wrong vs Micro_R 52%)
4. **Derived direction features added from NavSystem indicators**:
   - Pulse_DF_Curve (2nd derivative, price acceleration) - #1 feature by importance!
   - Pulse_MACD_Hist (momentum direction)
   - Price_Velocity (1st derivative, price speed)
   - Flow_Delta_10 (volumetric flow, buy vs sell)
   - Trend_EMA_Fast_Dist / Trend_EMA_Medium_Dist (trend direction)
   - Micro_RSI_14 (overbought/oversold)
5. Z-score normalization for extreme features (DF_Curve, Flow_Delta, MACD_Hist, RSI)

### Results:
| Verzió | OOS WR | VIZSGA WR | Long WR (OOS) | Short WR (OOS) |
|--------|--------|-----------|---------------|----------------|
| v2 (correct) | ~43% | ~43% | - | - |
| v3 (Micro 2x) | 48.0% | 49.4% | 44.3% | 50.4% |
| v3 (Ter 2x) | 48.1% | 50.4% | 45.2% | 50.3% |

### SHAP v3 findings:
- Pulse_DF_Curve: 25.8% wrong direction Long - BEST direction consistency
- Dist_Ter_R: 32.9% wrong Long - best S/R feature for Long
- Micro_RSI_14: 62% wrong Short - problematic for Short signals
- Dist_Micro_R: 52% wrong Long - worst S/R feature

### Feature importance (LGBM):
1. Pulse_DF_Curve 9.67%
2. Dist_Ter_S 7.63%
3. Dist_Ter_R 7.35%
4. Dist_Sec_S 6.85%
5. Dist_Sec_R 6.78%

### Files:
- `/data/dev/projects/z-ai-copilot/src/jules_cfd_v3.py` - main pipeline
- `/data/dev/projects/z-ai-copilot/src/viz_jules_cfd_v3.py` - visualization
- `/data/dev/projects/z-ai-copilot/src/shap_jules_cfd_v3.py` - SHAP analysis
- `/data/dev/projects/z-ai-copilot/models/jules_cfd/lgbm_jules_cfd_v3.pkl` - model
- `/data/dev/projects/z-ai-copilot/docs/jules_cfd/OOS_Jules_CFD_v3.html` - 503 KB
- `/data/dev/projects/z-ai-copilot/docs/jules_cfd/VIZSGA_Jules_CFD_v3.html` - 742 KB
- `/data/dev/projects/z-ai-copilot/docs/jules_cfd/shap_v3_beeswarm_long.png`, `shap_v3_beeswarm_short.png`, `shap_v3_bar_long_vs_short.png`