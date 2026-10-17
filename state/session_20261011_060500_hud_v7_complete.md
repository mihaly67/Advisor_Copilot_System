# Session: hud_v7_complete
*Időbélyeg: 2026-10-11T06:05:00.483436*

V7 HUD működik! 3 subchart + logolás:
- Sub1: MLP P(Long) zöld, tartomány 0.14-0.31, σ≈0.05
- Sub2: LGBM P(Long) kék, tartomány 0.16-0.44, σ≈0.11
- Sub3: ENS P(Long) zöld + conf piros + zajzónák + küszöb 0.50
- Signal mindig -1 (SHORT) — BTCUSD esésben
- Nincs GL crash, nincs name error, nincs float.copy() error
- Log: /tmp/hud_v7.log
- Fájl: /data/dev/projects/z-ai-copilot/src/hud_v7_cfd.py

Fontos javítások:
1. create_line name='' (üres) — nem lehet oszlopnév, mert library ellenőrzi
2. bid/ask = horizontal_line (nem create_line) — float.update() működik
3. legend(text='MLP P(Long)', lines=False) — statikus szöveg, nem vonalnevek
4. NoiseTracker csak bar_complete=True-kor frissül
5. predict_server logol: MLP= LGBM= ENS= értékeket

Következő lépések:
- Több bar (30+) → zajszintek stabilizálódnak
- Ha értékek mindig <0.5 → SHORT domináns, de lehet, hogy a modell kalibráció rossz
- Jobb oldali panelek (Feature 3D, AUC) — később
- Éles EA teszt (MT5 + Merkava)