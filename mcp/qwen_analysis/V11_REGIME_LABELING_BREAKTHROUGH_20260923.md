# V11 Regime-Conditional Labeling — ATTOROES
*2026-09-23 22:45*

## Modi:

- **Short label csak ADX<20 (nem trendelo) eseten**
- Uptrend-ben (ADX>20) Short lehetosegek = Noise
- Short 37.1% → 14.6% (61% Short Noise-ba olvadt)

## Eredmenyek:

| Metrika | V9 | V11 | Valtozas |
|---|---|---|---|
| Accuracy | 40.2% | 45.9% | +5.7% |
| Short Recall | 33.8% | 93.3% | +59.5% |
| Short Precision | 39.0% | 38.1% | -1.6% |
| Long Recall | 44.3% | 14.3% | -30.0% |
| Long Precision | 50.9% | 48.6% | -2.6% |
| Opposite | 30.7% | 20.7% | -10.0% |

## Cohen d javulas:
- Regime_ADX: 0.049 → **1.151** (23x erosve!)
- Regime_Trending: 0.045 → **1.082** (24x erosve!)
- Regime_Mom_10: -0.014 → -0.080 (5.7x)
- Regime_Short_Context: -0.030 → -0.083 (2.7x)

## Feature importance top 5:
1. Regime_Slope (7056) — regime
2. ATR_Micro (6192) — micro
3. Regime_ADX (5892) — regime
4. Kyle_Lambda (4843) — microstructure
5. Regime_Mom_10 (4673) — regime

## Problema:
- Long recall 14.3% (tul konzervativ)
- Long 1233 → Pred Noise (1298), sok Long elveszik
- De Long precision 48.6% meg mindig jo

## Next:
1. Long labeling is kondicionalas (EMA50 felett Long preferal)
2. Asymmetric class weights (Long tulsulyozas)
3. Optuna threshold kalibracio ujra
