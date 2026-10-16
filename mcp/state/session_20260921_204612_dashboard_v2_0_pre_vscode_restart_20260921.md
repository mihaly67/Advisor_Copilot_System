# Session: dashboard_v2_0_pre_vscode_restart_20260921
*Időbélyeg: 2026-09-21T20:46:12.995575*

# Dashboard v2.0 — VS Code újraindítás előtt — 2026.09.21

## Állapot:
- VS Code újraindítás szükséges (terminál halott volt)
- Dashboard kód újraépítve: /data/mcp_server/tools/token_dashboard.py (479→483 sor)

## Dashboard v2.0 felépítés:
### 4 kártya (2x2 rács):
1. ÖSSZES KÖLTSÉG (ALL-TIME) — perzisztens JSON-ből
2. MAI HASZNÁLAT — Task usage logból
3. P4000 GPU — /usr/bin/nvidia-smi (teljes út, 10s timeout)
4. QWEN 14B MQL5 — log + lock fájl

### Elhagyott (hibás volt):
- Kontextus ablak, Session kumulatív, Optimális task ajánlás, Figyelmeztetés sáv, Buborék értesítés

### Tálca — működő:
- X gomb = valódi kilépés (closeEvent: tray.hide() + event.accept())
- Kilépés menü = QApplication.quit()
- Nincs closeEvent hack

### Kód javítások a v2.0-ban:
- parse_logs() → parse_cost_entries() (csak megbízható Task usage sorok)
- get_gpu_status(): /usr/bin/nvidia-smi teljes út, 10s timeout, returncode+parts ellenőrzés
- Nincs INPUT_RE, USABLE_CONTEXT, SESSION_WARN stb.
- Nincs add_bar(), QProgressBar

## Újraindítás UTÁN futtatni:
```bash
# QSharedMemory orphan lehet — ha nem indul:
python3 /data/mcp_server/tools/token_dashboard.py
# Ha "már fut" hiba:
# rm /dev/shm/zai-token-dashboard-singleton 2>/dev/null
# python3 /data/mcp_server/tools/token_dashboard.py
```

## Ha a 4 kártya nem látszik:
- Ablak méret: 680x480 (lehet hogy kicsi)
- Ha GPU/Qwen üres: nvidia-smi vagy log nem elérhető (de MCP list_gpu szerint P4000 aktív)

## Fájl: /data/mcp_server/tools/token_dashboard.py
## Cost state: /data/mcp_server/state/cost_persistent.json