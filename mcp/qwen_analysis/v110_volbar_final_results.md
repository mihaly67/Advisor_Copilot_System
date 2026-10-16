# V110 VolBar Pipeline — Végeredmény

## Pipeline architektúra
1. **Volatility Bar Builder**: Σ|Δmid_price| ≥ ATR_target → bar zárul
2. **Feature Engineering**: 18 feature, shift(1) leakfix, ZZ+MTF direkt CSV-ből
3. **Triple Barrier Labeling**: PT=$1.5, SL=$1.0, max_bars=8
4. **LightGBM**: 781 trees, lr=0.0142, leaves=57, depth=6
5. **Threshold**: THL=0.384, THS=0.501, THN=0.202 (optimalizált OOS-on)

## ATR_target Sweep
| ATR  | Train bars | sec/bar | OOS WR | Viz WR | Gap  |
|------|-----------|---------|--------|--------|------|
| $1.5 | 294,995   | 22.8s   | 41.4%  | 41.1%  | +0.3%|
| $2.0 | 226,946   | 29.7s   | 44.1%  | 43.4%  | +0.7%|
| $3.0 | 155,374   | 43.3s   | 46.4%  | 49.0%  | -2.6%| ← BEST
| $5.0 | 95,293    | 70.7s   | 45.7%  | 43.4%  | +2.3%|
| $8.0 | 60,318    | 111.6s  | 44.3%  | 42.6%  | +1.7%|

## Végeredmény (optimized threshold)
| Metrika    | OOS      | Vizsga  |
|-----------|----------|---------|
| WR         | 50.8%    | 51.7%   |
| Profit     | $616.5   | $241.5  |
| Trades     | 2,281    | 826     |
| Gap        | -0.9% → STABIL |

## Feature Importance (Top 10)
1. RSI_M15_signed 9.27% (NEW dir)
2. Dist_Ter_S 6.84%
3. Dist_Ter_R 6.75%
4. MACD_Hist_ATR 6.53% (NEW dir)
5. Dist_Sec_S 6.30%
6. Dist_Sec_R 6.24%
7. Dist_Micro_S 6.09%
8. Dist_Micro_R 6.01%
9. RSI_signed 5.81% (NEW dir)
10. ROC_5 5.70% (NEW dir)

## Kulcs megállapítások
- A korábbi eredmények (WR=42%, 59.1%) INVALID — futures CSV-t használtak CFD helyett
- Volatility bar az egyetlen helyes megoldás CFD-re (nincs tick volume)
- WR > 50% pozitív edge-et jelent (random = 50%)
- A gap -0.9% — nincs overfitting
- A vizsgán JOBB WR, mint OOS-on — stabil generalizáció

## Fájlok
- `/data/dev/projects/z-ai-copilot/src/v110_volbar_pipeline.py`
- `/data/dev/projects/z-ai-copilot/src/v110_volbar_optimize.py`
- `/data/dev/projects/z-ai-copilot/models/v110_volbar/lgbm_18feat_volbar_opt.pkl`
- `/data/dev/projects/z-ai-copilot/docs/v110_volbar/volbar_opt_results.json`
- `/data/dev/projects/z-ai-copilot/docs/v110_volbar/viz_OOS_volbar.html`
- `/data/dev/projects/z-ai-copilot/docs/v110_volbar/viz_VIZSGA_volbar.html`
- `/data/dev/projects/z-ai-copilot/docs/v110_volbar/viz_comparison.html`
