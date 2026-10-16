# 🚧 HIÁNYOK ÉS BEÁLLÍTANDÓK — Teljes Roadmap

**Dátum**: 2026-10-13 | **Status**: Rendszer 60%-on — alapok megvannak, pipeline NEM fut

---

## 🔴 KRITIKUS — Pipeline nem működik

Ez a legnagyobb probléma. Minden infrastructure megvan, de **egy sikeres címkézés sem történt**.

### 1. Labeling Pipeline — NEM FUT
- **Probléma**: A TBM (Triple Barrier Method) pipeline sosem futott end-to-end
- **Mi kell**:
  - [ ] Adatforrás: BTCUSD/XAUUSD OHLCV adatok — honnan? (MQL5 live? CSV? SQLite?)
  - [ ] Dollar bar konverzió: `dollar_bar_threshold` concept_map-ból
  - [ ] TBM futtatása: `labeling.py::triple_barrier_labels` hívás valós adaton
  - [ ] Eredmény validáció: label-ek eloszlása (nem csak 0-k!), barrier hit arányok
  - [ ] Mentés: labeled DataFrame → SQLite vagy Parquet
- **Függőségek**: CUSUM filter, volatilitás (EWMA), barrier width számítás

### 2. Direction Features — NEM GENERÁLVA
- **Probléma**: A 6 direction feature (DF_Curve, Flow_Delta, PV_Corr, Mom_Persist, Vol_Adj_Mom, VR_1_4) sosem számolódott ki
- **Mi kell**:
  - [ ] Mindegyik feature implementációja vagy importja
  - [ ] Futtatás a labeled adatokon
  - [ ] AUC validáció — mind >0.55 kell (RSI/ADX TILTOTT mert ~0.53)

### 3. Meta-labeling — NEM FUT
- **Probléma**: Side model → meta model → size filter pipeline sosem futott
- **Mi kell**:
  - [ ] Első model: side prediction (+1/-1) — XGBoost/RF
  - [ ] Második model: meta-label (0/1) — size filter
  - [ ] PurgedKFold cross-validation
  - [ ] Sample weights: uniqueness × return × time_decay

---

## 🟡 FONTOS — Infrastructure hiányok

### 4. FAISS Similarity Search rag_query-be
- **Most**: SQL LIKE csak — nem szemantikus
- **Kell**: ml_vectorize_v2.py és brain_vectorize.py már van FAISS MiniLM-mel
- [ ] rag_query MCP tool: `mode='semantic'` → FAISS search hívás
- [ ] Index ellenőrzés: ml_rag_v2.db FAISS index friss-e

### 5. Qwen 14B modell letöltése
- **Most**: Csak 7B (5.07 GB) letöltve
- **Env.sh**: 14B az alapértelmezett, de GGUF hiányzik
- [ ] Letölteni: `Qwen/Qwen2.5-Coder-14B-Instruct-GGUF` q4_k_m.gguf (~9 GB)
- [ ] VRAM: 34/48 layer GPU-ra = ~7.5 GB — P4000 bírja, de szűken
- [ ] Benchmark: 14B vs 7B minőség (sebesség lassabb lesz)

### 6. Data Pipeline — adatforrás tisztázása
- **Probléma**: Nem clear honnan jön a OHLCV adat
- **Opciók**:
  - MQL5 terminal → SQLite (real-time BTCUSD/XAUUSD)
  - CSV fájlok (historical backtest)
  - CryptoCompare / Yahoo Finance API
- [ ] Döntés: melyik adatforrás?
- [ ] Adat séma: timestamp, open, high, low, close, volume
- [ ] Dollar bar aggregáció implementálás

### 7. Pipeline Orchestrator
- **Most**: Nincs end-to-end pipeline — minden külön script
- **Kell**:
  - [ ] `pipeline/run.py` — orchestrates: data→bars→label→features→model→backtest
  - [ ] Instrument config: concept_map `instruments[SYMBOL]`-ból
  - [ ] Logging + checkpoint (resume capability)
  - [ ] CLI: `python run.py --symbol BTCUSD --from 2024-01-01 --to 2025-01-01`

---

## 🟢 JÓ LENNE — Optimalizálások

### 8. VSCode Tasks + Launch configs
- [ ] `.vscode/tasks.json`: "Run Pipeline", "Run Backtest", "Qwen Analyze"
- [ ] `.vscode/launch.json`: Debug Python pipeline, Debug C++ backtest
- [ ] `.vscode/settings.json`: Workspace-specific Python path, test config

### 9. C/C++ Build System
- [ ] CMakeLists.txt a GPU-accelerált részhez (ha kell)
- [ ] llama.cpp C++ build optimalizálás
- [ ] sqlite-vec C extension build

### 10. RAG Index Frissítés
- [ ] ml_rag_v2.db: source_repo metadata javítás (mind "unknown")
- [ ] brain_rag.db: 89 repo re-index ha változott
- [ ] concept_map.json: új instrument hozzáadás workflow (EURUSD, SPX500)

### 11. Monitoring + Alerting
- [ ] Pipeline futás log → dashboard
- [ ] Model performance tracking (AUC, Sharpe, drawdown)
- [ ] GPU monitoring (Qwen vs training vs backtest)

### 12. Anti-Hallucination Enforcement
- [ ] Live LLM teszt: "implement TBM for XAUUSD" → protokoll aktiválódik?
- [ ] Cline hook: ha ML kód írás,强制 rag_query először
- [ ] Output validátor: generált kód vs concept_map referencia

---

## 📊 RENDSZER ÁLLAPOT ÖSSZEFOGLALÓ

| Komponens | Állapot | Készültség |
|-----------|---------|-----------|
| Knowledge index (L1-L4) | ✅ Működik | 95% |
| AGENTS.md grounding protocol | ✅ Megvan | 90% |
| MCP server + rag_query | ✅ Működik | 90% |
| Cline autoApprove | ✅ Minden true | 100% |
| VSCode extensions | ✅ Telepítve | 95% |
| Git config | ✅ Beállítva | 100% |
| Qwen 7B model | ✅ Letöltve + benchmarkolt | 100% |
| **Labeling pipeline** | ❌ **NEM FUT** | **0%** |
| **Direction features** | ❌ **NEM GENERÁLVA** | **0%** |
| **Meta-labeling** | ❌ **NEM FUT** | **0%** |
| **Data pipeline** | ❌ **NINCS** | **0%** |
| FAISS in rag_query | ⚠️ Csak CLI | 30% |
| 14B Qwen model | ❌ Hiányzik | 0% |
| Pipeline orchestrator | ❌ Nincs | 0% |

**Összkészültség: ~40%** — infrastructure jó, de a VALÓDI MUNKÁT (labeling, features, model) még senki nem csinálta!

---

## 🎯 PRIORITÁS SORREND (következő session)

1. **Adatforrás tisztázása** — MQL5-ből jön az adat? CSV? Döntés kell!
2. **Labeling pipeline futtatása** — akár 1 db sikeres TBM label-elés is haladás
3. **Direction features** — a 6 feature kiszámítása a labeled adatokon
4. **FAISS rag_query integráció** — szemantikus keresés MCP-n keresztül
5. **14B Qwen letöltés + teszt** — jobb minőség, de lassabb

A legfontosabb: **egy sikeres end-to-end futás** — adat→bar→label→feature→model. Minden más secondary.
