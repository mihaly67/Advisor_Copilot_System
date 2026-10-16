# Session: v105_final_optimization
*Időbélyeg: 2026-09-30T22:56:20.585134*

# v1.05 Teljes Optimalizálás — Végső Eredmények — 2026.09.30

## VÉGSŐ KONFIGURÁCIÓ: v1.05 + ThN=0.70

| Paraméter | v1.04 Baseline | v1.05 Eredeti | v1.05 OPTIMAL |
|-----------|---------------|---------------|---------------|
| Features | 42 | 55 | 55 |
| noise_weight | 0.70 | 0.85 | 0.85 |
| ThN (P(Noise)<) | 0.55 | 0.55 | **0.70** |
| Dir trades | 6,455 | 10,083 | **11,743** |
| WR% | 66.1% | 62.7% | **62.0%** |
| Profit | 6,337 | 8,874 | **10,091** |
| P/tr | 0.982 | 0.880 | **0.859** |
| PL ratio | 1.95 | 1.68 | **1.63** |
| L→Noise | 2,082 | 959 | **374** |
| S→Noise | 1,495 | 563 | **189** |
| Opp | 0 | 0 | **0** |

### JAVULÁS v1.05 eredeti → OPTIMAL
- **+1,217 profit** (+13.7%)
- **+1,660 trade** (+16.5%)
- **-585 L→Noise** (-61% elmaradt Long profit!)
- **-374 S→Noise** (-66% elmaradt Short profit!)
- WR: -0.7% (minimális minőségcsökkenés)

### JAVULÁS v1.04 baseline → OPTIMAL
- **+3,754 profit** (+59.3%!)
- **+5,288 trade** (+82%)
- **-1,708 L→Noise** (-82%)
- **-1,306 S→Noise** (-87%)
- WR: -4.1% (de a profit drasztikusan jobb)

## CASCADE ARCHITEKTÚRA
- Stage 1 (Noise-vs-Dir): AUC=0.7666
- Stage 2 (Long-vs-Short): AUC=1.0000
- **Hybrid = Baseline** (Opp már=0)
- **ThL nem számít** (Stage2 sosem téved)
- Cascade WR jobb, de túl kevés trade → profit rosszabb

## FEATURE KANDIDÁTUSOK v1.06-hoz
Top 10 új feature (Noise-vs-Dir AUC javulás):
1. Pulse_DF_Curve (+0.0205)
2. Close_15m (+0.0199) — LEHET LEAKY!
3. Ter_R (+0.0191) — nyers pivot szint
4. Sec_S (+0.0185) — nyers pivot szint
5. Micro_R (+0.0184) — nyers pivot szint
6. Sec_R (+0.0172) — nyers pivot szint
7. ATR_M15 (+0.0165)
8. Close_30m (+0.0148) — LEHET LEAKY!
9. Total_Dollar_Value (+0.0137)
10. Close_1m (+0.0137) — LEHET LEAKY!

SAFE top 10 (AUC=0.8137 együtt, +0.0471):
Pulse_DF_Curve, ATR_M15, Num_Ticks, Total_Dollar_Value,
Roll_Spread, Micro_MACD_Hist, Tick_Speed, Dist_15m,
Regime_Above_EMA50, Run_Length

## NOISE_WEIGHT x THN GRID SEARCH
Profit top 3:
1. nw=0.60 ThN=0.70 → P=10,197 (WR=61.6%)
2. nw=0.70 ThN=0.70 → P=10,178 (WR=61.7%)
3. nw=0.75 ThN=0.70 → P=10,156 (WR=61.7%)

WR top 3 (min 10000 trade):
1. nw=0.85 ThN=0.55 → WR=62.8% (P=8,939)
2. nw=0.85 ThN=0.60 → WR=62.4% (P=9,389)
3. nw=0.85 ThN=0.70 → WR=62.0% (P=10,091)

## DIR→NOISE HIBAELEMZÉS
Legnagyobb hatású feature-ök (Cohen's d):
1. MomScore_14 (combined=0.911)
2. Slope_Close_14 (combined=0.781)
3. Flow_Delta_10 (combined=0.532)
4. Mom10_Direction (combined=0.529)
5. Regime_Slope (combined=0.513)

Közös jellemző: a Dir→Noise hibáknál GYENGÉBB trend, kisebb slope, középső RSI
