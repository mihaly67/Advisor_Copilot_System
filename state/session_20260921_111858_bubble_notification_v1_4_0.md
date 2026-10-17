# Session: bubble_notification_v1_4_0
*Időbélyeg: 2026-09-21T11:18:58.802212*

## Dashboard v1.4.0 — Buborék értesítés + bezárható ablak — 2026.09.21 11:18

### Változtatások:
1. **closeEvent egyszerűsítve**: X gomb = hide (nincs felugró üzenet "Tálcára minimalizálva")
2. **10 perces buborék értesítés** (`_show_bubble`): tray showMessage 8s időtartammal
   - Összesített státusz: költség, kontextus, session, GPU, Qwen
   - Ikon: ✅ Information / ⚠️ Warning / ⚠️ Critical
3. **refresh() kritikus tray üzenet TÖRÖLVE**: nem zargat 5s-onként
4. **Indításkori felugró üzenet TÖRÖLVE**: csak tray ikon, nincs buborék induláskor

### init.d script v1.4.0:
- `start-stop-daemon` helyett `runuser -l` + `nohup`
- PID file a Python folyamaté (pgrep -u $USER -f "token_dashboard.py")
- `XDG_RUNTIME_DIR=/tmp/runtime-Jules` beállítva
- stop: kill, 5x vár, kill -9, orphan shm törlés

### Teszt:
- start → 1 folyamat ✅
- stop → leáll ✅
- start újra → 1 folyamat ✅
- Dupla start → QSharedMemory blokkolja a 2. Python folyamatot ✅

### .deb v1.4.0: /data/mcp_server/state/zai-token-dashboard_1.4.0_all.deb
### Folyamat: 1 db (PID 754182), service indítás, --minimized, tray-only