# Session: parse_logs_undefined_fix_20260921
*Időbélyeg: 2026-09-21T15:19:37.168166*

# Token Dashboard parse_logs() Fix — inputTokens=undefined (új session)

## PROBLÉMA
Amikor új VS Code session/task indul, a logban `inputTokens=undefined` jelenik meg.
A dashboard 128%-ot mutatott akkor is, amikor a task csak most kezdődött.
A napi költség és összköltség rendben voltak.

## GYÖKOK
1. **INPUT_RE regex** csak `inputTokens=(\d+)` mintát keresett. Ha a legutolsó
   API hívás `inputTokens=undefined`, a regex nem illeszkedett → a **régi 164K
   érték megmaradt** → hamis 128%.

2. **Fallback logika** (sor 116-117): ha `latest_context == 0`, beállította
   `current_task_usages[-1]["tokensIn"]`-t. De a Task usage `tokensIn` =
   teljes API input (cache+context), **NEM** a kontextusablak mérete. Ez is
   hamis nagy értéket adott.

## JAVÍTÁS
**Fájl:** `/data/mcp_server/tools/token_dashboard.py`

### 1. INPUT_RE regex kiterjesztése (sor 69)
REGI: `re.compile(r'\[VscodeSessionHost\].*?inputTokens=(\d+)')`
ÚJ: `re.compile(r'\[VscodeSessionHost\].*?inputTokens=(undefined|\d+)')`

### 2. parse_logs() undefined kezelés (sor 107-117)
Ha `raw == "undefined"`: `latest_context = 0` (régi érték nem marad!)
Ha szám és < 200K: `latest_context = val`
Ha szám és > 200K: `latest_cumulative = val`

### 3. Fallback logika szűkítése (sor 125-127)
Csak `latest_cumulative`-hez használja a Task usage-t.
`latest_context` NE a Task usage-ból számoljon — hamis 128%+ értéket adna.

### 4. Üres kontextus szöveg (sor 533)
"Nincs aktív task" → "Új session — mérés indul"

## EREDMÉNY
- Új session/task esetén: `latest_context = 0` → dashboard "Új session — mérés indul"
- Ha `inputTokens=X` (szám) jelenik meg a logban: helyes kontextus % jelenik meg
- Napi/össz költség továbbra is perzisztens (cost_persistent.json), nem érintett