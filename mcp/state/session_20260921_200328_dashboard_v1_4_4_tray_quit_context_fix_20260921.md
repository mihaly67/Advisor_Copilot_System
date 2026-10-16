# Session: dashboard_v1_4_4_tray_quit_context_fix_20260921
*Időbélyeg: 2026-09-21T20:03:28.467608*

# Dashboard v1.4.4 — Tray kilépés + kontextus reset + elnevezés javítás — 2026.09.21

## Hibák javítva:
1. **Tálca kilépés nem működött**: `act_quit` `self.close()`-t hívott → `closeEvent` elrejtette (hide) ahelyett, hogy kilépett volna.
   - JAVÍTÁS: Új `_do_quit()` metódus → `_force_quit_flag=True` + `QApplication.quit()`
   - `closeEvent` most ellenőrzi a flag-et: ha True → `event.accept()` (valódi kilépés), ha nem → `hide()` (tray-be)

2. **Token monitor nem zárható/frissíthető**: ugyanaz a `closeEvent` hiba.

3. **"Kumulatív" elnevezés csalóka**: 
   - `SESSION KUMULATÍV (inputTokens)` → `AKTUÁLIS SESSION (inputTokens)` (card title)
   - docstring + kommentek is javítva

4. **Előző task tokenjeit veszi figyelembe**: 
   - `parse_logs()` `latest_context` és `latest_cumulative` nem szűrtek `session_reset_ts` alapján
   - Csak `session_task_usages` (Task usage összeg) volt szűrve
   - JAVÍTÁS: az `inputTokens` olvasási loop-ba timestamp szűrés beépítve (line 135-138)
   - Most a kontextusablak és az aktuális session értékek is csak a reset utáni sorokat számolják

5. **Kontextus ablak 26% induláskor**: a fenti javítás megoldja — új dashboard indulás → `_task_start_ts=now` → csak az utána lévő log sorok számítanak

## Fájl: /data/mcp_server/tools/token_dashboard.py

## MEGJEGYZÉS: A terminál beragadt, nem lehetett .deb-et építeni vagy újraindítani.
## Felhasználónak kézi lépések:
1. Régi dashboard kill: `pkill -f token_dashboard`
2. Újraindítás: `python3 /data/mcp_server/tools/token_dashboard.py --minimized &`
   Vagy .deb rebuild ha szükséges

## Kód változtatások:
- Line 129-138: timestamp szűrés inputTokens olvasáskor
- Line 370: CardWidget title "AKTUÁLIS SESSION"
- Line 458: `act_quit.triggered.connect(self._do_quit)`
- Line 475-493: `_do_quit()` + `closeEvent()` újraírva `_force_quit_flag`-gel