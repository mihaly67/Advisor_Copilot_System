# Session: system_diagnosis
*Időbélyeg: 2026-10-11T12:32:02.049466*

RENDERSZINTŰ PROBLÉMA — modell nem kalibrált, zűrzavar élőben

Diagnózis:
- V7 HUD: info szöveg működik, chart ÜRES (3 subchart QWebEngine nem renderel)
- V5 HUD: chart működik, de görbék értelmezhetetlenek
- P(Long) MINDIG < 0.5 → mindig SHORT, soha Long
- P(Short) = 1 - P(Long) → tükörkép, felesleges vonal
- Bal felső LONG felirat rossz (V5 sig_eval logika hibás)
- AUC 0.8+ backtesten DE élőben P(Long) [0.15-0.35] — NEM KALIBRÁLT

Valós adatok (BTCUSD, 11 bar):
MLP: 0.14-0.31 σ=0.05 | LGBM: 0.11-0.49 σ=0.12 | ENS: 0.15-0.35 σ=0.07

Lehetséges okok:
1. Feature drift (élő adat ≠ tanítási adat)
2. RankGauss scaler rosszul transzformál
3. Backtest look-ahead bias
4. Modell overfitting
5. Kalibráció hiány (sigmoid output [0.15,0.35] nem [0,1])

Következő lépések (gép visszakapcsolás után):
1. V5 HUD + 5558 port + logolás (P(Long) csak, P(Short) eltávolít)
2. 100+ bar log → saját AUC számítás élő adaton
3. Feature importance + feature értékek tartománya logolása
4. Ha élő AUC ≈ 0.5 → modell újra tanítás szükséges

Fájlok:
- V7 HUD: /data/dev/projects/z-ai-copilot/src/hud_v7_cfd.py (chart üres, 3 subchart nem renderel)
- V7 test: /data/dev/projects/z-ai-copilot/src/hud_v7_test.py
- predict_server: /data/dev/projects/z-ai-copilot/src/predict_server.py
- V5 referencia: /data/ml/Knowledge_Base/External_Repos/hud_v5_cfd.py
- Log: /tmp/hud_v7.log (11 bar adat)