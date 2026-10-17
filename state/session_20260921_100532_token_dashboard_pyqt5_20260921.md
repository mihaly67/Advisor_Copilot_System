# Session: token_dashboard_pyqt5_20260921
*Időbélyeg: 2026-09-21T10:05:32.186508*

## Token Dashboard PyQt5 — 2026.09.21 10:05

### Kesz PyQt5 dashboard
- Script: /data/mcp_server/tools/token_dashboard.py
- Inditas: /home/Jules/jules_venv/bin/python3 /data/mcp_server/tools/token_dashboard.py
- Process: PID 269744 (fut)

### Telepitve:
1. .desktop: /home/Jules/.local/share/applications/cline-token-dashboard.desktop
2. Autostart: /home/Jules/.config/autostart/cline-token-dashboard.desktop
3. SysVinit: /etc/init.d/cline-token-dashboard (update-rc.d defaults)

### Dashboard funkciok:
- Kontextus ablak meret (128K Z.ai GLM-4.5)
  - Figyelmeztetes 80%-nal (90K)
  - Kritikus 90%-nal (102K)
  - Uj task ajanlas 95%-nal (107K)
- Mai token hasznalat (IN/OUT/cost/calls)
- Kumulativ session (inputTokens)
  - Warn 500K, Critical 1M
- GPU P4000 statusz (VRAM, kihasznalas, temp)
- Qwen MQL5 statusz (phase, progress, tok/s)
- Optimális task ajanlas (hatralevo kerek szama)
- Figyelmezteto sav (szin kodolt: zold/sarga/piros)
- Rendszertalca (tray) icon
- 5s frissitesi timer

### Optimalis token kalkulacio:
- Kontextus ablak: 128K (131072)
- Rendszer prompt + tools: ~15K
- Hasznalhato: ~113K (116512)
- Atlag/kor: ~5K token (user+assistant+tool)
- Optimalis task hossz: 20-22 kor (~100K)
- Figyelmeztetes: 80K (80%)
- Uj task: 107K (95%)

### Status:
- Dashboard fut, nincs hiba
- MQL5: 21/88 RAG, 6.4 tok/s
- GPU: 56%, VRAM 7662 MB