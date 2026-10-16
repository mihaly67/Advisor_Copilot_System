# LGBM Copilot — Fejlesztői Környezet

> **Hely:** `/data/LGBM_copilot/`
> **Lemez:** `/dev/sdb1` (219GB, 10% használat, 188GB szabad)
> **Cél:** MT5 EA + LGBM/LSTM copilot fejlesztés — Dollar Bar Triple Barrier módszerrel
> **Előd rendszer:** `/home/Jules/LGBM_mlops` (referencia, kritikai elemzés: `docs/analysis/`)

## Architektúra

```
MT5 EA (MQL5) → TCP Socket → Python Backend → LGBM/LSTM → ZMQ PUB → HUD
     ↑                                                           ↓
     └───────────── PRED|Signal|P_Long|P_Short|P_Noise ←──────────┘
```

## Mappastruktúra

| Mappa | Tartalom |
|-------|----------|
| `src/data_pipeline/` | Dollar Bar generálás, feature engineering (anti-leakage) |
| `src/labeling/` | Triple Barrier címkézés (ATR-alapú, anti-overlabeling) |
| `src/models/` | LGBM és LSTM modellek tanítása |
| `src/evaluation/` | Walk-forward CV, purged k-fold, multi-regime teszt |
| `src/live/` | Éles copilot backend (TCP 5555/5556, ZMQ PUB 5557) |
| `src/utils/` | Segédprogramok (adatbetöltés, normalizáció, stb.) |
| `data/raw/` | Nyers MT5 CSV adatok (tick, OHLCV) |
| `data/processed/` | Feldolgozott (Dollar Bar, fused features) |
| `data/labeled/` | Triple Barrier címkézett adatok |
| `data/exam/` | Vak vizsga adatok (out-of-sample) |
| `models/lgbm/` | LightGBM modellek (.pkl) |
| `models/lstm/` | LSTM modellek (.pth) |
| `models/scalers/` | Normalizációs paraméterek (.npy) |
| `scripts/mt5_collectors/` | MQL5 adatgyűjtő scriptek (.mq5) |
| `scripts/batch/` | Batch feldolgozó scriptek (.sh) |
| `config/` | Konfigurációs fájlok (JSON, YAML) |
| `notebooks/` | Jupyter notebookok (elemzés, vizualizáció) |
| `tests/` | Tesztek (anti-leakage, adatintegritás) |
| `logs/` | Futtatási naplók |
| `docs/architecture/` | Architektúra dokumentáció |
| `docs/methodology/` | Metodológia (Dollar Bar, Triple Barrier, 3MTF) |
| `docs/analysis/` | Qwen elemzések, kritikai elemzés |
| `MT5/Experts/` | EA forráskódok (.mq5) |
| `MT5/Scripts/` | MT5 scriptek (.mq5) |
| `MT5/Indicators/` | Indikátorok (.mq5) |
| `MT5/Include/` | Include fájlok (.mqh) |
| `cache/` | GPU cache, intermediate files |
| `_qwen_analysis/` | Qwen mélyelemzés kimenetek |
| `mcp/state/` | MCP session memóriák (320+ session, fejlesztési történet) |
| `mcp/context/` | MCP kontextus (memory.jsonl, MCTS fák, fejlesztési irányok) |
| `mcp/tools/` | MCP Python eszközök (Qwen, orchestrátor, vektorizáló) |
| `mcp/qwen_analysis/` | Brain Qwen elemzések (139 md — audit, diagnózis, pipeline) |
| `mcp/logs/` | Log elemzések (.md, .py — NEM .log) |
| `mcp/data/` | MCP adat (token optimizer, stb.) |
| `mcp/conversations/` | MCP beszélgetés szösszenetek |

## Fejlesztési elvek (a Jules rendszer hibáiból tanulva)

1. **Anti-leakage** — minden feature shift(1) előtt rolling, ZigZag csak real-time (MT5-ből)
2. **Feature konzisztencia** — training = evaluation = live (ugyanazok a feature-ök)
3. **ATR-alapú barrier** — nem fix dollar, volatilitás-skálázott
4. **Walk-forward validáció** — purged k-fold CV, multi-regime, multi-day
5. **Unified threshold** — egyetlen konfiguráció training/eval/live
6. **Dinamikus Dollar Bar threshold** — instrumentum-specifikus, EMA-based
7. **OOS LSTM training** — strictly out-of-sample LGBM predikciókkal

## 🛡️ Data Governance (KRITIKUS)

> ⚠️ **BUG FIX 2026-10-16**: Pipeline napokig vizsga (exam) adaton tanult — "külön vizsga" = out-of-sample!

| Adat | Fájl | Méret | Használat |
|------|------|-------|-----------|
| **Training** | `data/raw/{INSTR}/{INSTR}_training_tick.csv` | 880MB, 5.2M tick | ✅ TANÍTÁS |
| **Exam** | `data/exam/{INSTR}/{INSTR}_exam_tick.csv` | 54MB, 4 nap | ❌ CSAK kiértékelés |
| **M1 Reference** | `data/raw/{INSTR}/M1_history_{INSTR}.csv` | 85MB, 2.7 év | Referencia |

**Szabályok:**
1. `data/raw/` = TANÍTÁS, `data/exam/` = CSAK KIÉRTÉKELÉS
2. Pipeline ALAPÉRTELMEZÉSBEN training adatot tölt
3. Exam adat SOHA nem mehet a model.fit()-be
4. Szennyezett modellek TÖRÖLVE (2026-10-16)

## v4.01 Pipeline Újdonságok

- Meta-labeling (AFML Ch.3) — másodlagos szűrő
- Feature interactions (4 új) — tree már nonlinear, csekély hatás
- Dollar-bar signal threshold — adaptív
- Sample weights (AFML Ch.4) — **A/B: HURT AUC**, kikapcsolva (--no-weights)

## GitHub

- **Repo**: https://github.com/mihaly67/Advisor_Copilot_System
- **.gitignore**: venv/, *.log, *.deb, models/, charts/, CSV adatok NEM felküldve
