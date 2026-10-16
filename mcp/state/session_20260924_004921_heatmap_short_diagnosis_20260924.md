# Session: heatmap_short_diagnosis_20260924
*Időbélyeg: 2026-09-24T00:49:21.034818*

# Heatmap Short Diagnosis — 2026-09-24

## Script
- `/data/dev/projects/z-ai-copilot/src/heatmap_short_diagnosis.py` (278 sor)
- Output: `/data/dev/projects/z-ai-copilot/docs/short_diagnosis_heatmap.html` (67KB, Plotly CDN)

## 4 Panel
1. SHAP Feature × Class hőtérkép (31×4: Short/Noise/Long/Δ(L−S))
2. Feature korrelációs hőtérkép (31×31, Pearson)
3. P(Short) vs Feature kvartilis (TRUE Short barokon, 31×4)
4. Short-Focus: r(feature,P(Short)) + SHAP Short + Δ(L−S) bar chartok

## LABEL MAPPING (kritikus javítás!)
- CSV Target_Label: -1=Short, 0=Noise, +1=Long
- Model classes: 0=Short, 1=Noise, 2=Long (y_shifted = y+1 a train scriptben)
- Script először rosszul szűrt (==0 Short helyett ==−1), javítva

## EREDMÉNYEK (FULL dataset, 31139 bar)
- Short: 4538 (14.6%), Noise: 12183 (39.1%), Long: 14418 (46.3%)
- TRUE Short barokon: P(Short)=0.516, P(Long)=0.422, P(L)>P(S): 29.3%
- (OOS subset v11: 70.8% opposite — a training data-n jobb)

## TOP SHORT-GYENGÍTŐ FEATURE-ÖK (r(feature, P(Short)) TRUE Short-on)
1. Kyle_Lambda r=-0.249 ← informed trading erősség = alacsonyabb P(Short)
2. Amihud_Illiq r=-0.244 ← illikviditás = alacsonyabb P(Short)
3. Run_Length r=-0.191
4. ATR_Micro r=-0.185 ← volatilitás = alacsonyabb P(Short)
5. Pulse_DF_Curve r=-0.136
6. Micro_S_Vel r=-0.106

## KEY INSIGHT
A mikroszerkezeti feature-ök (Kyle_Lambda, Amihud, ATR, Run_Length) MIND negatívan korrelálnak P(Short)-tal. A modell megtanulta: nagy likviditás/mozgás = nem Short. Csak Regime_ADX és Regime_Trending segítik a Short-ot (SHAP Short=2.52, 0.91).

## REDUNDÁNS FEATURE PÁROK (>0.85 korreláció)
- Kyle_Lambda ↔ Amihud_Illiq (0.938)
- WPR_14 ↔ RSI_Fast_5 (0.922)
- WPR_14 ↔ Stoch_D (0.912)
- WPR_14 ↔ Regime_ZScore (0.861)
- Trade_Flow_Imb ↔ RSI_Fast_5 (0.858)
- Pulse_DF_Curve ↔ Bar_Duration_Sec (−0.945)

## KÖVETKEZŐ LÉPÉS
User döntés: feature pruning (27 marad 31-ből) vagy labeling revízió vagy meta-labeling.