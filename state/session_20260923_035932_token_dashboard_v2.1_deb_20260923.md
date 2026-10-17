# Session: token_dashboard_v2.1_deb_20260923
*Időbélyeg: 2026-09-23T03:59:32.398077*

# Token Dashboard v2.1 — .deb csomag telepítve

## Verzió: 2.1.0
## Fájlok:
- `/usr/bin/zai-token-dashboard` — fő script (PyQt5, 4 kártya)
- `/data/mcp_server/tools/token_dashboard.py` — forrás
- `/data/mcp_server/tools/gen_token_icon.py` — ikon generátor
- `/data/mcp_server/state/icons/zai-token-*.png` — ikonok (16-256px)
- `/usr/share/icons/hicolor/*/apps/zai-token-dashboard.png` — rendszer ikonok
- `/usr/share/applications/zai-token-dashboard.desktop` — alkalmazás menü bejegyzés
- `/home/Jules/.config/autostart/zai-token-dashboard.desktop` — autostart (tálcára indul --hidden)
- `/data/mcp_server/logs/token_dashboard.log` — saját log (5mp frissítés)
- `/data/mcp_server/state/cost_persistent.json` — perzisztens költség state

## 4 kártya:
1. ÖSSZES KÖLTSÉG — cost_persistent.json + VS Code log merge
2. MAI HASZNÁLAT — mai nap Task usage sorok (UTC→local szűrés)
3. TASK/SESSION — legutolsó Cline log fájl = jelenlegi session
4. P4000 GPU — nvidia-smi

## Ikon: $ jel + grafikon sávok + "Z.ai" felirat, Breeze Dark
## .deb: /tmp/zai-token-dashboard_2.1.0_all.deb
## Régi cline-token-dashboard.desktop autostart törölve