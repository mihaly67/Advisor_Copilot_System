# Session: session_context_v2_cline_events_20260921
*Időbélyeg: 2026-09-21T21:26:12.121067*

# Session kontextus kártya v2 — Cline idle/running + saját log — 2026.09.21

## Változtatás (teljes átírás):
A 60s szünet heurisztika helyett **Cline log session események** alapján működik.

### Új függvények:
1. `_parse_ts(ts_str)` — ISO timestamp → datetime
2. `write_task_log(event_type, **kwargs)` — dashboard saját log írása
3. `read_dashboard_task_log()` — saját log visszolvasása (fallback)
4. `parse_cline_session_events(latest_log)` — Cline log session események
5. `get_session_context()` — teljes újraimplementálás

### Cline log események (regex):
- `Session status: running` → task indulás/folytatás
- `Session status: idle` → **task VÉGE** (biztos határ)
- `Session rebuilt for mode` → új task
- `Continuing idle session` → follow-up = új task

### Task határozás:
1. Utolsó `idle` → következő `running` = task kezdete timestamp
2. Ha nincs session esemény → fallback: saját dashboard log
3. Ha az sincs → fallback: első entry timestamp
4. Aktuális task = entries ahol `ts >= task_start_ts`

### Dashboard saját log: `/data/mcp_server/logs/token_dashboard_task.log`
- `2026-09-21T21:25:47 | TASK_START | ctx=753 | calls=1`
- `2026-09-21T19:19:53 | TASK_END | ctx=2035 | calls=3 | cost=0.0334`
- Dupla biztosíték: dashboard újraindítás után saját logból rekonstruál
- Csak állapotváltáskor ír (nem minden refresh)

### Kártya tartalom (7 sor):
1. Task indulás: 19:25:47 (2p 3mp) 🟢 AKTÍV — kék, bold
2. Kontextus: 753 (0.8K) — lila, nagy
3. 🟢 Hatékony kontextus — színes figyelmeztetés
4. Növekedés: +0 | Hívások: 1 — dim
5. Task költség: $0.0131 | Eff: $0.0174/1K — sárga
6. 💡 Tipp — dim

### Figyelmeztetési küszöbök (token input):
- < 10K: 🟢 Hatékony
- < 30K: 🟡 Mérsékelt
- < 60K: 🟠 Nehéz
- ≥ 60K: 🔴 TÚL HOSSZÚ — RESET

### Ablak: 680x620
### Fájl: /data/mcp_server/tools/token_dashboard.py (~700 sor)
### Dashboard fut, PID 3298320

## Teszt:
- get_session_context() = ctx=753, task_start=19:25:47, active=True, duration=7200s
- Saját log: `TASK_START | ctx=753 | calls=1` ✓
- Napi/összköltség nem módosítva ✓