# Session: v5cfd_ml_first_signal
*Időbélyeg: 2026-10-08T23:03:21.939733*

# V5 CFD ML-First Signal Logic (2026-10-08 v4)

## Változtatások

### 1. classify_signal() — ML-first logika
**Régi (Fade-domináns):** CUSUM → Fade irány → ML csak ha conf>0.30 → Fade mindig nyert
**Új (ML-first):**
1. conf < NOISE_THRESHOLD (0.15) → NO TRADE (zajzóna ~42.5%-57.5%)
2. CUSUM egyetért ML-lel → erős signal
3. CUSUM ellenkezik + conf > OVERRIDE_CONF (0.40) → ML felülírja
4. CUSUM ellenkezik + conf <= 0.40 → NO TRADE (bizonytalan)

### 2. Paraméterek
- NOISE_THRESHOLD=0.15 (P(L) 42.5%-57.5% zajzóna)
- OVERRIDE_CONF=0.40 (ML felülírja CUSUM-ot ha conf > 40%)

### 3. Log formátum
```
[22:58:07] ⚪ NO TRADE | P(L)=52.1% conf=0.04 | CUSUM:↓ Fade:L ML:L | zaj | ✗
```
Mutatja: signal, P(L), conf, CUSUM irány, Fade irány, ML irány, döntés oka, stabilitás

### 4. Subchart zajzóna
- noise_lo: 0.425 (narancssárga szaggatott vonal)
- noise_hi: 0.575 (narancssárga szaggatott vonal)
- 0.50 küszöb: fehér szaggatott vonal

### 5. HUD info sáv
- Mutatja: Signal, P(L), conf, CUSUM↑/↓, FadeL/S, ML:L/S, döntés ok [zaj]/[CUSUM↔ML]/[ML=CUSUM]/[ML override]/[ML]

### 6. Training pipeline AUC
- `roc_auc_score` hozzáadva OOS és Vizsga értékeléshez
- `scale_pos_weight` hozzáadva LGBM-hez (Short/Long arány)
- `classification_report` importálva
- AUC bekerül a results.json-be

### 7. BAR_HISTORY_LEN=60 — csúszóablak ✅
Nem változott. A deque(maxlen=60) automatikusan kiesik a régi barokat. CUSUM state globális.

### Élő eredmény
- Első bar: P(L)=52.1%, conf=0.04 → NO TRADE (zajzóna) ✅
- A régi logika SHORT-ot küldött volna (Fade dominált)
