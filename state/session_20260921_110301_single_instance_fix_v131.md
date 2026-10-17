# Session: single_instance_fix_v131
*Időbélyeg: 2026-09-21T11:03:01.801848*

## Dashboard v1.3.1 — Duplikáció fix (single instance) — 2026.09.21 11:02

### Probléma: 3-5 dashboard indult (service + autostart + kezi)
### Megoldás: KETTŐS LOCK
1. **QSharedMemory** (Python szintű): `shared.create(1)` — ha már fut, azonnal kilép
   - Orphan shm kezelés: `attach()` + `detach()` törli az elárvult szegmenst induláskor
2. **PID file lock** (init.d szintű): `start-stop-daemon --make-pidfile`
   - `is_running()` ellenőrzi PID file-t induláskor
   - Ha már fut → "Már fut (PID xxx)." és exit 0

### init.d script javítások:
- `is_running()` függvény PID ellenőrzéssel
- `start`: orphan shm törlés induláskor (`ipcs -m | awk ... | ipcrm -m`)
- `stop`: graceful kill, majd 5x vár, majd kill -9
- `status`: PID file ellenőrzés
- `Provides: zai-token-dashboard` (volt: cline-token-dashboard)
- sleep 3 (volt 1) a start után

### Teszt eredmények (mind 3 indítási módszer):
1. `sudo service zai-token-dashboard start` → elindul (PID xxx)
2. `sudo service zai-token-dashboard start` újra → "Már fut" — nem indít újat ✅
3. `python3 token_dashboard.py --minimized` → QSharedMemory blokkol ✅
4. `/usr/bin/zai-token-dashboard --minimized` → QSharedMemory blokkol ✅
Eredmény: mindig 1 folyamat

### .deb v1.3.1: /data/mcp_server/state/zai-token-dashboard_1.3.1_all.deb (59K)
### Futtató folyamat: 1 db (PID 639875), service indítás, --minimized