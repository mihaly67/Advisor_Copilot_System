# Session: dual_model_3lepes_kesz_20260925
*Időbélyeg: 2026-09-25T19:29:48.189841*

# Dual Model Grid Search — 3. lépés kész (2026.09.25.)

## DUAL MODEL: Jules V5 (breakout) + NavSystem v1.01 (direction) a V8 CSV-n (31,139 bar)

## Feature mapping sikeres:
- NavSystem V8 → Jules V5: Dist_Micro_R_ATR→Dist_Micro_R, Wick_Upper_ATR→Upper_Wick_ATR, stb.
- Stoch_State_M1 = (Stoch_K - 50) / 50 — újra-számolva
- Mindkét modell predikciója ugyanazon az adaton (V8 CSV)

## EREDMÉNYEK:

### Baseline NavSystem alone (th=0.25, noise=0.35):
- trades=4015, WR=91.0%, profit=+6941, opp=51, p/t=1.73

### Baseline Jules alone (Dir_Conf>0.20, breakout>0.70) — rossz a V8 címkézésen:
- trades=15751, WR=24.0%, profit=-4402, opp=8400

### Best combo: th_br=0.50, th_nav=0.25, th_n=0.50:
- trades=16550, WR=72.2%, profit=+19309, opp=502, p/t=1.17

### Best WR combo: th_br=0.85, th_nav=0.50, th_n=0.35:
- trades=2258, WR=92.0%, profit=+3976, opp=15, p/t=1.76

### KULCS FELISMERÉS:
- NavSystem magas th_n=0.35 (szigorú noise filter) → 91-92% WR, de kevés trade (2258-4015)
- NavSystem alacsony th_n=0.50 (engedékenyebb) → 72-75% WR, de sokkal több trade (9156-16550) és magasabb profit (+19309)
- Jules breakout filter (th_br=0.50 vs 0.85) alig változtatja a WR-t, de alacsonyabb threshold = több trade = több profit

### STRATÉGIA:
1. **Conservative (th_br=0.85, th_n=0.35):** 2258T, 92% WR, +3976 profit, 15 opp — biztonságos
2. **Aggressive (th_br=0.50, th_n=0.50):** 16550T, 72% WR, +19309 profit, 502 opp — maximális profit
3. **Balanced (th_br=0.50, th_n=0.35):** 4005T, 91% WR, +6924 profit, 51 opp, p/t=1.73 — jó kompromisszum

### Következő lépés: Optuna kalibráció (4. lépés)
- Cél: megtalálni az optimális th_br, th_nav, th_n kombinációt
- Profit/trade maximalizálása vagy Sharpe ratio

## Fájlok:
- Script: /data/dev/projects/z-ai-copilot/src/dual_model_jules_nav.py
- CSV: /data/dev/projects/z-ai-copilot/models/dual_model_grid_results.csv