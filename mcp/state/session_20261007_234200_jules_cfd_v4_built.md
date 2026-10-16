# Session: jules_cfd_v4_built
*Időbélyeg: 2026-10-07T23:42:00.167815*

## Jules CFD v4 Pipeline — Built & Tested

### Architektúra (Prado-helyes)
```
Tick CSV → Dollar bars → CUSUM filter → features at events → Triple Barrier → LightGBM
```

### Kulcs változások v3 → v4
1. **CUSUM FILTER** — csak CUSUM eventeken label-elünk (noise -78%)
2. **Bar_Direction feature** — (Close-Open)/(High-Low), folytonos [-1,+1], buying/selling pressure
3. **NavSystem direction** — DF_Direction, MACD_Direction, Nav_Consensus
4. **Regime_ADX + Regime_Trending** — környezeti kontextus

### Eredmények (nav_v31, CUSUM 1.5x vol)
- VIZSGA WR: **48.8%**, Short WR: **55.0%**, STABIL (gap -1.0%)
- Bar_Direction importance: **8.31%** (v3-ban 0%)
- OOS WR: 47.8%, Short WR: 53.5%

### Hátramaradt problémák
1. Long WR 40.7% — még mindig rosszabb mint random
2. Túl kevés train sample (5,235 CUSUM event a nav_v31-ből, 24K bar)
3. A nav_v31 adat kisebb mint a teljes tick adat (4.15M tick)

### Következő lépések
1. Full pipeline a 4.15M tick adatból → több CUSUM event
2. Meta-labeling: Primary=Bar_Sign/CUSUM direction, Secondary=ML
3. M1 window features (momentum/velocity M1 OHLC-ről)
4. CUSUM direction as side prediction → meta-labeler decides bet size only

### Fájlok
- `/data/dev/projects/z-ai-copilot/src/jules_cfd_v4.py` — v4 pipeline
- `/data/dev/projects/z-ai-copilot/src/prado_cusum_filter.py` — CUSUM filter lib
- Model: `/data/dev/projects/z-ai-copilot/models/jules_cfd_v4/lgbm_jules_cfd_v4.pkl`
- Results: `/data/dev/projects/z-ai-copilot/docs/jules_cfd_v4/jules_cfd_v4_results.json`
