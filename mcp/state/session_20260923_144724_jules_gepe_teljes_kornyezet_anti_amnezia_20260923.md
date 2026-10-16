# Session: jules_gepe_teljes_kornyezet_anti_amnezia_20260923
*Időbélyeg: 2026-09-23T14:47:24.064706*

# Jules Gépe — Teljes Környezet Rögzítés (Anti-amnézia dokumentum)
*Időbélyeg: 2026-09-23*
*Figyelmeztetés: EZ A FŐ REFERENCIA DOKUMENTUM. Ha bármi hol van kérdés, IDE NÉZZ!*

## HARDVER
- **CPU:** Intel Xeon E5-2673 v4 @ 2.30GHz, 1 socket, 20 core, 40 thread
- **RAM:** 62 GB (48 GB szabad)
- **GPU 0:** NVIDIA Quadro P4000 (8 GB VRAM) — Qwen LLM fut itt
- **GPU 1:** NVIDIA Quadro P2000 (5 GB VRAM) — egyéb GPU feladatok
- **GPU driver:** 580.178.04
- **Lemez /data:** 219 GB (183 GB szabad) — adat, Brain, ml, mcp_server
- **Lemez /home:** 156 GB (34 GB szabad) — Jules home, venv, projektek
- **OS:** Linux Ubuntu
- **Wine:** MetaTrader 5 fut Wine alatt

## META TRADER 5
- **Útvonal:** `/home/Jules/.wine/drive_c/Program Files/MetaTrader 5 IC Markets EU/`
- **Scripts:** `.../MQL5/Scripts/`
- **Indicators:** `.../MQL5/Indicators/Indicators/`
- **Files (CSV kimenet):** `.../MQL5/Files/`
- **NEM kell Python MetaTrader5 csomag** — offline pipeline MT5 nélkül megy, EA Wine alatt fut

## PYTHON KÖRNYEZET
- **Központi venv:** `/home/Jules/jules_venv/`
  - `/home/Jules/jules_venv/bin/python3` (Python 3.11)
  - `/home/Jules/jules_venv/bin/pip`
- **Telepített csomagok:**
  - ta 0.11.0 — Feature engineering (RSI, MACD, MFI, Stoch, WPR, BB, EMA, ATR, ROC, Keltner)
  - lightgbm 4.7.0 — Modell
  - optuna 5.0.0 — Küszöb kalibráció
  - scikit-learn 1.8.0 — Metrikák
  - pandas 3.0.3 — Adatfeldolgozás
  - numpy 2.4.6 — Numerikus
  - joblib 1.5.3 — Modell mentés
  - pyzmq 27.2.0 — Éles copilot ZMQ
  - PyQt5 5.15.10 + pyqtgraph 0.14.0 — HUD GUI
  - matplotlib 3.11.1 — Vizualizáció
  - shap 0.51.0 — Feature importance heatmap
  - catboost 1.2.10 — (kísérleti, pipeline nem használja)

