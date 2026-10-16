# CUSUM Filter + Bar Sign Audit Results — 2026.10.07

## Kritikus eredmények

### [1] BAR SIGN (dollar bar irány)
- Bull (Close>Open): 13,906 (49.3%)
- Bear (Close<Open): 14,275 (50.6%)
- Doji: 31 (0.1%)
- **Bar_Sign → next_bar irány egyezés: 49.3%** — ROSSZABB mint random! Egyedül nem prediktív
- **Bar_Sign[t-1] corr(CUSUM_dir) = +0.1406** — De a CUSUM iránnyal KORRELÁL!

### [2] CUSUM FILTER
- 1.0x vol threshold ($2.3): 9,281 events (32.9% of bars) — Up=4,609 Down=4,672
- 0.5x vol ($1.2): 15,457 events (54.8%) — túl sok
- 1.5x vol ($3.5): 6,109 events (21.7%) — jó szelektivitás
- 2.0x vol ($4.6): 4,376 events (15.5%) — nagyon szelektív

### [3] FEATURE CORRELATION WITH CUSUM DIRECTION
| Feature | corr(CUSUM_dir) |
|---------|----------------|
| Price_Velocity | **+0.1099** |
| Bar_Sign[t-1] | **+0.1406** |
| Trend_EMA_Fast_Dist | -0.0772 |
| Dist_Micro_R_ATR | -0.0614 |
| Micro_RSI_14 | +0.0603 |
| Pulse_MACD_Hist | +0.0556 |
| Flow_Delta_10 | +0.0350 |
| Dist_Ter_R_ATR | -0.0165 |

**Korreláció a next-bar Close.diff-el (jelenlegi pipeline): ~0.004 — gyakorlatilag 0!**
**Korreláció a CUSUM iránnyal: 0.06-0.14 — 15-35x jobb!**

### [4] LABEL SNR
- ALL bars: L=42.3% S=52.6% N=5.0% SNR=95.0%
- CUSUM events: L=43.1% S=53.2% N=3.7% SNR=96.3%
- SNR javulás: 1.01x (kicsi, mert PT/SL már szelektál)

### [5] DIST_* IRÁNY LOGIKA PROBLÉMA
- Dist_Micro_R_ATR Long:poz=95.0% Short:neg=**5.6%** — SHORT LABEL NEM TÁMOGATJA!
- Dist_Ter_R_ATR Long:poz=98.2% Short:neg=**1.8%** — MÉG ROSSZABB!
- **Ez azt jelenti: Dist_R mindig pozitív, Dist_S mindig pozitív — S/R mindig felett/alatt vagyunk**
- **A label irány (Long/Short) nem kódolódik a Dist feature-ben!**

## Konklúzió

### 3 FŐ HIBA a jelenlegi pipeline-ban:

1. **NINCS CUSUM FILTER** → minden bar labelelve, túl sok noise
2. **NINCS BAR_SIGN feature** → a buying/selling pressure info elveszik
3. **Dist feature-k NEM KÓDOLJÁK az irányt** → Long és Short sample-ok azonos feature-eloszlással

### A CUSUM irány javítja a feature korrelációt 15-35x!
- Price_Velocity: 0.004 → 0.110 (27x)
- Pulse_MACD_Hist: 0.004 → 0.056 (14x)
- Micro_RSI_14: -0.005 → 0.060 (12x)

### JAVÍTÁSI TERV (prioritás sorrend):
1. **Bar_Sign feature** hozzáadása (corr=0.14 a CUSUM iránnyal)
2. **CUSUM filter** → csak CUSUM eventeken label-elni
3. **Feature-k M1 OHLC-ről** számolni (nem dollar bar OHLC-ről)
4. **Meta-labeling** → Primary=Bar_Sign/CUSUM direction, Secondary=ML
