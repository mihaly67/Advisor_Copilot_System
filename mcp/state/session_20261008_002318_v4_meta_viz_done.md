# Session: v4_meta_viz_done
*Időbélyeg: 2026-10-08T00:23:18.644554*

## V4 Meta Vizualizáció — KÉSZ

### 5 HTML vizualizáció generálva (14s):
1. `viz_cusum_Train.html` (6.8MB) — 42K bar CUSUM filter + event markers
2. `viz_cusum_Vizsga.html` (661KB) — 4K bar CUSUM filter + event markers
3. `viz_meta_OOS.html` (127KB) — Utolsó 500 bar: candlestick + Long/Short/Skip markers + CUSUM + P(follow)
4. `viz_meta_Vizsga.html` (954KB) — Teljes vizsga: candlestick + meta-label signals
5. `viz_meta_dashboard.html` (12KB) — Összehasonlító: WR, Profit, Direction WR, Meta javulás, Feature Imp, Gap

### Viz stílus: VIZ_STANDARD v1.0
- Dark theme (#111 bg, #000 paper)
- CDN Plotly (plotly-4.1.1)
- Zöld=Long, Piros=Short, Arany=Skip, Cián=s_pos, Parázs=s_neg

### Script: /data/dev/projects/z-ai-copilot/src/viz_v4_meta.py
### Output: /data/dev/projects/z-ai-copilot/docs/jules_cfd_v4_meta/
