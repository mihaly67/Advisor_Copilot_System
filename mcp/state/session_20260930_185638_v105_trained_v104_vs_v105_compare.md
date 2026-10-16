# Session: v105_trained_v104_vs_v105_compare
*Időbélyeg: 2026-09-30T18:56:38.064006*

# v1.05 Tanitas + v1.04 vs v1.05 Osszehasonlitas — 2026.09.30

## V1.05 MODELL
- 55 feature (42 v1.04 + 13 uj Noise-vs-Dir)
- noise_weight = 0.85 (v1.04=0.7)
- Uj feature-ek: RSI_M15, Regime_ADX, Regime_Slope, Regime_Short_Context, Regime_Trending,
  Kyle_Vol_Sync, Kyle_Lambda, Amihud_Illiq, VPIN, Trend_EMA_Super_Dist, Trend_EMA_Slow_Dist,
  Micro_Price_Dist, EMA50_Slope_Up

## NOISE RECALL JAVULAS
- v1.04: Noise recall=24.9% | Dir->Noise=1557 (19.9%)
- v1.05: Noise recall=32.2% | Dir->Noise=1956 (24.9%)
- Megjegyzes: Noise recall javult (24.9→32.2%), DE Dir->Noise novelodott default threshold-nal!
  Ez azert van, mert noise_weight=0.85→a modell tobb Noise-t josl, de kevesebb iranyt→tobb Dir→Noise hiba

## VERZIO OSSZEHASONLITAS (kiemelt threshold-ok)

| Scenario | THL | THS | THN | v1.04 WR% | v1.05 WR% | Δ WR | v1.04 Profit | v1.05 Profit | Δ Profit | v1.04 DN% | v1.05 DN% | v1.04 PL | v1.05 PL |
|----------|-----|-----|-----|-----------|-----------|------|-------------|-------------|----------|-----------|-----------|----------|----------|
| Laza     |0.30|0.35|0.55| 62.1      | 62.7      | +0.6 |      9339   |      8874   |   -465   | 37.9      | 37.3      | 1.64     | 1.68     |
| S1       |0.35|0.40|0.50| 62.4      | 63.2      | +0.8 |      8786   |      8349   |   -437   | 37.6      | 36.8      | 1.66     | 1.72     |
| S2       |0.45|0.50|0.40| 63.8      | 64.7      | +0.9 |      7369   |      7014   |   -355   | 36.2      | 35.3      | 1.77     | 1.83     |
| S3       |0.50|0.55|0.35| 64.9      | 66.1      | +1.2 |      6344   |      6337   |     -7   | 35.1      | 33.9      | 1.85     | 1.95     |
| Szigor   |0.55|0.55|0.30| 66.8      | 67.5      | +0.7 |      5369   |      5492   |   +123   | 33.2      | 32.5      | 2.01     | 2.08     |

## KULCS MEGALLAPITASOK

1. **WR javul minden scenario-ban** v1.05-ben (+0.6% to +1.2%)
2. **DN% (DirAsNoise) csokken minden scenario-ban** (-0.6 to -1.2%)
3. **PL ratio javul minden scenario-ban** (1.64→1.68 to 2.01→2.08)
4. **Profit: Szigor scenario-ban v1.05 NYER** (+123), tobbi scenario-ban v1.04 nyer (de csokenebb kulonbseggel)
5. **S3 scenario: gyakorlatilag azonos profit** (-7 kulonbseg), de WR +1.2% es DN -1.2% javul

## TOP 5 PROFIT
- v1.04: 10216 (THL=0.25 THS=0.30 THN=0.70, WR=61.3%)
- v1.05: 10055 (THL=0.30 THS=0.30 THN=0.70, WR=61.8%)

## KOVETKEZO LEPESEK
- A v1.05 vilagosan jobb minosegu predikciot ad (WR, PL, DN mind javult)
- A profit kis mertekben csokkent a laza threshold-oknal, de Szigor scenario-ban mar nyer
- Erdekes lenne: (1) noise_weight=0.80 proba, (2) Optuna threshold optimalizalas v1.05 modellel

## FAJLOK
- Model: /data/dev/projects/z-ai-copilot/models/v105/lgbm_v105.pkl
- Features: /data/dev/projects/z-ai-copilot/src/features_v8.py (55 feat)
- Train: /data/dev/projects/z-ai-copilot/src/train_jules_v105.py
- Compare: /data/dev/projects/z-ai-copilot/src/v104_vs_v105_compare.py
- Metrics: /data/dev/projects/z-ai-copilot/models/v105/metrics.json
