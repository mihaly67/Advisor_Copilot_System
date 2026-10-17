# Session: iranylatas_noise_blokkolas_nav_3c_v1.01_20260924_2118
*Időbélyeg: 2026-09-24T21:21:56.452229*

# IRÁNYLÁTÁS + NOISE BLOKKOLÁS ANALÍZIS — nav_3c_v1.01 (2026.09.24. 21:18)

## 🎯 FŐ FELISMERÉS: Modell 93.1%-ban LÁTJA az irányt — de Noise blokkolja!

### Számok:
- Irány látás: 2944/3162 = 93.1% (P_Long>P_Short amikor actual Long, vagy fordítva)
- Noise blokkol (P_Noise>0.50): 1419/2944 = 48.2% → fele blokkolva!
- P_Noise > 0.30: 95.4% (szinte mindig magas)
- P_Noise > 0.40: 81.5%
- P_Noise > 0.55: 27.1%
- P_Noise > 0.60: 12.0%

### Blocked vs Unblocked indikátor minta:
- BLOCKED (P_Noise>0.50): indikátorok ~50 körül (semleges)
  - Micro_RSI_14=52.0, Stoch_D=55.4, WPR_14=-44.6, RSI_Fast_5=52.8
- UNBLOCKED (P_Noise<=0.50): indikátorok EXTREMEBB
  - Micro_RSI_14=48.3, Stoch_D=46.6, WPR_14=-53.6, RSI_Fast_5=47.6

### Kulcs felismerés: "Indikátor közép = Noise blokkolás"
- 48% Noise label → modell Noise-t tanult alapértelmezettnek
- Csak EXTREM indikátor értéknél küzdi le a Noise priort
- De mire indikátorok extrémre érnek → trend már 73% lefutott!

### Indikátor paraméterek:
- Pulse_MACD_Hist: MACD(15,5,5) — gyors MACD
- Stoch: Stochastic(14,3) — 14 bar lookback, 3 bar smooth
- WPR_14: Williams %R(14) — 14 bar
- RSI_Fast_5: RSI(5) — nagyon gyors
- Micro_RSI_14: RSI(14) — standard
- RSI_M15: RSI M15 timeframe (MQ5) — lassú

### Generált fájlok:
1. docs/heatmap_nav_3c_v1.01.html — korreláció heatmap
2. docs/indicator_dist_nav_3c_v1.01.html — blocked vs unblocked eloszlás
3. docs/indicator_timeseries_nav_3c_v1.01.html — 5-panel idősor
4. src/heatmap_nav_3c_v1.01.py — script

### Következő lépések:
1. th_noise 0.50 → 0.60 kipróbálása (csak 12% blokkolás)
2. Noise label arány csökkentése (48% → 35%?) → modell kevésbé Noise-biased
3. EMA simítás a P_Long/P_Short/P_Noise jeleken