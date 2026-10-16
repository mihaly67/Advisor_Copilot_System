# Session: next_task_hud_integration
*Időbélyeg: 2026-09-27T01:42:40.311723*

## Következő Task: HUD Integráció

### Cél
Nav_v3_final modell (32 feature, WR=48.3%) bekötése a Jules által készített HUD-ba.

### Amit Jules készített
- `start_hud_v1.17.sh` — HUD indító script
- HUD valószínűleg ZMQ-n kommunikál az EA-val (port 5555-5557)

### Amit be kell kötni
1. `models/nav_v3_final/model.pkl` — a végleges modell
2. `models/nav_v3_final/features.txt` — 32 feature lista
3. Optuna küszöbök: th_L=0.42, th_S=0.44, th_NL=0.55, th_NS=0.56

### Lépések
1. Session csatlakoztatás — Jules munkakörnyezet felmérése
2. HUD konfig frissítése nav_v3_final modellre
3. ZMQ pipeline teszt (REQ/REP vagy PUB/SUB)
4. OOS forward-return equity curve validáció
5. navsystem_indicators_v3.py NAV_FEATURES_V3 lista szűkítése 32 feature-re

### Kontextus (már session-ben mentve)
- Session: nav_v3_final_complete — teljes pipeline dokumentáció
- Log: /data/Brain/_qwen_analysis/nav_v3_final_pipeline_log.md
- Modell: /data/dev/projects/z-ai-copilot/models/nav_v3_final/
