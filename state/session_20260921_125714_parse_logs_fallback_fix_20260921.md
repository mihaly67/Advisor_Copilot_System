# Session: parse_logs_fallback_fix_20260921
*Időbélyeg: 2026-09-21T12:57:14.982285*

# parse_logs() Fallback Fix — 2026.09.21 12:20

## PROBLÉMA
VSCode újraindítás után a dashboard "Nincs aktív task"-ot mutatott.
OK: új session logban `inputTokens=undefined` a `[VscodeSessionHost] send()` sorokban,
így `INPUT_RE` nem illeszkedett → `latest_context=0`, `latest_cumulative=0`.

MÉG1 OK: a saját válaszszöveg (ami log-ba íródott) tartalmazta az `inputTokens=619075`
szót, amit a régi regex megtalált (false positive), beállította `latest_cumulative`-t,
így a fallback feltétel (`latest_cumulative == 0`) hamis lett.

## JAVÍTÁS (két változás, /data/mcp_server/tools/token_dashboard.py)

### 1. INPUT_RE szűkítés (sor 68)
RÉGI: `re.compile(r'inputTokens=(\d+)')`
ÚJ: `re.compile(r'\[VscodeSessionHost\].*?inputTokens=(\d+)')`
Így csak valódi API session host sorokban keres, nem response szövegben.

### 2. Fallback külön feltételekkel (sor 114-118)
RÉGI: `if latest_context == 0 AND latest_cumulative == 0 AND current_task_usages:`
ÚJ: külön if mindkettőre:
```python
if current_task_usages:
    if latest_context == 0:
        latest_context = current_task_usages[-1]["tokensIn"]
    if latest_cumulative == 0:
        latest_cumulative = sum(e["tokensIn"] for e in current_task_usages)
```

### 3. parse_logs bővítése (sor 82-100)
`current_task_usages` lista gyűjtése: csak a current_log Task usage bejegyzései.
Fallback: `latest_context` = utolsó Task usage tokensIn, `latest_cumulative` = összeg.

## TESZT EREDMÉNY
entries=764, context=394, cumulative=87387 — mindkettő > 0 ✅

## VERZIÓ
token_dashboard.py módosítva. .deb nem frissítve.
Dashboard fut: PID 1236183, --minimized