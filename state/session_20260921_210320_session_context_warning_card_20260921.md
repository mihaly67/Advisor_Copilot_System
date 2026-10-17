# Session: session_context_warning_card_20260921
*Időbélyeg: 2026-09-21T21:03:20.141440*

# Session kontextus kártya — figyelmeztető rendszer — 2026.09.21

## Változtatás:
A "SESSION TOKENEK" kártya átnevezve "SESSION KONTEXTUS"-ra, teljes átdesignolva.

### Új függvény: `get_session_context()`
- Bemásolja az összes Task usage entry-t a legutolsó Cline logból
- Task detektálás: 60s szünet utáni hívások = új task (előzőt ignorálja)
- Aktuális kontextus = utolsó tokensIn (élő kontextusablak méret)
- Kontextus növekedés = utolsó - első tokensIn az aktuális taskon belül
- Költség hatékonyság = task_cost / (task_in / 1000) = $/1K token

### Figyelmeztetési küszöbök (token input):
- < 10K: 🟢 Hatékony kontextus — "Optimális — folytasd a munkát"
- < 30K: 🟡 Mérsékelt — "Figyelj a kontextus növekedésre"
- < 60K: 🟠 Nehéz — "Zárj felesleges fájlokat, tömöríts"
- ≥ 60K: 🔴 TÚL HOSSZÚ — RESET ajánlott — "Új task / context reset = költség csökkenés"

### Kártya tartalom (5 sor):
1. Kontextus: X,XXX (X.KK) — lila, nagy
2. 🟢/🟡/🟠/🔴 figyelmeztetés — színes, bold
3. Növekedés: +/-XXX | Hívások: N — dim
4. Task költség: $X.XXXX | Eff: $X.XXXX/1K — sárga
5. 💡 Tipp — dim, kicsi

### Ablak: 680x600 (korábban 480→560→600)
### Tray tooltip: kiegészült `| CTX: X.KK`

## Teszt:
get_session_context() = current_context=2306, growth=+724, task_cost=$0.05, calls=3, 🟢 Hatékony
Dashboard fut, PID 3204935

## Fájl: /data/mcp_server/tools/token_dashboard.py (~530 sor)