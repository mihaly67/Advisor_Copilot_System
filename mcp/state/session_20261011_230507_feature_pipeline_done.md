# Session: feature_pipeline_done
*Időbélyeg: 2026-10-11T23:05:07.752341*

LGB Copilot BTCUSD — FEATURE PIPELINE KÉSZ

## ARCHITEKTÚRA: Hibrid dollár bar + Scalper S/R

### Dollár bar feature-ök [DB] — Python számolja (offline = online):
1. Bar_Direction, Bar_Body_Ratio, Wick_Upper/Lower_Ratio
2. Return_1bar, High_Low_ATR
3. Micro_RSI_14 (dollar bar RSI)
4. Trend_EMA_Fast/Medium/Slow_Dist (ATR-normalizált)
5. Mom_3, Mom_5, Mom_10 (ATR-normalizált momentum)
6. Price_Velocity, Pulse_DF_Curve
7. CUSUM_Direction, CUSUM_x_Bar
8. Run_Length, Duration_Sec, Num_Ticks, Tick_Speed

### Scalper S/R + MTF feature-ök [SR] — EA küldi (offline: CSV merge):
22. ATR_M15, RSI_M15
23-29. Dist_Micro/Sec/Ter_R/S_ATR (S/R távolság ATR-normalizálva)

### TRAIN/SERVE SKEW VÉDELEM:
- Offline: Scalper CSV → merge_asof backward (no lookahead)
- Online: EA tick-ben megjön ugyanaz a S/R + MTF
- → offline = online, NINCS skew!

### Eredmény:
332,642 bar × 29 feature (50.6s)
features_BTCUSD.csv mentve

### LOGIKA:
1. Dollár bar elkészül (tick-ekből, $1.04M threshold)
2. Dollár bar completion → feature számítás (Python)
3. S/R + MTF az EA-tól (offline: CSV merge)
4. LGBM predict → P(TP|Long), P(TP|Short)
5. HUD → trader látja
6. M1 gyertyazárás FÜGGETLEN — dollár bar az atomic unit!
