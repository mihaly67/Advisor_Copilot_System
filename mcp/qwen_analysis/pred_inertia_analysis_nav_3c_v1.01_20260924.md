# Predikció Tehetetlenség Analízis — nav_3c_v1.01 (2026.09.24. 20:40)

## 🎯 Fő Eredmény: 3 feature kiszedése → Long/Short egyensúly + oscilláció javulás

### Azonosított problémás feature-k:
1. **Regime_Long_Context** (bináris 0/1): 97.4% egymásutáni azonos → lépcsőfüggvény → P_Long ugrál
2. **Regime_Short_Context** (bináris 0/1): 93.5% azonos → lépcsőfüggvény → P_Short ugrál
3. **Trade_Flow_Imb** (folytonos): 49.5% szignálváltás → vad oscilláció

### Eredmények — Régi (14f) vs Új (11f)
| Metrika | Régi (14f) | Új (11f) | Javulás |
|---|---|---|---|
| Long trades | 17 | 1326 | +7,700% |
| Short trades | 2716 | 1393 | -49% |
| Long/Short ratio | 1:160 | 1:1.05 | EGYENNSÚLY |
| Win rate | 50.5% | 50.4% | ≈ |
| Opp rate | 1.7% | 1.6% | ≈ |
| Profit | +1394 | +1394 | ≈ |
| pct_zero | 37.2% | 29.9% | -7.3% |
| pct_opp | 44.3% | 37.4% | -6.9% |
| lag_opp | 7.0 bar | 6.9 bar | -0.1 |
| lag_cor | 6.3 bar | 6.3 bar | ≈ |

### Konklúzió:
- 3 feature kiszedése javított az oscilláción (pct_zero -7.3%, pct_opp -6.9%)
- De a 7 bar fáziskésés NEM javult — az indikátorok (RSI/Stoch/MACD) sajátja
- Szimmetrikus th_noise=0.50 megoldotta a Long/Short egyensúlyt

### Fájlok:
- Modell: `/data/dev/projects/z-ai-copilot/models/nav_3c_v1.01/`
- Script: `/data/dev/projects/z-ai-copilot/src/train_lgbm_nav_3c_v1.01.py`
- Viz: `/data/dev/projects/z-ai-copilot/src/viz_nav_3c_v1.01.py`
- HTML: `/data/dev/projects/z-ai-copilot/docs/viz_nav_3c_v1.01.html`
- Inertia CSV: `/data/dev/projects/z-ai-copilot/models/nav_3c_v1.01/inertia_analysis.csv`
- Inertia script: `/data/dev/projects/z-ai-copilot/src/pred_inertia_analysis.py`