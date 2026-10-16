# 🔴 SHORT DIAGNOSTIKAI CHECKLIST

> **Utolsó frissítés:** 2026-09-24
> **Állapot:** NYITOTT — V5 Short=0 nem megoldás, gyökérok kell
> **Forrás:** /data/dev/projects/z-ai-copilot/

## Tünet
- V5 (8 feat, Long-only): +$2611 profit, de Short nullázva ← NEM MEGOLDÁS
- V7-V9 (Short kényszerítés): opposite 20-21%, profit esik ← NEM MEGOLDÁS
- A modell Short-címkézett barokon Long-ot mond (P(L)>P(S) 70%-ban)

## Lehetséges Gyökérok

### [ ] 1. LABELING BUG — dom_labeler_v5.py
- Regime-conditional Short: Short only when ADX<20
- Ha ADX>20 → Short = Noise (cirkuláris probléma → modell nem tanul Short-ot)
- **Ellenőrizni**: ADX<20 hányszor teljesül? Mennyi Short marad?
- **Ellenőrizni**: Volatilis dropok (nagy ATR) → Short label Noise lesz? ← GYANÚS

### [ ] 2. FEATURE ENGINEERING BUG — dom_feature_engineer_mtf.py
- Shift(1) minden feature-en → anti-lookahead, de vajon helyes?
- ATR_Micro, Kyle_Lambda, Amihud mind Short-gyengítő (r<0 with P(Short))
- **Ellenőrizni**: Feature értékek Short barokon vs Long barokon — diszkriminálnak-e?
- **Ellenőrizni**: Regime_ADX feature vs label ADX — ugyanaz? Körkörös?

### [ ] 3. LABEL/SIGNÁL KONFLIKTUS
- Label: -1=Short (ár ESNI fog)
- De XAUUSD uptrend 2 éve → Long mindig jobb expected value
- **Ellenőrizni**: Short barok ténylegesen drop-e az ár? Vagy csak korrekció amiben Long is nyer?

### [ ] 4. ASZIMMETRIKUS PT/SL A LABELINGBEN
- PT_Long=1.2$, PT_Short=1.8$, SL=1.0$, max_bars=8
- Short PT 50%-lal nagyobb ← kevesebb Short label
- **Ellenőrizni**: Milyen arány Short/Long/Noise? Short elnyomva?

## Fájlok Vizsgálatra
- `/data/dev/projects/z-ai-copilot/src/dom_labeler_v5.py` — labeling logika
- `/data/dev/projects/z-ai-copilot/src/dom_feature_engineer_mtf.py` — feature gen
- `/data/dev/projects/z-ai-copilot/Master_csv/processed/labeled_dollar_bars_adaptive.csv` — labeled adat
- `/data/dev/projects/z-ai-copilot/models/v5/` — V5 model + SHAP

## Konkrét Ellenőrzések
1. Label eloszlás: hány Short/Noise/Long? ADX<20 hányszor?
2. Short barokon feature értékek vs Long barokon: diszkriminál-e?
3. Regime_ADX feature vs Regime_ADX-based label: körkörös?
4. Triple barrier: Short barok ténylegesen nyert-e (ár esett)?
5. V5 SHAP: Regime_ADX SHAP_Short=2.2 de a többi feature SHAP_Short≈0.02 ← MIÉRT?
