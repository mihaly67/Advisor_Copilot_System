# Session: FELBEKESZULT_FELUGRO_ABLAKOK_JAVITANDO
*Időbélyeg: 2026-09-21T11:30:05.273292*

# HOSSZÚ TASK — FÉLBEKÉSZÜLT, KÖVETKEZŐ TASKBAN FOLYTATANDÓ

## Probléma: Felugró ablakok még mindig jelennek meg

A user jelentése: hiába zárom be az ablakot, felugró ablakok jelennek meg.
A v1.4.0 javítások ellenére továbbra is zavaró felugrókat okoz valami.

## JAVÍTANDÓ — következő taskban:

### 1. Felugró ablakok kivizsgálása
- **Melyik kódsor** okozza a felugrást? Ellenőrizni kell:
  - `closeEvent` — már nem ad showMessage-t (v1.4.0 javítva)
  - `_show_bubble` — 10 perces buborék (ez szándékos, de lehet hogy zavaró)
  - `refresh()` — már nem ad showMessage-t (v1.4.0 javítva, de ellenőrizni!)
  - Indításkori `showMessage("Z.ai Dashboard", "Tálcán fut...")` — v1.4.0-ban törölve, de a kódot ELLENŐRIZNI KELL
  - **QMessageBox** — valahol használva van? `from PyQt5.QtWidgets import QMessageBox` — keresni kell `QMessageBox` hívásokat!

### 2. Konkrét javítandó fájlok:
- `/data/mcp_server/tools/token_dashboard.py` — fő dashboard kód
- `/etc/init.d/zai-token-dashboard` — service script (runuser indítás)
- `/home/Jules/.local/share/applications/zai-token-dashboard.desktop` — desktop bejegyzés
- `/home/Jules/.config/autostart/` — AUTOSTART nincs (törölve), de ELLENŐRIZNI KELL

### 3. Ellenőrzendő pontok:
- `grep -n 'showMessage' /data/mcp_server/tools/token_dashboard.py` — hány helyen hívja?
- `grep -n 'QMessageBox' /data/mcp_server/tools/token_dashboard.py` — van még QMessageBox?
- `grep -n 'showNormal\|show\|raise\|activateWindow' /data/mcp_server/tools/token_dashboard.py` — mikor jön elő ablak?
- A `_tray_activated` dupla kattintás `showNormal()` — ez OK, de lehet hogy más is hívja
- A `closeEvent` `event.ignore()` + `hide()` — ez elrejti, de ha valami `showNormal()`-t hív...

### 4. Lehetséges okok:
1. **Több folyamat** még mindig fut (QSharedMemory nem blokkolja megfelelően)
2. **Az init.d service újraindítja** a folyamatot amikor az meghal (Restart=on-failure nincs, de lehet hogy a service stop/start ciklus okozza)
3. **Autostart desktop bejegyzés** valahol még létezik és induláskor elindít egy másodikat
4. **A buborék értesítés** (`_show_bubble`) 10 percenként felugró ablakot nyit (nem csak tray buborék)
5. **QSystemTrayIcon.showMessage** egyes környezetekben ablakot nyit, nem buborékot

### 5. Javasolt megoldások következő taskban:
- **Minden `showMessage` hívást törölni** a refresh()-ből és closeEvent-ből (már megvan, de ellenőrizni)
- **A `_show_bubble`-t tesztelni**: vajon tray buborékot ad vagy ablakot nyit?
- **Ha a `showMessage` ablakot nyit**, akkor `_show_bubble`-t átírni: csak a tray tooltip frissítése (`self.tray.setToolTip(...)`), nincs showMessage
- **Az init.d service-t megszüntetni** és egyszerű autostart desktop bejegyzést használni (a service indítás bonyolult és több folyamatot okoz)
- **Egyetlen indítási pont**: csak `/home/Jules/.config/autostart/zai-token-dashboard.desktop` — semmi init.d, semmi service
- **QSharedMemory lock** marad a biztonság kedvéért

## Aktuális állapot:
- Dashboard fut: 1 folyamat (PID 754182), --minimized, service indítás
- .deb v1.4.0 telepítve: `/data/mcp_server/state/zai-token-dashboard_1.4.0_all.deb`
- MQL5 analízis: 32/88 RAG lekérdezés, 7.7 tok/s

## Fontos fájl path-ek:
- Dashboard kód: `/data/mcp_server/tools/token_dashboard.py`
- init.d script: `/etc/init.d/zai-token-dashboard`
- Wrapper: `/usr/bin/zai-token-dashboard`
- Desktop: `/usr/share/applications/zai-token-dashboard.desktop`
- Autostart: (nincs — törölve volt, de ellenőrizni)
- Ikonok: `/data/mcp_server/state/icons/zai-*.png`
- Log: `/data/mcp_server/logs/token_dashboard.log`
- PID file: `/tmp/zai-token-dashboard.pid`
- QSharedMemory key: `zai-token-dashboard-singleton`