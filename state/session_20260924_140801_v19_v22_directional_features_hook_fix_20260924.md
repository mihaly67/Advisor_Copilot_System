# Session: v19_v22_directional_features_hook_fix_20260924
*Időbélyeg: 2026-09-24T14:08:01.367446*

V19-V22 modell eredmények + PreToolUse hook fix (2026-09-24)

PRETTOOLUSE HOOK FIX:
- Probléma: *.csv minta a .clineignore-ban blokkolta az ML parancsokat (CSV útvonalak a run_commands-ben)
- Megoldás: a hook run_commands ágában a grep -E szűkítve: csak .env/.key/.pem/.p12/.pfx/.keystore/.jks/.secret/.credentials fájlokat blokkol
- A read_files és editor továbbra is minden .clineignore mintát vizsgál
- Teszt: .csv run_commands-ben = cancel:false ✅, .env run_commands-ben = cancel:true ✅
- Beégve: .clinerules/universal.md, memory-bank/activeContext.md, memory-bank/progress.md

MODELL EREDMÉNYEK (V6 labeling, 50 feature + 10 interakció):

| Verzió | Feature | Mode | Accuracy | Trades | TPD | Win% | Opp% | Profit$ |
|--------|---------|------|----------|--------|-----|------|------|---------|
| V19 | 124 | 3-class | 42.1% | 1900 | 167 | 48.4% | 44.6% | +$857 |
| V20/V22 | 50 | 3-class | 40.7% | 2175 | 191 | 49.0% | 44.1% | +$1020 |
| V5 (régi) | 8 | Long-only | 46.5% | 6029 | ~530 | 47.8% | 16.8% | +$2611 |
| meta_v1 | 30 | meta-binary | 51.9% | 6168 | ~542 | 50.8% | 49.2% | +$3237 |

SHAP REDUNDANCIA ANALÍZIS (meta_v1, 30 feature):
- Redundáns párok (|r|>0.85):
  Pulse_DF_Curve <-> Num_Ticks (r=-0.959) → Num_Ticks eltávolítva
  Pulse_DF_Curve <-> Tick_Speed (r=+0.854) → Tick_Speed eltávolítva
  Slope_Close_14 <-> Flow_Delta_10 (r=+0.859) → Flow_Delta_10 eltávolítva
  Num_Ticks <-> Tick_Speed (r=-0.871)

ÚJ IRÁNY-SPECIFIKUS FEATURE-ÖK (13, alacsony korreláció):
Bearish_Rejection (r=0.347), Bullish_Rejection (r=0.363), Consec_Bearish_3, Consec_Bullish_3,
Higher_High_5, Lower_Low_5, Trend_Align_Bull, Trend_Align_Bear, Wick_Asymmetry,
EMA50_Slope_Up, Mom5_Up, Bar_Bullish, Price_Vel_Up

10 INTERAKCIÓ FEATURE (Golden Features, RAG mljar inspiráció):
Trend_Strength, Rejection_Diff, Rejection_Strength, Streak_Pressure, Structure_Dir,
Mom_Agree, Vel_ATR_Ratio, Wick_Pressure, EMA_Proximity, RSI_Deviation

KULCS FELISMERÉS:
- V20 elérte a 191 TPD-t (cél 100+ ✅), de win rate 49% (alig jobb V5 47.8%-ánál)
- A 3-class modell (Long+Short+Noise) magas opposite rate (44.1%) → profit alacsonyabb
- A Long-only V5 még mindig a legjobb profit ($2611), de nem predikálja az irányt
- meta_v1 a legjobb win rate (50.8%), de AUC=0.533 (gyenge diszkrimináció)
- RAG insight: Qlib LightGBM high-freq benchmark → IC=0.035, Long prec=51.1%, Short prec=54.3% — hasonló a miénkhez