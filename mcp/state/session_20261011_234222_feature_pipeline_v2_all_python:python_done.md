# Session: feature_pipeline_v2_all_python:python_done
*Időbélyeg: 2026-10-11T23:42:22.788465*

LGB Copilot BTCUSD — FEATURE PIPELINE V2 (MINDEN PYTHON, Bar_Sign SZŰRŐ)

## 37 FEATURE, MINDEN PYTHON (NINCS EA S/R merge!)

### Bar_Sign SZŰRŐ (+1 növekedés / -1 csökkenés):
- Bar_Sign = -1 (csökkenés) → P(Long) = 0 (NEM Long!)
- Bar_Sign = +1 (növekedés) → P(Short) = 0 (NEM Short!)
- Kizárja trenddel szembeni predikciót
- +1 = 167,480 (50.4%)  -1 = 165,162 (49.6%) — kiegyensúlyozott

### Feature kategóriák:
1. Bar_Sign (1) — SZŰRŐ
2. Bar morphológia (5): Bar_Direction, Bar_Body_Ratio, Wick_Upper/Lower_Ratio
3. ATR-normalizált (2): Return_1bar, High_Low_ATR
4. RSI (1): Micro_RSI_14
5. EMA (3): Trend_EMA_Fast/Medium/Slow_Dist
6. Momentum (3): Mom_3, Mom_5, Mom_10
7. Velocity (2): Price_Velocity, Pulse_DF_Curve
8. CUSUM (2): CUSUM_Direction, CUSUM_x_Bar
9. Meta (4): Run_Length, Duration_Sec, Num_Ticks, Tick_Speed
10. Swing S/R Python (6+3=9): Dist_Micro/Sec/Ter_R/S_ATR + Micro/Sec/Ter_R/S
11. Pivot Python (3): pivot_dist, delta_pivot_dist, above_pivot

### Pivot minőség:
- pivot_dist: mean=0.016 std=1.549
- delta_pivot_dist: ρ₁=-0.328 (alacsony AC, jó!)
- above_pivot: 48.5% above / 51.5% below

### TRAIN/SERVE SKEW = 0:
- MINDEN feature Python-ból, dollár bar OHLC-ből
- compute_swing_sr() offline = online
- EA S/R KIVEVE (distribution shift veszély!)
