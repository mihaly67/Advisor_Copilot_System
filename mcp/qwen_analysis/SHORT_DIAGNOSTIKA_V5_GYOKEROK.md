# 🔴 SHORT DIAGNOSTIKA — V5 GYÖKÉROK ELEMZÉS

> **Dátum:** 2026-09-24
> **Forrás:** `/data/dev/projects/z-ai-copilot/`
> **Script:** `/data/mcp_server/state/short_diag.py`

---

## 1. LABEL ELOSZLÁS

```
-1 (Short):  4538  (14.6%)
 0 (Noise): 12183  (39.1%)
+1 (Long):  14418  (46.3%)
```

**Short a kisebbségi osztály** — de ez nem a fő probléma.

---

## 2. 🚨 GYÖKÉROK #1: KÖRKÖRÖS LABELING

### Tények:
- **Short barok 100%-a ADX<20** (4538/4538 = 100%)
- Long barok: ADX mean=24.5, 38.7%-uk ADX<20
- Noise barok: ADX mean=28.3

### Kód (`dom_labeler_v5.py` 96-99. sor):
```python
if short_allowed[i]:   # ADX < 20
    hit = -1           # Short
else:
    hit = 0            # uptrend-ben Short = Noise
```

### Konklúzió:
A labeling **kényszeríti** hogy Short csak ADX<20 esetén jöhessen létre. De a V5 modell **Regime_ADX** feature-t használja (SHAP_Short=2.46, #1 feature). Ez **TAUTOLOGIA**:

```
Labeling: ADX<20 → Short label
Model:    ADX<20 feature → Short prediction
```

A modell nem tanulja meg *miért* megy le az ár — csak memorizálja a labeling szabályt. Amikor OOS-ben Short barokon Long-ot mond (62.6%), az azért van mert az ADX érték alapján nem tudja megkülönböztetni a Short-ot a Long-tól az ADX<20 sávban belül.

---

## 3. 🚨 GYÖKÉROK #2: ASZIMMETRIKUS PT

### Paraméterek:
- PT_Long = 1.2$  (Long profit target)
- PT_Short = 1.8$ (Short profit target — **50%-kal nagyobb!**)
- SL = 1.0$
- Max_bars = 8

### Hatás:
- Long: 1.2$ emelkedés elég a Long label-hez (könnyebb)
- Short: 1.8$ esés kell a Short label-hez (nehezebb)
- Sok bar ahol az ár 1.2-1.8$ között esett → **Noise lesz Short helyett**

### Számok:
- Potenciális Short win (PT=1.8$ elérve): 8343
- Potenciális Short loss (SL=1.0$ elérve): 15266
- **Short win/loss ratio = 0.55** — a Short label torzított, a kisebb eséseket Noise-ba nyomja

---

## 4. 🚨 GYÖKÉROK #3: 6/8 FEATURE NEM DISZKRIMINÁL

### Cohen's d (Short vs Long):

| Feature | Short mean | Long mean | Cohen's d | Verdict |
|---------|-----------|----------|-----------|---------|
| Regime_ADX | 15.6 | 24.5 | **-1.231** | Erős, de KÖRKÖRÖS |
| Regime_Trending | 0.00 | 0.41 | **-1.185** | Erős, de KÖRKÖRÖS |
| ATR_Micro | 2.42 | 2.62 | -0.243 | Gyenge |
| Dist_Sec_S_ATR | 1.10 | 1.29 | -0.201 | Gyenge |
| Kyle_Lambda | 0.00 | 0.00 | -0.167 | Gyenge |
| Dist_Sec_R_ATR | -1.06 | -1.21 | +0.164 | Gyenge |
| Trend_EMA_Slow_Dist | +0.02 | -0.01 | +0.047 | Semmi |
| Micro_RSI_14 | 49.9 | 50.1 | -0.017 | Semmi |

**6 featureből 6 nem diszkriminál Short vs Long-ot** (|d| < 0.3). A modell nem kap irány-specifikus információt a feature-öktől — csak a körkörös ADX/Trending-et.

---

## 5. V5 PREDIKCIÓ OOS (6228 bar)

### True Short barok (n=1061):
- P(Short) mean = 0.442
- P(Long) mean = **0.488** ← Long-nak jósolja!
- **62.6% Long predikció Short barokon** ← Opposite!

### True Long barok (n=2955):
- P(Long) mean = 0.589
- P(Short) mean = 0.194
- 79.3% helyesen Long ← jó, de csak mert Long a többség

### SHAP importance:
```
Regime_ADX         SHAP_Short=2.46  SHAP_Long=0.20   L-S=-2.26
Regime_Trending    SHAP_Short=1.03  SHAP_Long=0.04   L-S=-0.99
ATR_Micro          SHAP_Short=0.03  SHAP_Long=0.07
Trend_EMA_Slow_Dist SHAP_Short=0.08 SHAP_Long=0.03
Kyle_Lambda        SHAP_Short=0.03  SHAP_Long=0.05
Micro_RSI_14       SHAP_Short=0.05  SHAP_Long=0.03
Dist_Sec_R_ATR     SHAP_Short=0.05  SHAP_Long=0.04
Dist_Sec_S_ATR     SHAP_Short=0.04  SHAP_Long=0.03
```

Csak Regime_ADX és Regime_Trending hat a Short predikcióra — de mindkettő körkörös a labelinggel.

---

## 6. ÖSSZEFOGLALÁS — HÁROM GYÖKÉROK

### 1. KÖRKÖRÖS LABELING (fő hiba)
A labeling ADX<20 → Short szabályt használ. A modell ugyanezt az ADX feature-t használja. A modell nem tanul piaci mintákat, csak a labeling szabályt memorizálja. **OOS-ben nem tud generalizálni** mert az ADX<20 sávon belül nem tudja megkülönböztetni Short vs Long-ot.

### 2. ASZIMMETRIKUS PT (másodlagos hiba)
PT_Short=1.8$ vs PT_Long=1.2$ → kisebb esések Noise-ba kerülnek → kevesebb Short tanulópélda.

### 3. FEATURE HIÁNY (harmadlagos hiba)
6/8 feature nem diszkriminál Short vs Long-ot (Cohen's d ≈ 0). Nincsenek Short-specifikus feature-ök (bearish momentum, rejection, volume imbalance).

---

## 7. JAVASOLT MEGOLDÁSOK

### A) Labeling fix (legfontosabb):
1. **Távolítsuk el a regime_short_filtert** — hagyjuk a triple barrier-t természetesen Short-ot generálni
2. **Szimmetrikus PT**: PT_Short=1.2$ (mint Long)
3. **Vagy fixed-horizon labeling**: 5 bar múlva return > threshold → Long/Short/Noise (simpler, no circularity)

### B) Feature fix:
4. **Adjunk Short-specifikus feature-öket**:
   - Bearish rejection (close < open, long lower wick)
   - Volume imbalance (sell volume / buy volume)
   - Momentum negatív (ROC < 0)
   - Micro_RSI bearish cross (RSI < 30 és csökken)

### C) Validációs fix:
5. **Regime_ADX-t KIVENNI a feature-ökből** és megnézni mi marad — ha semmi nem diszkriminál, akkor a feature engineering a hiba
6. **Labeling körkörösség teszt**: ha a label és a feature korrelációja > 0.8, az körkörös

### Prioritás: A1 → A2 → B4 → C5
