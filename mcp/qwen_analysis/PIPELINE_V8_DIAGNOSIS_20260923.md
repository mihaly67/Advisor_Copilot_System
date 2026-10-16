# Pipeline V8 — Teljes diagnosztika

## Végleges eredmény

| Verzió | Feature | Accuracy | Short R | Long R | Opposite |
|---|---|---|---|---|---|
| V1 eredeti | 48 | 40.3% | 73% | **17%** | ~25% (de Short dominált) |
| V6 (14 feat) | 14 | 37.7% | 38% | 37% | 32.1% |
| V8 (19 feat) | 19 | 39.0% | 31% | **43%** | 31.0% |

## Alapvető felismerés: Cohen d < 0.08 MINDEN feature-re

```
Price_Velocity:  d=-0.080  ← A LEGJOBB, de elhanyagolható
WPR_14:          d=-0.048
RSI_Fast_5:      d=-0.046
Pulse_MACD_Hist: d=-0.045
```

Cohen d > 0.2 = kis hatás. Mi 0.08-nál vagyunk = **ZÉRÓ diszkriminatív erő**.

## Mi a gyökér probléma?

**XAUUSD dollárbár scalping (5-8 bar horizon):**
- Long és Short belépések **ugyanabban a feature-térben** helyezkednek el
- A pivot distance-ök NEM prediktívak (diff < 0.03 ATR)
- A momentum oszcillátorok (WPR, RSI, Stoch) marginálisan differenciálnak
- A pivot interakció flag-ek teljesen haszontalanok (SHAP < 0.003)

## Pivot Velocity — új feature ami segít

```
Micro_R_Vel: d=-0.045  ← R esik = Long, R emelkedik = Short
Micro_S_Vel: d=-0.045  ← S mozgása is prediktív
```

DE még mindig d=0.045, ami elhanyagolható.

## Aszimmetrikus labeling eredménye

PT_Long=1.2$, PT_Short=1.8$, max_bars=8:
- Long: 46.3% (könnyebb = több Long label)
- Short: 37.1% (nehezebb = kevesebb Short label)
- Noise: 16.6%

Ez **eltolja** a modellt Long felé (recall 43%), de NEM oldja meg az opposite problémát.

## Következtetés

1. **A feature-ök nem a baj** — az adat természete miatt Long és Short belépések megkülönböztethetetlenek scalping horizonton
2. **Meta-labeling** (kétlépcsős) lehet a megoldás: először "van esemény?" aztán "milyen irány?"
3. **Hosszabb timeframe** (M5/M15 bár) talán jobban diszkriminál
4. **Order flow / DOM feature-ök** (Depth of Market imbalance) hiányoznak — ezek ténylegesen prediktívak scalpingon
5. **Jules eredeti pipeline** hasonló eredményekkel küzdött — a 10 feature modell sem volt 50%+

## V8 feature lista (19)
1. Price_Velocity (d=-0.080, LEGJOBB)
2. WPR_14 (d=-0.048, irány)
3. RSI_Fast_5 (d=-0.046)
4. Pulse_MACD_Hist (d=-0.045)
5. Trend_EMA_Fast_Dist (d=+0.028)
6-7. Micro_R_Vel, Micro_S_Vel (pivot velocity)
8-10. Micro_R_Wick_Rej, Sec_R_Wick_Rej, Micro_S_Wick_Bnc (haszontalan, eldobandó)
11-12. Dist_Micro_R_ATR, Dist_Micro_S_ATR
13-15. Pulse_DF_Curve, Avg_Spread, ATR_Micro
16-18. Wick_Upper_ATR, Wick_Lower_ATR, Bar_Duration_Sec
19. Stoch_D
