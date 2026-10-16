# Session: pred_inertia_analysis_nav_3c_v1.01_20260924
*Időbélyeg: 2026-09-24T20:37:32.438898*

# Predikció Tehetetlenség Analízis — nav_3c_v1.01

## Dátum: 2026.09.24.

## 🎯 Fő Eredmény: ~7 bar fáziskésés trendváltásra

### Statisztika (218 trend szegmens):
- lag_opp (ellentétes pred. meddig magas): 7.0 bar átlag, 8 medián
- lag_cor (helyes pred. meddig indul): 6.3 bar átlag, 8 medián
- pct_zero (helyes pred. nullán aktív trendben): 37.2% átlag
- max_pos (pred. maximum pozíciója a trendben): 0.73 → a trend 73%-ánál (VÉGE!)
- cor_end (trend végén helyes pred.): 0.475 (nem tér vissza nullára)
- opp_end (trend végén ellentétes pred.): 0.039 (végre nulla)
- pct_noise (Noise dominancia): 58.8%
- pct_opp (ellentétes > 0.20): 44.3%

### A ciklus amit a felhasználó leírt — MIND bizonyítva:
1. Trend kezdete → ellentétes pred. még 7 bar-ig magas
2. Helyes pred. 6.3 bar-ig nullán nem indul
3. 37%-ban a helyes pred. nullán (< 0.10) aktív trendben!
4. Pred. maximum a trend 73%-ánál = VÉGE FELE
5. P_Long csúcs 0.60 de P_Noise 0.40 > th_NL=0.30 → NO SIGNAL (blokkolva!)
6. Trend végén helyes pred. még 0.475 → lassan nullázódik új trendben

### Konkrét példa (DOWN trend 2026-09-01):
- Bar 0: P_Long=0.0002 (nullán!)
- Bar 27: P_Long=0.003 (MÉG nullán — 27 bar!)
- Bar 29: P_Long=0.207 (hirtelen ugrás!)
- Bar 31: P_Long=0.599 (CSÚCS! De P_Noise=0.40 → BLOCKED)
- Bar 32: P_Long=0.218 (VISSZAZUHAN!)
- Bar 49: P_Long=0.003 (TELJESEN NULLÁN megint)

### Két fő probléma:
1. **Fáziskésés:** ~7 bar reakcióidő trendváltásra
2. **Oscilláció:** P_Long bar-ról bar-ra ugrál (0.02→0.60→0.22→0.003)
3. **Noise dominancia:** P_Noise medián 0.497 — mindig jelen van

### Lehetséges okok:
- 14 feature nem elég (PastRet_1/3, Slope_Close_14 hiányzik)
- RSI/Stoch/MACD maguk is tehetetlenek ( especially M15 )
- LGBM túl merev (depth=6, 500 trees)
- Label (PT/SL) nem feltétlenül korrelál ár trenddel

### Fájlok:
- Script: src/pred_inertia_analysis.py
- CSV: models/nav_3c_v1.01/inertia_analysis.csv
- Brain log: /data/Brain/_qwen_analysis/pred_inertia_analysis_nav_3c_v1.01_20260924.md