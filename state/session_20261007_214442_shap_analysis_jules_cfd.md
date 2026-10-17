# Session: shap_analysis_jules_cfd
*Időbélyeg: 2026-10-07T21:44:42.340935*

SHAP ANALYSIS - Jules CFD CORRECT — 2026-10-07

KULCS FELISMERES: A modell NEM ad ellentetes jeleket!
- Long jelek ahol Short SHAP > Long SHAP: 0 (0.0%)
- Short jelek ahol Long SHAP > Short SHAP: 3 (0.2%)

DE: feature-onkent VAN rossz iranyu huzas (30-50%):
- Stoch_State_M1: Long-ban 712/1526 (46.7%) huz Short-ot!
- Upper_Wick_ATR: Long-ban 700/1526 (45.9%) huz Short-ot!
- Dist_Micro_S: Long-ban 758/1526 (49.7%) huz Short-ot!
- Dist_Sec_S: Short-ban 837/1599 (52.3%) huz Long-ot!
- Dist_Ter_R: Long-ban 603/1526 (39.5%) es Short-ban 677/1599 (42.3%)

GLOBAL IMPORTANCE:
- Long: Tick_Speed=21.6%, Dist_Ter_S=14.0%, Dist_Sec_S=12.0%
- Short: Tick_Speed=17.1%, Dist_Sec_R=13.1%, Dist_Micro_R=13.1%

DIAGNOSZTIS: A feature-k NEM iranytudjak!
- Egy feature 30-50% esetben ROSSZ iranyba huz
- De a TENYESZI modell kimenet nem ellentetes (0% Long-Short swap)
- Ez azt jelenti: a feature-k ZAJT adnak, de a LGBM tanulta kompenzalni

FILES:
- Script: /data/dev/projects/z-ai-copilot/src/shap_jules_cfd.py
- Beeswarm Long: /data/dev/projects/z-ai-copilot/docs/jules_cfd/shap_beeswarm_long.png
- Beeswarm Short: /data/dev/projects/z-ai-copilot/docs/jules_cfd/shap_beeswarm_short.png
- Bar comparison: /data/dev/projects/z-ai-copilot/docs/jules_cfd/shap_bar_long_vs_short.png