## MUNKATERÜLET — /data/dev
- **Gyökér:** `/data/dev/` — Git repo, központi fejlesztői munkaterület
- **README:** `/data/dev/README.md` — struktúra leírás
- **projects/** — Aktív projektek
  - `scalper-copilot/` — Jules eredeti LGBM_mlops projektje (MARAD, nézelődés, vizualizáció)
  - `hardver-monitor/` — Hardver monitor .deb csomagok
- **libs/** — Megosztott könyvtárak (common, mql5, pine-script)
- **docs/** — Dokumentáció (adr, api, guides)
- **data/** — Symlink nagy adatokhoz (brain-rag.db, ml-rag.db, mcp-state)
- **config/** — .env fájlok, Cline beállítások
- **scripts/** — Használati scriptek
- **logs/** — Központi log
- **venv/** — Python venv (EZ MÁR NEM A FŐ VENV! A /home/Jules/jules_venv/ az!)

## ÚJ PROJEKT: Z.ai Copilot
- **Név:** Z.ai Copilot
- **Munkaterület:** `/data/dev/projects/z-ai-copilot/` (LÉTREHOZANDÓ)
- **Cél:** 3 lépcsős pipeline: Tick gyűjtő → Dollar bar képző → Feature engineering
- **Adatforrás:** Scalper_Copilot_Miner_v1.mq5 (18 oszlop, 811 MB)

## JULES EREDETI PROJEKT (referencia, MARAD)
- **/home/Jules/LGBM_mlops/** — Jules eredeti projekt gyökér
- **/data/dev/projects/scalper-copilot/** — Ugyanaz (másolat/link)
- **/data/LGBM_copilot/** — Régebbi verzió (cache, data, docs, models, MT5, scripts, src)
- Ezekben van a pipeline Python scriptjei, modellek, dokumentáció
- **NEM TÖRÖLJÜK** — nézelődés, vizualizáció, referencia

## BRAIN ÉS RAG
- **/data/Brain/** — 76+ repo klón, _qwen_analysis/ elemzések
- **RAG v4 DB:** `/data/Brain/_vectorized/brain_rag.db` — 336,907 chunks, 133 repos
- **ML RAG DB:** `/data/ml/_vectorized/ml_rag_v2.db`
- **Qwen elemzések:** `/data/Brain/_qwen_analysis/` — Pipeline terv, NavSystem fordítás, Környezet

## MCP SZERVER
- **Szerver:** `/data/mcp_server/server.py`
- **LLM:** Qwen2.5-Coder-7B-Instruct (GGUF Q5_K_M, P4000 GPU-n)
- **Modell:** `/data/ml/hf_cache/qwen2.5-coder-7b-instruct-q5_k_m.gguf`
- **Session memória:** `/data/mcp_server/state/` — session_*.md fájlok
- **Conversations:** `/data/mcp_server/conversations/`
- **Tools:** `/data/mcp_server/tools/` (ml_vectorize_v2.py stb.)

## VECtorIZE / RAG SEARCH
```bash
DISPLAY=:0 CUDA_VISIBLE_DEVICES=0 python3 /data/mcp_server/tools/ml_vectorize_v2.py --search "keresőkifejezés" 2>&1 | head -30
```

## CLINE WORKSPACE
- **/home/Jules/zhipu_projekt/** — Cline VS Code workspace
- **memory-bank/** — activeContext.md, techContext.md, progress.md stb.
- **.clinerules/** — 8 fájl (universal, ml-python, mql5, typescript stb.)
- **.clineignore** — 201 sor (wine, venv, git stb. kizárva)
- **agents.md** — Fő projekt dokumentáció (MT5 EA + LGBM + LSTM Copilot)

## KULCS FÁJL ÚTVONALAK ÖSSZEFOGLALVA
| Mi | Hol |
|---|---|
| Cline workspace | `/home/Jules/zhipu_projekt/` |
| Központi venv | `/home/Jules/jules_venv/` |
| MT5 Wine | `/home/Jules/.wine/drive_c/Program Files/MetaTrader 5 IC Markets EU/` |
| Munkaterület | `/data/dev/` |
| Jules projekt (eredeti) | `/home/Jules/LGBM_mlops/` |
| Pipeline scriptek | `/home/Jules/LGBM_mlops/Micro_LGBM/src/` |
| Master CSV | `/home/Jules/LGBM_mlops/Master_csv/` |
| Z.ai Copilot (új) | `/data/dev/projects/z-ai-copilot/` (LÉTREHOZANDÓ) |
| Brain repók | `/data/Brain/` |
| Qwen elemzések | `/data/Brain/_qwen_analysis/` |
| MCP szerver | `/data/mcp_server/` |
| RAG DB | `/data/Brain/_vectorized/brain_rag.db` |
| Token Dashboard | `/usr/bin/zai-token-dashboard` (.deb telepítve) |

## PIPELINE TERV (rövid)
1. Tick gyűjtő (MQ5): Scalper_Copilot_Miner_v1 → 18 oszlop CSV ✅ KÉSZ
2. Dollar bar képző (Python): prado_dollar_bars.py módosítva
3. Feature engineering (Python): dom_feature_engineer_mtf.py módosítva + NavSystem v2.22 indikátorok
4. Labeling: dom_labeler_v5.py (NEM VÁLTOZIK)
5. Betanítás: train_lgbm_fusion_v5.py
6. SHAP + Optuna: feature szelekcó + 4D küszöb
7. KIESŐ: fuse_macro_to_dollar_bars.py