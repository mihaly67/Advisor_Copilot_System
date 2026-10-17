# Session: v106_production_deployed
*Időbélyeg: 2026-09-30T23:56:44.824244*

# v1.06 Production Deployment — Teljes Jelentés — 2026.09.30

## PRODUCTION PACKAGE
- /models/production/lgbm_v106.pkl — v1.06 modell (65 feature)
- /models/production/features.txt — feature lista
- /models/production/config.json — threshold konfig (ThN=0.75)
- /models/production/predict_v106.py — TradingPredictorV106 osztály

## PREDICTOR VALIDÁCIÓ
- Batch: Dir=12,138 WR=61.2% Profit=10,149 Opp=0 ✅
- Single bar: működik ✅
- ThN=0.75 az egyetlen döntési paraméter

## WALK-FORWARD VALIDÁCIÓ (idősrendi)
### Time-window (v105 ThN=0.70):
- Q1 (Aug 3-11): WR=61.4% P=2,440
- Q2 (Aug 11-19): WR=61.4% P=2,492
- Q3 (Aug 19-26): WR=62.5% P=2,554
- Q4 (Aug 26-Sep 1): WR=61.8% P=2,567
→ STABIL, nem omladozik!

### Expanding window (v106 ThN=0.75):
- WF1: WR=59.6% P=1,424
- WF2: WR=59.6% P=1,408
- WF3: WR=64.0% P=1,563
- WF4: WR=61.1% P=1,478
- WF5: WR=60.7% P=1,456
- WF6: WR=61.6% P=1,531
→ STABIL, nincs overfit!

## VIZUALIZÁCIÓ
- /docs/v106/v104_vs_v106_comparison.png — 6-panel összehasonlító chart

## DÖNTÉSI LOGIKA (production)
1. Modell → P(Short), P(Noise), P(Long)
2. Ha P(Noise) >= 0.75 → NOISE (nem kereskedünk)
3. Ha P(Noise) < 0.75 ÉS P(Long) > P(Short) → LONG
4. Ha P(Noise) < 0.75 ÉS P(Long) <= P(Short) → SHORT
5. Opposite error soha (Stage2 AUC=1.0)
