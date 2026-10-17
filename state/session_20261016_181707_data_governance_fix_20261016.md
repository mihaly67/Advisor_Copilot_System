# Session: data_governance_fix_20261016
*Időbélyeg: 2026-10-16T18:17:07.683790*

# DATA GOVERNANCE FIX — 2026-10-16

## KRITIKUS HIBA FELFEDVE ÉS JAVÍTVA

### A hiba:
A pipeline NAPOKIG a `BTCUSD_külön_vizsga.csv`-vel tanított (4 nap vizsga adat)!
A "külön vizsga" = EXAM/OUT-OF-SAMPLE — SOHA nem szabad tanítani rajta!

### A javítás:
1. ✅ Adatkönyvtár szervezve: data/raw/ = TRAIN, data/exam/ = VIZSGA
2. ✅ Szimbolikus linkek létrehozva (nem duplikálunk GB-okat)
3. ✅ Minden szennyezett modell, predikció, chart TÖRÖLVE
4. ✅ Pipeline kód javítva (v4.py és v4_01.py) — ALWAYS loads train data
5. ✅ Tudástár dokumentálva: data_governance_rules.md

### Adatkönyvtár:
```
data/raw/BTCUSD/train_tick_BTCUSD.csv   → 880MB, 2.5 hónap (JUN-SEP 2026) = TANÍTÁS
data/raw/BTCUSD/M1_history_BTCUSD.csv   → 85MB, 2.7 év (2024-SEP 2026) = REFERENCIA
data/exam/BTCUSD/exam_tick_BTCUSD.csv   → 54MB, 4 nap (OCT 5-8 2026) = CSAK KIÉRTÉKELÉS
```

### Törölt fájlok:
- Összes BTCUSD_v4_*, v401_*, scalper_*, v3* modell
- Összes HTML/PNG chart
- Összes pipeline output (features, labels, pipeline_result)
- models/scalper/ most ÜRES (csak v3_optuna.db maradt)

### Pipeline kód változás:
- load_tick_data() MOST MINDIG a train adatot tölti
- Nincs több "use_full" switch — alapértelmezés = teljes 2.5 hónap
- Exam adat külön betölthető kiértékelésre

### Következő lépés:
PIPELINE FUTTATÁS a 2.5 hónap train adaton! (880MB, ~5M tick)