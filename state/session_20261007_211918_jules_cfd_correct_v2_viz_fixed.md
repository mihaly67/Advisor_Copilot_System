# Session: jules_cfd_correct_v2_viz_fixed
*Időbélyeg: 2026-10-07T21:19:18.505613*

Jules CFD CORRECT v2 VIZ — 2026-10-07

KULCS JAVÍTÁSOK:
1. Stoch filter KI — csak threshold + stability(SW=2)
2. VIZSGA Dist_* normalizálás: ATR_M15 (M1 ATR) használata, nem dollár bar ATR!
3. merge_zz: ha CSV már tartalmazza a pivotokat, skip merge (duplikáció elkerülése)

EREDMÉNYEK (új model, M1 ATR normalizált Dist_*):
| Metrika | OOS | VIZSGA |
|---------|-----|--------|
| WR      | 43.0% | 43.6% |
| Gap     | -0.6% → STABIL! |
| Long WR | 39.5% | 44.7% |
| Short WR| 46.1% | 40.2% |

V2 VIZ (Stoch KI, SW=2):
| OOS: L:759 S:818 WR=45.6% |
| VIZSGA: L:1087 S:613 WR=43.7% |

FEATURE IMPORTANCE (M1 ATR normalizált):
Dist_Ter_S=11.14%, Dist_Ter_R=10.86%, Dist_Sec_S=10.55%...
Minden feature aktív (nem 0%!)

FILES:
- Viz script: /data/dev/projects/z-ai-copilot/src/viz_jules_cfd_correct_v2.py
- Pipeline: /data/dev/projects/z-ai-copilot/src/jules_cfd_correct.py
- OOS HTML: /data/dev/projects/z-ai-copilot/docs/jules_cfd/OOS_Jules_CFD_CORRECT_v2.html (584 KB)
- VIZSGA HTML: /data/dev/projects/z-ai-copilot/docs/jules_cfd/VIZSGA_Jules_CFD_CORRECT_v2.html (874 KB)