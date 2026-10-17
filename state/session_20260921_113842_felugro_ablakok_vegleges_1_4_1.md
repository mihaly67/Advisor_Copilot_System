# Session: felugro_ablakok_vegleges_1_4_1
*Időbélyeg: 2026-09-21T11:38:42.370894*

# Dashboard v1.4.1 — Felugró ablakok végleges javítása — 2026.09.21 11:38

## Probléma
A v1.4.0-ban a `_show_bubble()` 10 percenként `QSystemTrayIcon.showMessage()`-et hívott.
KDE Plasma alatt a `showMessage()` nem csak tray buborékot ad, hanem **felugró értesítési ablakot** nyit.
A user hiába zárta be, 10 perc múlva újra feljött.

## Megoldás — v1.4.1
1. **`_show_bubble()` átírása** (sor 428-439):
   - Mindig: `self.tray.setToolTip(msg)` — tooltip frissítés (néma, nem nyit ablakot)
   - `self.tray.showMessage()` TÖRÖLVE — ez okozta a felugrókat
   - Csak figyelmeztetés/kritikus esetben: `subprocess.run(['notify-send', ...])` — KDE natív értesítés (bezárható, nem ugrik fel újra)
   - Information szint (normál): csak tooltip, semmilyen értesítés
   - Warning szint: notify-send `--urgency=normal`
   - Critical szint: notify-send `--urgency=critical`

2. **QMessageBox import törlése** (sor 24): nem volt használva sehol

3. **Desktop bejegyzés**: `StartupNotify=true` → `StartupNotify=false` (`/usr/share/applications/zai-token-dashboard.desktop`)

## Fájlok:
- `/data/mcp_server/tools/token_dashboard.py` — módosítva
- `/usr/share/applications/zai-token-dashboard.desktop` — StartupNotify=false
- `/data/mcp_server/state/zai-token-dashboard_1.4.1_all.deb` — új .deb

## Teszt:
- Kód fordítás: OK (py_compile)
- .deb telepítés: OK (dpkg -i)
- Szervíz újraindítás: OK (PID 880436, 1 folyamat, --minimized)
- `notify-send` elérhető: `/usr/bin/notify-send` ✅

## Folyamat állapot:
- 1 db folyamat fut (PID 880436), service indítás, --minimized, tray-only
- Nincs showMessage hívás a kódban (grep ellenőrizve)
- Nincs QMessageBox a kódban (csak import volt, törölve)