# SHAP V2 — Fordított pivot feature-ök
*2026-09-23*

## Long recall: 16% (előző 17%) — gyakorlatilag nem javult

### Mi történt a fordítás után?

A Dist feature-ők Long_minus_Short értékei továbbra is NEGATÍVOK:
- Dist_Sec_R_ATR: -0.037 (előtte -0.045) — kicsit javult, de még mindig Short!
- Dist_1m: -0.018
- Dist_Sec_S_ATR: -0.020

**A fordítás NEM segített**, mert a gyökérokok más:

### Valódi gyökérok: LABEL ASZIMMETRIA

A labeler PT=1.5$, SL=1.0$, max_bars=5. XAUUSD-ra:
- Short PT (ár essen 1.5$) → gyakran megtörténik (arany gyorsan esik)
- Long PT (ár emelkedjen 1.5$) → lassabb, max_bars=5 nem elég
- Eredmény: Long label-ek nehezebben jönnek létre, a modell kevesebb példát lát

### Top 3 Long SHAP továbbra is abszolút érték:
- Sec_S: 0.157 (megnövekedett 0.118-ról)
- Ter_S: 0.076
- Close_15m: 0.071

A Sec_S SHAP_Long NŐTT a fordítás után (0.118 → 0.157), de ez nem elég.

## Következő lépések
1. Labeler PT aszimmetrikus: Long PT=1.2$, Short PT=1.5$ (könnyebb Long)
2. Vagy max_bars=8 Long-nál, 5 Short-nál
3. Vagy objektív label: következő N bar High/Low alapján