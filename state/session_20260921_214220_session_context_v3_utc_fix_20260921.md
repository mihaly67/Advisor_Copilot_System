# Session: session_context_v3_utc_fix_20260921
*Időbélyeg: 2026-09-21T21:42:20.828385*

# Session Kontextus Kártya v3 — UTC fix + zajszűrés + tömör layout — 2026.09.21

## 3 javítás:

### 1. 🔴 UTC→helyi idő konverzió (KULCSPROBLÉMA MEGOLDVA)
A Cline log `2026-09-21T19:38:01.249Z` formátumú — a `Z` = UTC.
A kód `datetime.now()`-val (CEST=UTC+2) hasonlított össze → 2 óra tévedés.

**Fix:**
- `_parse_ts(ts_str)`: ha `Z` suffix van, UTC-ként parse-ol, majd `time.altzone` offset-tel helyivé alakít
- Minden regex (SESSION_STATUS_RE, SESSION_REBUILT_RE, CONTINUING_IDLE_RE) és entries regex most a teljes timestampet fogja: `(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z?)`
- `timedelta` hozzáadva az importokhoz

**Eredmény:** task_start_ts = 21:38:01 (local), duration = 3.4p (helyes, nem 2 óra)

### 2. 🔧 pending→running zajszűrés
A Cline log minden API hívásnál küld `pending→running` párt (~10ms). Ez NEM task határ.
**Fix:** `parse_cline_session_events` most csak valódi task határokat gyűjt:
- `idle` → mindig jelentős (task VÉGE)
- `running` → CSAK ha előző esemény `idle`/`rebuilt` volt (új task kezdete)
- `pending→running` → ignorálva (belső hívás zaj)
- `Session rebuilt` / `Continuing idle` → mindig új task

Eredmény: 4 log fájl → 15 valódi esemény (volt 100+ zaj)

### 3. 📐 Tömör kártya layout (kevesebb üres hely)
- `setContentsMargins(10,6,10,6)` → `(8,3,8,3)` — kártya belső margin
- `setSpacing(2)` → `setSpacing(1)` — kártyán belüli sorköz
- `setMinimumHeight(size+6)` → `setMinimumHeight(size+2)` — label magasság
- `title_label.setMinimumHeight(16)` → `13`
- Grid spacing: `8` → `5`
- Main layout: `setSpacing(8)→5`, `setContentsMargins(10,10,10,10)→(8,6,8,6)`

### Teszt eredmény:
- task_start_ts: 2026-09-21 21:38:01 (helyi) ✓
- task_duration: 205s (3.4p) ✓
- task_active: True ✓
- task_calls: 19 ✓
- Saját log: `TASK_START | ctx=901 | calls=19` ✓
- Dashboard fut, PID 3366320