# SHAP Modell-diagnosztika Eredmények
*Időbélyeg: 2026-09-23 17:05*

## KULCSFELFEDEZÉS: Long katasztrófa oka

### Top 3 Long feature (SHAP_Long érték)
1. **Sec_S** (Secondary Support): 0.118 — a modell a TÁMASZ közelségét használja Long-hoz
2. **Ter_S** (Tertiary Support): 0.094
3. **Close_15m**: 0.077

### A probléma: Long_minus_Short mind negatív (kivétellel Dist_30m, Dist_Ter_S_ATR)

Pivot/Distance feature-ök Long_minus_Short értéke:
- Dist_Sec_R_ATR: **-0.045** (legerősebb Short-segítő!)
- Dist_1m: -0.015
- Dist_Sec_S_ATR: -0.024
- Dist_Micro_R_ATR: -0.012
- Dist_Ter_R_ATR: -0.011
- Trend_EMA_Super_Dist: -0.007
- Trend_EMA_Fast_Dist: -0.008

**Ez azt jelenti:** a pivot távolság feature-ök MIND Short-et segítenek, nem Long-ot!

### Miért?

1. **Sec_S és Ter_S** (támasz szintek) alapból benne vannak a CSV-ben mint ABSZOLÚT érték. Ha a modell "közel van a támaszhoz" = Long, de a támasz szint is mozog!

2. **Dist_XXX_ATR feature-ök** (shift-1 miatt) KÉSVE látják a távolságot. Amikor az ár gyorsan emelkedik (Long helyzet), a támasz távolodik → a feature "távol vagyok a támasztól" = nem Long. De közben az ár már emelkedett!

3. **Trend EMA feature-ök**: ha az ár az EMA felett van (Long helyzet), a Trend_EMA_X_Dist pozitív. De a SHAP szerint ez SEGÍTI A SHORT-OT. Ez ellentétes logika!

### Gyökérok: LOOKAHEAD bias a label-ben?
A label entry = Open[i+1]. Ha az ár gyorsan emelkedik (Long), a Open[i+1] MAGASABB, így a PT=1.5$ könnyebben elérhető. De a feature-ök shift(1)-el KÉSNEK — az ár már elment!

### Top 5 globális SHAP fontosság
1. Micro_R: 0.215 (SHAP_Noise dominal!)
2. ATR_Micro: 0.089
3. Close_30m: 0.074
4. Sec_S: 0.068
5. Ter_S: 0.067

**Micro_R 0.42 Noise SHAP!** Ez azt jelenti, a Micro Resistance szintből leginkább Noise jelet csinál a modell — nem Longot vagy Shortot!

## Javaslatok
1. **Eldobni a zavaró feature-öket**: Dist_Sec_R_ATR, Dist_1m, Trend_EMA_Fast_Dist
2. **Megfordítani a Dist feature-ök logikáját**: jelenleg (Close - Support)/ATR, de lehet hogy (Support - Close)/ATR kell (pozitív = Long)
3. **Új feature**: momentum irány (Close > Open = bullish) mint Long trigger
4. **Labeling revízió**: lehet hogy max_bars=5 túl kevés a Long jeleknek