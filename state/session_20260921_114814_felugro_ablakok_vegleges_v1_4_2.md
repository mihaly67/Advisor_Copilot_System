# Session: felugro_ablakok_vegleges_v1_4_2
*Időbélyeg: 2026-09-21T11:48:14.599846*

# Dashboard v1.4.2 — Felugró ablakok VÉGLEGES javítás (hardware monitor is) — 2026.09.21 11:47

## Gyökérokozók (KETTŐ!)
1. **token_dashboard.py `_show_bubble()`**: 10 percenként `notify-send`-et hívott, és mivel a session kritikus volt, MINDEN 10 percben küldött értesítést — bezárod, 10 perc múlva újra jön
2. **hardware_monitor_v2.py** (sor 397, 420): `QSystemTrayIcon.showMessage()` hívások KDE-ben FELUGRÓ ABLAKOT nyitottak — closeEvent és process kill esetén

## Javítások v1.4.2
### token_dashboard.py
- `_show_bubble()`: csak ÁLLAPOTVÁLTOZÁSKOR küld notify-send-et (nem minden 10 percben)
  - `self._last_ctx_critical` / `_last_sess_critical` / `_last_warned` state tracking
  - Ha már critical és marad critical → nincs új értesítés
  - Csak ha non-critical → critical váltás van → notify-send
  - Mindig: `setToolTip(msg)` — tooltip frissítés (néma)

### hardware_monitor_v2.py (/usr/bin/)
- **Sor 397** closeEvent: `showMessage` → `setToolTip` (néma)
- **Sor 420** kill_process: `showMessage` → `setToolTip` (néma)
- Összes showMessage eltávolítva

## Eredmény
- `showMessage` hívások száma mindkét fájlban: **0**
- Token dashboard: 1 folyamat (PID 935621, --minimized, tray-only)
- Hardware monitor: 1 folyamat (PID 935471, --hidden)
- .deb: `/data/mcp_server/state/zai-token-dashboard_1.4.2_all.deb`

## Fájlok:
- `/data/mcp_server/tools/token_dashboard.py` — módosítva
- `/usr/bin/hardware_monitor_v2.py` — módosítva (showMessage → setToolTip)
- `/usr/share/applications/zai-token-dashboard.desktop` — StartupNotify=false (v1.4.1-ből)