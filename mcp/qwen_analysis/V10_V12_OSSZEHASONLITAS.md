# 📊 V10-V12 ÖSSZEHASONLÍTÁS — ÚJ V6 LABELING (szimmetrikus, regime filter nélkül)

> **Dátum:** 2026-09-24
> **Labeling:** V6 (`dom_labeler_v6.py`) — PT_Long=1.2$, PT_Short=1.2$, SL=1.0$, max_bars=8, **regime filter KI**
> **Adat:** `labeled_dollar_bars_v6.csv` (31,139 sor)

## Label eloszlás V6 (új) vs V5 (régi)

| Label | V5 (régi) | V6 (új) |
|-------|----------|---------|
| Short | 14.6% (4,538) | **43.1% (13,410)** |
| Long  | 46.3% (14,418) | 42.5% (13,226) |
| Noise | 39.1% (12,183) | **14.5% (4,503)** |
| Short ADX<20 | **100%** | **39.4%** ← körkörösség megszűnt! |

## Modell eredmények

| Verzió | Feature | Accuracy | Trades (L/S) | Win% | Opp% | Profit$ |
|--------|---------|----------|-------------|------|------|---------|
| V5 (régi labeling) | 8 | 46.5% | 6029/0 | 47.8% | 16.8% | +2611 |
| V10 (új labeling) | 82 | 43.3% | 5985 (2830/**3155**) | 45.0% | **42.2%** | +2103 |
| V11 (új labeling) | 20 | 42.6% | 5996 (4811/**1185**) | 43.9% | **43.2%** | +1897 |
| V12 (új labeling) | 10 | 42.7% | 5965 (4807/**1158**) | 44.4% | **42.8%** | +1973 |

## Kulcs megfigyelések

### 1. Short recall drasztikusan javult
- V5: Short recall = 0% (nullázva)
- V10: Short recall = 82% (de opposite 42.2%)
- V11/V12: Short recall ~20% (kevesebb Short trade, de opposite még mindig 43%)

### 2. Opposite magas maradt (42-43%)
A modell **nem tudja megkülönböztetni Short vs Long-ot**. A szimmetrikus labeling azt jelenti, hogy ~50/50 Short/Long, és a feature-ök nem hordoznak irány-specifikus információt.

### 3. SHAP: Regime_ADX már nem körkörös
- V5: Regime_ADX SHAP_Short=2.46 (#1 feature, körkörös)
- V10: Regime_ADX SHAP_Short=0.012 (#3, **nem körkörös**)
- V12: Regime_ADX SHAP_Short=0.031 (#5)

### 4. WPR továbbra sem diszkriminál
- V6 labelinggel is: Cohen's d = +0.03 (Short vs Long)
- WPR_Change_5: d = +0.036
- WPR_Bearish_Cross: d = +0.002
- **WPR nem az irányt mutatja** dollar bar-on

### 5. Egyetlen feature sem irány-specifikus
SHAP Long_minus_Short értékek mind <0.04 — egyik feature sem tudja megmondani Short vs Long.

## Következtetés

A **labeling körkörösség megszűnt** (Regime_ADX SHAP zuhant), de a **modell nem tudja megkülönböztetni az irányokat**. A feature engineering nem ad irány-specifikus információt.

## Következő lépések

1. **Irány-specifikus feature-ök** kellenek:
   - Price_Velocity előjele (negatív = Short irány)
   - Trade_Flow_Imb negatív = eladási nyomás
   - Wick aszimmetria (felső wick nagyobb = Short)
   - Momentum irány (ROC < 0 = Short)

2. **Meta-labeling** (López de Prado): 1. modell prediktál irányt, 2. modell szűri (trade/no-trade)

3. **Asymmetric class weighting**: Short osztály súlyozása magasabb

4. **Fixed-horizon labeling**: 5 bar múlva return > threshold → label (egyszerűbb, talán kevesebb Noise)
