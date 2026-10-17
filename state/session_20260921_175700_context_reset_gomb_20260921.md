# Session: context_reset_gomb_20260921
*Időbélyeg: 2026-09-21T17:57:00.946091*

# Token Dashboard — Kontextus Reset Funkció (Frissítés gomb)

## PROBLÉMA
A frissítés gombra kattintva a `parse_logs()` újra beolvassa a régi logot,
és mivel az új task még nem írt `inputTokens=X` sort, a régi 164K érték
megmaradt → hamis 128%. VSCode újraindítása vagy új task indítása nélkül
kell működnie.

## MEGVALÓSÍTÁS
**Fájl:** `/data/mcp_server/tools/token_dashboard.py`

### 1. Új flag-ek (__init__, sor 292-293)
```python
self._context_reset_active = False  # Frissítés gomb = kontextus reset
self._last_ctx_value = 0            # Előző ismert kontextus érték
```

### 2. _on_refresh_clicked() metódus (sor 507-525)
- `_context_reset_active = True`
- Gomb szöveg: "Resetelve ✓" (zöld háttér)
- Azonnali `refresh()` hívás

### 3. refresh() kontextus szakasz (sor 533-560)
- Ha `_context_reset_active`:
  - Ha `ctx_tokens > 0` ÉS `ctx_tokens != _last_ctx_value` → új érték!
    Reset feloldása, gomb vissza ("Frissítés")
  - Különben: `ctx_tokens = 0` (kontextus kártya üres)
- `_last_ctx_value` frissítése ha `ctx_tokens > 0`

### 4. Tray menü (sor 424-425)
"Frissítés" → "Kontextus reset (frissítés)" → `_on_refresh_clicked`

### 5. Gomb handler (sor 406)
`self.refresh` → `self._on_refresh_clicked`

## HASZNÁLAT
1. Dashboard mutatja a hamis 128%-ot (régi log érték)
2. Kattints a "Frissítés" gombra
3. Gomb → "Resetelve ✓" (zöld), kontextus kártya → "Új session — mérés indul" (0%)
4. Amint az új task első `inputTokens=X` sor megjelenik a logban
   (5s belül), a dashboard automatikusan átvált a helyes %-ra
5. Gomb visszavált "Frissítés"-re

## ÁLLAPOT
- Kód kész ✅
- Dashboard újraindítása SIKERTELEN — `run_commands` beragadt
- Felhasználó újraindíthatja manuálisan:
  ```bash
  pkill -f token_dashboard
  nohup /home/Jules/jules_venv/bin/python3 /data/mcp_server/tools/token_dashboard.py --minimized &
  ```