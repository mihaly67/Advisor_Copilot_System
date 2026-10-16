# Session: shap_analysis
*Időbélyeg: 2026-10-05T00:07:22.095247*

SHAP ANALYSIS KÉSZ.

TOP 10 FEATURES (átlagos |SHAP| mindhárom osztályból):
1. Dist_Micro_R  all=0.085  L=0.133 S=0.072 N=0.051 ← LEGFONTOSABB
2. Dist_Micro_S  all=0.075  L=0.090 S=0.101 N=0.033
3. Tick_Speed    all=0.069  L=0.042 S=0.034 N=0.130 ← NOISE dominál
4. Dist_Ter_S    all=0.060  L=0.033 S=0.047 N=0.100
5. Dist_Ter_R    all=0.053  L=0.040 S=0.030 N=0.090
6. Dist_Sec_R    all=0.040  L=0.038 S=0.035 N=0.048
7. Dist_Sec_S    all=0.037  L=0.037 S=0.042 N=0.033
8. Stoch_State_M1 all=0.023 L=0.024 S=0.031 N=0.014 ← GYENGE
9. Upper_Wick_ATR all=0.012 L=0.012 S=0.013 N=0.012
10. Lower_Wick_ATR all=0.012 L=0.013 S=0.011 N=0.012

SHAP IRÁNY:
- Long: Tick_Speed++ (gyorsabb=Long), Dist_Sec_R++ (távolság R=Long), Dist_Micro_S++ (micro S=Long)
- Short: Dist_Sec_S++ (távolság S=Short), Dist_Ter_S++ (ter S=Short), Dist_Micro_S-- (micro S↓=Short)

FONTOS: Stoch_State_M1 csak 8. (0.023) — igazolja hogy Stoch szűrés kikapcsolása jó döntés!

Kimenet: /data/dev/projects/z-ai-copilot/docs/v110/shap_heatmap.png (91KB)
         shap_bar_overall/short/noise/long.png
         shap_summary_short/noise/long.png