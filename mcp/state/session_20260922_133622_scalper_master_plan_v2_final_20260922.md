# Session: scalper_master_plan_v2_final_20260922
*Időbélyeg: 2026-09-22T13:36:22.990604*

# SCALPER COPILOT MESTERTERV v2.0 — VÉGLEGES VÁZLAT

## DÁTUM: 2026.09.22.
## ÁLLAPOT: VÉGLEGES — minden más terv törölve

## FŐ ELVEK (felhasználó által meghatározva):
1. **Meglévő vázra építünk, hibákat kiküszöbölve** = működőképes. Nem nulláról.
2. **Predikció bővítés: GAF-CNN + LGBM** — ha együtt tud működni, egyesítjük vizualizációval (két eltérő módszer). Ha nem, egyedi predikció külön-külön. Alternatíva: egyik felülbírálja másikat, de marad külön mert két módszer = működő rendszer.
3. **Python EA MT5-re, grafikus kereskedelmi panellel.** Alkalmasnak kell lennie TV-re is. Önálló asztali chart TV, MT5 tálcán. Broker nem érzékeli.
4. **Platform-független:** A kulcs csak az API — melyik platformra csatlakozik. A logika platform-független.
5. **Robot irány TÖRÖLVE.** Copilot = ember-gép hibrid, manuális végrehajtás.
6. **Minden pontot külön tervezünk meg.** Ez a végleges vázlat.

## 3 LÉPCSŐ = KÉSZ COPILOT:

### LÉPCSŐ 1: Meglévő LGBM Copilot Hibajavítása → Működő Rendszer (2-3 hét)
- **Hét 1:** ÚJ CSV adatgyűjtés → meglévő pipeline (Dollar Bar → Feature → Label)
  - Kódok: `dom_feature_engineer_mtf.py`, `dom_labeler_v5.py`, `train_lgbm_fusion_v5.py`, `pipeline_master.py`
  - Hibák: merge_asof időbélyeg, lookahead bias, labeler edge case
- **Hét 2:** Tanítás + Vizsga
  - Offline betanítás LGBM (30-feature Super-Matrix, P4000)
  - Vakteszt (OOS blind) + SHAP + 4D aszimmetrikus küszöb (Optuna)
  - Gyorsított valós idejű szimuláció (10x-100x adatsor) → eredmény összehasonlítás
  - Ha egyezik → modell érvényesítve
  - Éles validáció: MT5 Demo, 48h continuous, latencia <5ms
- **Hét 3:** HUD hibajavítás → kiterjesztés
  - Kód: `hud_v1.16.py` (LWC QtChart + ZMQ SUB 5557 + PyQt5)
  - Hibák: ZMQ stabilitás, adatfrissítés
  - Bővítés: BUY/SELL/CLOSE gombok, P_Noise/Signal csúszkák, Dollar Bar progress, 4D threshold UI
- **KIMENET:** Működő LGBM Scalper Copilot + HUD

### LÉPCSŐ 2: GAF-CNN + GAN Predikció Bővítés (2-3 hét)
- **Hét 1:** GAF pipeline + CNN tanítás
  - Dollar Bar → GASF/GADF kép (`cnn_gaf-master/`)
  - 3-csatornás RGB (`scafe-master/`)
  - CNN tanítás ResNet18, PyTorch, P4000
- **Hét 2:** Predikció + Egyesítési teszt
  - Éles CNN inference: GAF→CNN→P_CNN (GPU <10ms)
  - **TESZT:** LGBM+CNN ensemble vs LGBM egyedül
    - Ha Win Rate ≥ LGBM+3% → EGYÜTT, egyesítés vizualizációval (HUD: LGBM sáv + CNN sáv + ensemble döntés + Grad-CAM)
    - Ha Win Rate < LGBM+3% → KÜLÖN-KÜLÖN, külön panelek, kereskedő dönt
  - Alternatíva: egyik felülbírálja a másikat, de MARAD KÜLÖN
- **Hét 3:** GAN (opcionális) + validáció
- **RAG források:** cnn_gaf-master (0.648), scafe-master (0.582), Series2GAF-master (0.547), Stock-Prediction-using-ANN-master (GAN)
- **KIMENET:** Működő predikciós rendszer: LGBM + (GAF-CNN ± GAN)

### LÉPCSŐ 3: Python EA + Kereskedelmi Panel — Platform-Független (2-3 hét)
- **Hét 1:** API absztrakciós réteg
  - Interfész: connect(), get_ticks(), get_bars(), get_positions(), order_send(), order_close(), get_account_info()
  - Implementációk: MT5API (MetaTrader5), TVAPI (CDP 9222), IBKRAPI (TWS), MockAPI
  - **A copilot logika NEM tudja melyik platformra csatlakozott**
- **Hét 2:** Kereskedelmi panel (grafikus)
  - Chart panel: LWC QtChart candlestick + LGBM/CNN overlay + GAF panel
  - Kezelő panel: BUY/SELL/CLOSE gombok, küszöb csúszkák, pozíció lista, equity curve
  - Platform választó: [MT5] [TV] [Mock]
- **Hét 3:** TV önálló asztali + MT5 tálcán + validáció
  - TV teljes képernyő, MT5 minimalizálva a tálcán
  - Broker védelem 3 réteg: MT5 tálcán, TV más app, magic=0, nincs EA charton
  - Broker telemetria: ÜRES
  - Éles próba: TV chart → API → MT5 → order → eredmény
- **RAG források:** metatrader-mcp-server, tradingview-mcp (84 eszköz), lightweight-charts
- **KIMENET:** Kész Copilot rendszer, platform-független

## TÖRÖLT TERVEK:
- SCALPER_MASTER_PLAN_v1.md (v1.0) — TÖRÖLVE
- SCALPER_MASTER_PLAN_v1.1.md — TÖRÖLVE
- SCALPER_MASTER_PLAN_v1.2.md — TÖRÖLVE

## EGYETLEN FENNÁLLÓ TERV:
- `/data/Brain/_qwen_analysis/SCALPER_MASTER_PLAN_v2.0.md` (22056 bájt)

## RAG KÖRNYEZET:
- 336,907 chunks, 133 repos, 3,234 edges, 2,903 MB DB
- Minden lépcsőhöz megvan a kód a RAG-ban: pipeline, feature engineering, labeling, training, GAF-CNN, GAN, MT5 API, TV API, lightweight charts

## MEGLÉVŐ KÓDBÁZIS:
- `mt5_live_copilot_v2.00.py` — élő copilot
- `train_lgbm_fusion_v5.py` — LGBM tanító
- `dom_feature_engineer_mtf.py` — 3MTF feature engineer
- `dom_labeler_v5.py` — labeler
- `hud_v1.16.py` — HUD (LWC QtChart + ZMQ SUB 5557)
- `pipeline_master.py` — pipeline orchestrator

## KÖVETKEZŐ LÉPÉS:
Lépcső 1 megkezdése — Hét 1: ÚJ CSV adatgyűjtés + pipeline hibajavítás