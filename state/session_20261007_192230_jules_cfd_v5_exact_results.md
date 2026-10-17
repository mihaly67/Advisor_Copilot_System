# Session: jules_cfd_v5_exact_results
*Időbélyeg: 2026-10-07T19:22:30.040867*

Jules CFD V5 Exact Pipeline Results — 2026-10-07

PIPELINE: jules_cfd_pipeline.py
- Input: features_dollar_bars.csv (CFD, $444K, shift(1) leakfix, ZZ merge)
- Features: 10 Jules exact (Tick_Speed, Dist_*_R/S, Stoch_State_M1, Wick_ATR)
- Label: V5 Strict Wick, PT=$1.5, SL=$1.0, max_bars=5
- LGBM: 781 trees, lr=0.0142, num_leaves=57, class_weight=balanced
- Threshold: P_LONG_MIN=0.350, P_SHORT_MIN=0.360, P_NOISE_MAX=0.470
- Filters: Stoch hard filter + Stability window=3

RESULTS:
| Metrika | OOS | Vizsga |
|---------|-----|--------|
| WR | 41.2% | 39.4% |
| Profit | $10 | $-22 |
| Trades | 325 | 1,479 |
| Long WR | 36.1% | 0.0% |
| Short WR | 44.2% | 39.4% |
| Swap% | 52.3% | 51.7% |
| WR gap | +1.8% (STABIL) |

DIAGNOSIS: ROSSZABB MINT VELETLEN (mindkét WR < 50%)

ROOT CAUSE:
1. Stoch hard filter blokkolja az osszes Long-ot vizsgan (Stoch < 0 gyakori)
2. Modell aszimmetrikus: Short dominans, Long alulreprezentalva
3. Swap > 50%: tobb mint fele predikcio rossz irany
4. Stability filter tul szigoru (3/3 egyezes) → csak 325 trade OOS-on

FILES:
- Script: /data/dev/projects/z-ai-copilot/src/jules_cfd_pipeline.py
- Model: /data/dev/projects/z-ai-copilot/models/jules_cfd/lgbm_jules_cfd_10feat.pkl
- Results: /data/dev/projects/z-ai-copilot/docs/jules_cfd/jules_cfd_results.json
- Viz: /data/dev/projects/z-ai-copilot/docs/jules_cfd/OOS_Jules_CFD.html + VIZSGA_Jules_CFD.html