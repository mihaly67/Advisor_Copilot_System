# SHAP + Korrelációs Analízis — Feature Pruning
*2026-09-23 17:20*

## Eredmény: 48 → 24 feature (50% csökkenés!)

### Eldobandó feature-ök (24) — redundáns párok |r|>0.85

#### 1. Pulse_DF_Curve probléma (|r|=0.99 minden árszinttel)
A Pulse_DF_Curve = (MACD - BollingerMavg) — ez **abszolút árszint**, nem normalizált!
Korreláció minden Close_Xm, Micro_R/S, Sec_R/S, Ter_R/S-sel: -0.995 → -0.999
**Megoldás:** Pulse_DF_Curve-t el kell dobnia, vagy normalizálni kell ATR-rel

#### 2. Momentum oszcillátor redundancia (RSI/WPR/Stoch/BB_ZScore)
- WPR_14 ↔ RSI_Fast_5: r=0.922
- Stoch_K ↔ RSI_Fast_5: r=0.922
- Micro_BB_ZScore ↔ RSI_Fast_5: r=0.917
- WPR_14 ↔ Stoch_D: r=0.913
- Micro_RSI_14 ↔ Micro_BB_ZScore: r=0.896

Mind ugyanazt mérik (momentum/overbought-oversold), elég egyet megtartani.

#### 3. Pivot szint redundancia
- Dist_Sec_R_ATR ↔ Dist_Ter_R_ATR: r=0.912 (a Sec és Ter távolságok nagyon hasonlóak)
- Dist_Sec_S_ATR ↔ Dist_Ter_S_ATR: r=0.891
- Ter_R/S ↔ Pulse_DF_Curve: r=-0.97 → átveszi a Pulse_DF_Curve szerepét

#### 4. Bar meta redundancia
- Num_Ticks ↔ ATR_M15: r=-0.873 (több tick = nagyobb volatility)
- Num_Ticks ↔ Tick_Speed: r=-0.873 (inverz)
- Total_Dollar_Value ↔ Tick_Speed: r=-0.874

#### 5. Trend EMA redundancia
- Micro_RSI_14 ↔ Trend_EMA_Slow_Dist: r=-0.871
- Micro_RSI_14 ↔ Trend_EMA_Medium_Dist: r=-0.891
- Flow_Delta_10 ↔ Trend_EMA_Medium_Dist: r=-0.886

### Megtartandó 24 feature
A legfontosabbak (SHAP_Total alapján):
1. Micro_R (0.215) — abszolút szint
2. ATR_Micro (0.089)
3. Close_30m (0.074)
4. Sec_S (0.068) — abszolút szint (Long #1 feature)
5. Ter_S (0.067) — abszolút szint (Long #2 feature)

### Kritikus megfigyelés
A Sec_S (SHAP_Long=0.157) és Ter_S (SHAP_Long=0.076) abszolút árszintek a legfontosabb Long-ok — de ezek túl fogják illeszteni az árszinthez. **Overfitting veszély!**

### Javaslat
1. Eldobni a 24 redundáns feature-t
2. Pulse_DF_Curve-t újraépíteni ATR-normalizálva: (MACD - BB_Mavg) / ATR
3. Csak 1 momentum oszcillátort megtartani (RSI_Fast_5 vagy WPR_14)
4. Abszolút árszintek (Micro_R, Sec_S, Ter_S) cseréje normalizált távolságra