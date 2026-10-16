# Session: v104_viz_session_close
*Időbélyeg: 2026-09-30T00:58:00.488989*

# v1.04 Vizualizáció Session Zárás — 2026.09.30

## PROBLÉMA ÖSSZEFOGLALÓ
7 próbálkozás után sem sikerült elfogadható vizualizációt készíteni.

## FŐ ZŰRZAVAROK

### 1. Threshold zűrzavar
- THL=0.100, THS=0.100, THN=0.900 — ezek a predict_thr()-ban használt értékek
- Túl alacsony threshold → 1007 Long + 1141 Short / 4 Noise (2152 bars-ból!)
- Gyakorlatilag MINDENkit osztályoz L vagy S-nek, noise alig van
- Ez NEM reális — a modell túlzottan magabiztos
- **Következő session**: threshold optimalizálás kell (pl. THL=0.50, THS=0.50 vagy magasabb)

### 2. Színezési zűrzavar
- Több iteráció: #006400 vs #228B22 (ForestGreen), #8B0000 vs #B22222 (FireBrick)
- A "sötét vs világos" marker színek nem voltak konzisztensek a vonalakkal
- A vonalak #228B22/#B22222 voltak, a markerek kezdetben #006400/#8B0000
- Végül markerek is ForestGreen/FireBrick lettek, de ez sem volt elfogadható

### 3. Vizualizációs zűrzavar
- viz_v5.html minta volt a cél, de sosem lett pontosan olyan
- Panel 1: trade vonalak + marker háromszögek (túl sok trace — 2152 vonal + 5 marker)
- Panel 2: valószínűségek + threshold vonalak
- Panel 3: Label vs Prediction scatter
- A 2152 egyedi vonal trace BLOÁLTA a HTML-t (5.6 MB!) és lassú volt

## AMI MŰKÖDIK
- Model betöltés: lgbm_v104.pkl + features.txt (42 feat)
- OOS adat: labeled_oos_slope1.csv
- predict_thr() logika helyes (csak threshold rossz)
- HTML generálás sikeres, megnyitható
- Rács halványítás: #333333 a #111111 háttéren (post-process replace)

## AMI NEM MŰKÖDIK
- Threshold nem optimalizált
- Marker színek nem lettek jók
- Túl sok trace (2152 vonal) → lassú HTML
- Nem lett screenshot/PNG validáció

## KÖVETKEZŐ SESSION FELADATOK
1. **v1.04 modell javítás** — threshold optimalizálás (pl. ROC/PR curve alapján)
2. **Vizualizáció újragondolás** — OHLC candlestick Panel 1-en (nem 2152 vonal!)
3. **Színezés véglegesítése** — konzisztens paletta dokumentálva
4. **PNG export** — nem csak HTML, hanem screenshot is
5. **Referencia**: viz_v5.html megvan, abból kiindulni

## FÁJLOK
- Script: /data/dev/projects/z-ai-copilot/src/viz_v104_3day.py
- HTML: /data/dev/projects/z-ai-copilot/docs/v104/viz_v104_3day.html (5589 KB)
- Model: /data/dev/projects/z-ai-copilot/models/v104/lgbm_v104.pkl
- OOS: /data/dev/projects/z-ai-copilot/Master_csv/processed/labeled_oos_slope1.csv
- Referencia: /data/dev/projects/z-ai-copilot/docs/viz_v5.html