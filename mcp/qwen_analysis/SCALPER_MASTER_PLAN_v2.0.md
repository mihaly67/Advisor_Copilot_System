# 🔥 SCALPER COPILOT MESTERTERV v2.0

> **Alapelv:** Meglévő vázra építünk, hibákat kiküszöbölve → működőképes. Nem nulláról.
> **Szabály:** Minden lépcső működő rendszer. Nincs továbblépés amíg nem megy.
> **Platform-függetlenség:** A kulcs csak az API — melyik platformra csatlakozik. A logika platform-független.
> **Robot irány TÖRÖLVE.** Copilot = ember-gép hibrid, manuális végrehajtás.

---

## 🏗️ LÉPCSŐ 1: Meglévő LGBM Copilot Hibajavítása → Működő Rendszer

> A váz megvan. A kód megvan. A pipeline megvan. CSAK a hibákat kell kiküszöbölni.

### 1.1 Adatgyűjtés — Új CSV-vel Indulva

**Meglévő kódok (RAG-ból):**
- `Micro_LGBM/src/dom_feature_engineer_mtf.py` ✅
- `Micro_LGBM/src/dom_labeler_v5.py` ✅
-+ `Micro_LGBM/src/train_lgbm_fusion_v5.py` ✅
- `pipeline_master.py` ✅

**Feladat:** Új CSV adatgyűjtés → meglévő pipeline-n keresztül:

```
ÚJ CSV adatok (MT5 CopyTicks/CopyRates)
    ↓
Adatmérnökség: Dollar Bar aggregáció ($444k küszöb)
    ↓
Jellemzőmérnökség: 3MTF features (M15/M30 makro + mikro OBI/Z-score)
    ↓
Labelling: Anti-overlabeling (ATR távolság szűrő) → Long/Short/Noise
    ↓
Pipeline: Feature Fusion (merge_asof backward) → 30-feature Super-Matrix
    ↓
Tanító adat kész
```

**Hibák amiket ki kell küszöbölni:**
- ZMQ kapcsolat stabilitás (reconnect, heartbeat)
- Warmup cold start (15k tick → 1000 Dollar Bar)
- Feature merge időbélyeg igazítás (lookahead bias ellenőrzés)
- Labeler edge case: extrém volatilitás >40 pont ugrás

### 1.2 Tanítás + Vizsga + Módszertan

**Offline fázis (kész adatsoron):**
```
Betanítás: LightGBM (30-feature Super-Matrix)
    ↓
Vakteszt (Out-of-Sample blind test)
    ↓
SHAP feature fontosság elemzés
    ↓
4D Aszimmetrikus küszöb kalibráció (Optuna)
    ↓
Win Rate + Soft Win + Drawdown mérés
    ↓
Betanított modell (.txt) kész
```

**Gyorsított valós idejű tesztelés (reality simulation felgyorsítva):**
```
Offline adatsor → gyorsított stream (10x-100x sebesség)
    ↓
Python copilot: DollarBar → Feature → LGBM predict
    ↓
Jel generáció + küszöb szűrés
    ↓
Eredmény log → összehasonlítás offline vakteszt eredménnyel
    ↓
Ha egyezik → modell érvényesítve
```

**Éles validáció (normál sebAég):**
```
MT5 Demo → valós tick stream → teljes pipeline
    ↓
48h continuous run → crash nélkül
    ↓
Latencia: tick→inference→signal < 5ms
```

### 1.3 HUD Hibajavítás → Működő Kijelző

**MAglévő kód:** `hud_v1.16.py` (LWC QtChart + ZMQ SUB 5557 + PyQt5)

**Hibák kiküszöbölése:**
- ZMQ adatfogadás stabilitás
- P_Long/P_Short/P_Noise kijelzés frissítés
- Position Manager vonal frissítés
- Chart candlestick update valós időben

**Kiterjesztés (működő HUD-ra építve):**
- BUY/SELL/CLOSE gombok a chart panelen
- P_Noise + Signal küszöb csúszkák
- Dollar Bar progress bar ($X/$444k)
- 4D aszimmetrikus küszöb UI
- Soft Win indikátor (>0.75R)

**✅ LÉPCSŐ 1 KIMENET:** Működő LGBM Scalper Copilot + HUD. EA a charton, Python háttér, manuális végrehajtás.

---

## 🏗️ LÉPCSŐ 2: Predikció Bővítés — GAF-CNN + LGBM Együtt vagy Külön

> **Cél:** GAF-CNN (és9 és GAN predikció BŐVÍTÉE a meglévő LGBM mellé.
> Ha együtt tudnak működni → egyesítés vizualizációval (két eltérő módszer).
> Ha nem → egyedi predikció külön-külön.
> Alternatíva: egyik felülbírálja a másikat, de MARAD KÜLÖN mert két módszer.

### 2.1 GAF Képgeneráló Pipeline

| Feladat | RAG forrás |
|---|---|
| Dollar Bar → GASF/GADF kép | `cnn_gaf-master/` (0.648) |
| 3-csatornás RGB (GASF+GADF+MTF) | `scafe-master/` (0.582) |
| Paraméterezés: window_size, stride | `Series2G&F-master/` (0.547) |

### 2.2 CNN Betanítás + Predikció

| Feladat | RAG forrás |
2
|---|---|
| CNN tanítás (ResNet18, PyTorch, P4000) | `cnn_gaf-master/` |
| Predikció: GAF kép → P_CNN_Long/Short/Noise | Ugyanaz a 3 valószínűség |
| Grad-CAM hőtérkép (XAI) | `scafe-master/`, `captum-main/` |

### 2.3 GAN Bővítés (Opcionális)

| Feladat | RAG forrás |
|---|---|
| GAN + GAF-CNN → szintetikus adat augmentáció | `Stock-Prediction-using-ANN-master/` |
| Adatbővítés kevés adat esetén | Generatív hálózat |

### 2.4 Egyesítési Teszt — Együtt vagy Külön?

```
TESZT 1: LGBM + CNN ensemble (súlyozott)
    ↓
Ha Win Rate ≥ LGBM egyedül + 3%:
    → EGYÜTT MŰKÖDIK → Egyesítés vizualizációval
    → HUD: LGBM sáv + CNN sáv + ensemble döntés
    → Grad-CAM overlay (két eltérő módszer vizualizálva)

Ha Win Rate < LGBM egyedül + 3%:
    → NEM EGYÜTT → KÜLÖN-KÜLÖN predikció
    → Mindkettő jelet ad, de külön
    → Alternatíva: egyik felülbírálja a másikatAat
    → De MARAD KÜLÖN mert két módszer
    → HUD: LGBM panel + CNN panel (külön sávok)
```

**Vizualizáció (ha egyesíthető):**
```
┌──────────────────────────────────────────────────┐
│  LWC Candlestick Chart                            │
├──────────────────────────────────────────────────┤
│  LGBM:  ████████░░ P_Long=0.62  → LONG           │
│  CNN:   ███████░░░ P_Long=0.58  → LONG           │
│  ▶ ENSEMBLE: LONG ✅ (egyezés, magas confidence) │
├────────────────────┬─────────────────────────────┤
│  GAF Image         │  Grad-CAM (CNN figyelmi     │
│  (utolsó 50 DB)    │  fókusz hőtérkép)           │
└────────────────────┴─────────────────────────────┘
```

**Vizualizáció (ha nem egyesíthető):**
```
┌──────────────────────────────────────────────────┐
│  LWC Candlestick Chart                            │
├──────────────────────────────────────────────────┤
│  LGBM:  ████████░░ P_Long=0.62  → LONG           │
│  CNN:   ████░░░░░░ P_Short=0.45 → SHORT          │
│  ⚠ ELLENTMONDÁS — mindkettő külön jelet ad      │
│  → Kereskedő dönt: melyiket követi               │
├────────────────────┬─────────────────────────────┤
│  GAF Image         │  Grad-CAM                   │
└────────────────────┴─────────────────────────────┘
```

**✅ LÉPCSŐ 2 KIMENET:** Működő predikciós rendszer: LGBM + (GAF-CNN ± GAN). Vagy egyesítve vizualizációval, vagy külön-külön. Két módszer, működő rendszer.

---

## �&️ LÉPCSŐ 3: Python EA + Kereskedelmi Panel — Platform-Független

> **Cél:** Python EA MT5-re, grafikus kereskedelmi panellel (chart panel + kezelő panel).
> **Alkalmasság:** Ugyanez a panel TV-re is.
> **Architektúra:** Önálló asztali chart = TV, MT5 a tálcán. TV API-n kapja az adatokat, chartot épít.
> **Broker védelem:** MT5 a tálcán minimalizálva → broker nem érzékeli, hogy teljes képernyőn van más.
> **Platform-függetlenség:** A kulcs csak az API — melyik platformra csatlakozik.

### 3.1 Platform-Független API Absztrakciós Réteg

```
┌─────────────────────────────────────────┐
│  COPILOT LOGIKA (platform-független)     │
│  ├─ Feature Engine                       │
│  ├─ LGBM Inference                      │
│  ├─ CNN Inference (ha bekapcsolt)        │
│  ├─ Döntés fúzió                        │
│  └─ Jel generátor                       │
├─────────────────────────────────────────┤
│  API ABSZTRAKCIÓ (interfész)            │
│  ├─ connect(login, password, server)     │
│  ├─ get_ticks(symbol)                   │
│  ├─ get_bars(symbol, tf)                │
│  ├─ get_positions()                     │
│  ├─ order_send(symbol, type, vol, ...)  │
│  ├─ order_close(ticket)                 │
│  └─ get_account_info()                  │
├─────────────────────────────────────────┤
│  PLATFORM IMPLEMENTÁCIÓ                 │
│  ├─ MT5API  → MetaTrader5 Python lib   │
│  ├─ TVAPI   → TradingView CDP (9222)   │
│  ├─ IBKRAPI → Interactive Brokers TWS  │
│  └─ MockAPI → Teszt/szimuláció         │
└─────────────────────────────────────────┘
```

**A copilot logika NEM tudja, melyik platformra csatlakozott.** Csak az API interfészt látja.

### 3.2 Kereskedelmi Panel (Grafikus)

**Chart panel:**
- Lightweight Charts QtChart (candlestick + volume) — MÁR MEGVAN (`hud_v1.16.py`)
- LGBM probability sáv (P_Long/P_Short/P_Noise)
- CNN probability sáv (ha bekapcsolt)
- Dollar Bar progress
- GAF overlay (ha bekapcsolt)

**Kezelő panel:**
- BUY / SELL / CLOSE gombok
- P_Noise + Signal küszöb csúszkák
- 4D aszimmetrikus küszöb beállítás
- Pozíció lista (nyitott + függő)
- Equity curve + drawdown
- Kapcsolat státusz (MT5/TV/API zöld-pirok)
- **Platform vá) választó** (MT5 / TV / Mock)

### 3.3 TV Önálló Asztali Chart — MT5 a Tálcán

```
┌──────────────────────────────────────────────────┐
│  TV ASZ$TALI CHART (teljes képernyő)              │
│  ┌────────────────────────────────────────────┐   │
│  │  Lightweight Charts candlestick            │   │
│  │  LGBM HUD overlay                          │   │
│  │  CNN overlay (ha bekapcsolt)              "│   │
│  ├────────────────────────────────────────────┤   │
│  │  KEZELŐ PANEL                              │   │
│  │  [BUY] [SELL] [CLOSE]  |  Szimbólum: XAU  │   │
│  │  Noise: ██░░ 0.27       |  Signal: ██░ 0.33│   │
│  │  Pozíciók: 1 live, 0 pending               │   │
│  │  Kapcsolat: MT5 ✅ (tálcán)                │   │
│  └────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────┘
                        ↕ API
┌──────────────────────────────────────────────────┐
│  MT5 (TÁLCÁN, minimalizálva)                      │
│  ├─ Python EA: MT5API.connect()                  │
│  ├─ Adat: MT5API.get_ticks("XAUUSD")            │
│  ├─ Order: MT5API.order_send(magic=0)           │
│  └─ Broker telemetria: ÜRES (nincs chart inter.) │
└──────────────────────────────────────────────────┘
```

**Broker védelem — 3 réteg:**
1. **MT5 a tálcán** → broker nem lát chart interakciót (nincs EA a charton)
2. **TV a képernyőn** → broker nem tudja, hogy TV fut (más alkalmazás)
3. **Magic=0** → order manuálisnak látszik bróker felé

### 3.4 Ugyanez a Panel-Panel TV-Re Is

```
TV ASZTALI CHART
    ↕ TVAPI (CDP port 9222)
TRADINGVIEW DESKTOP
    ↕ Webhook / Pine Script
BROKER (TV közvetítés)
```

VAGY:

```
TV ASZTALI CHART
    ↕ MT5API
MT5 (tálcán)
    ↕ Broker
```

**A panel NEM tudja, honnan jön az adat.** Az API absztrakció kezeli.

**✅ LÉPCSŐ 3 KIMENET:** Működő Python EA + grafikus kereskedelmi panel. Platform-független (MT5/TV/IBKR). TV önálló asztal, MT5 tálcán. Broker nem érzékel. Kész Copilot rendszer.

---

## 📋 Lépcsők Összefoglaló

| Lépcső | Cél | Idő | Állapot |
|---|---|---|---|
| **1** 🔥 | **Meglévő LGBM hibajavítás → működő** | **2-3 hét** | **KÖVETKEZŐ** |
| **2** | **GAF-CNN + GAN predikció bővítés** | **2-3 hét** | |
| **3** | **Python EA + kereskedelmi panel (platform-független)** | **2-3 hét** | |

**3 lépcső = KÉSZ COPILOT RENDSZER.** Robot irány törölve. Minden további (auto-execution, alternatív modellek, multi-signal) jövőbeli bővítés.

---

## 🔑 Lépcső 1 Részletes Munkabontás

### H5t 1: Adatgyűjtés + Pipeline (hibajavítás)

| Nap | Feladat | Forrás |
|---|---|---|
| 1-2 | ÚJ CSV adatgyűjtés (MT5 CopyTicks/CopyRates, XAUUSD M1, 1-3 hónap) | MT5 Python API |
| 2-3 | Pipeline futtatás: CSV → Dollar Bar → Feature → Label | `pipeline_master.py`, `dom_feature_engineer_mtf.py` |
| 3-4 | Hibák: merge_asof időbélyeg, lookahead bias | RAG: `train_lgbm_fusion_v5.py` |
| 4-5 | Hibák: labeler edge case (extrém volatilitás, >40p ugrás) | `dom_labeler_v5.py` |

### Hét 2: Tanítás + Vizsga

| Nap | Feladat |
|---|---|
| 6-7 | LGBM betanítás (30-feature Super-Matrix, P4000 GPU) |
| 7-8 | Vakteszt (Out-of-Sample blind) + SHAP |
| 8-9 | 4D aszimmetrikus küszöb kalibráció (Optuna) |
| 9-10 | Gyorsított valós idejű szimuláció (10x-100x adatsor) |

### Hét 3: HUD + Éles Próba

| Nap | Feladat |
|---|---|
| 11-12 | HUD hibajavítás (ZMQ stabilitás, adatfrissítés) |
| 12-13 | HUD kiterjesztés (gombok, csúszkák, progress bar) |
| 2-15 | Demo forward test (MT5 demo, 48h continuous) |
| 15 | Éles próba 0.01 lot (ha demo OK) |

---

## 🔑 Lépcső 2 Részletes Munkabontás

### Hét 1: GAF Pipeline + CNN Tanítás

| Nap | Feladat | RAG forrás |
|---|---|---|
| 1-2 | Dollar Bar → GASF/GADF képgenerátor | `cnn_gaf-master/` |
| 2-3 | 3-csatornás GAF opció | `scafe-master/` |
| 3-4 | Címkék átvétele (dom_labeler_v5) | Meglévő |
| 4-5 | CNN tanítás ResNet18, PyTorch, P4000 | `cnn7gaf-master/` |

### Hét 2: Predikció + Egyesítési Teszt

| Nap | Feladat |
|---|---|
| 1-2 | Éles CNN inference: GAF→CNN→P_CNN (GPU <10ms) |
| 2-3 | Egyesítési teszt: LGBM+CNN9ensemble vs LGBM egyedül |
| 3-4 | HaBegyütt → egyesítés vizualizációval; Ha nem → külön |
| 4-5 | HUD bővítés: CNN panel, Grad-CAM, diszkrepancia |

### Hét 3: GAN (ha idő engedi) + Validáció

| Nap | Feladat |
|---|---|
| 1-2 | GAN adat augmentáció (ha kevés adat) |
| 3-5 | Vakteszt ensemble, demo forward, Win Rate összehasonlítás |

---

## 🔑 Lépcső 3 Részletes Munkabontás

### Hét 1: API Absztrakció

| Nap | Feladat | RAG forrás |
|---|---|---|
| 1-2 | Platform API interfész definíció (abc) | Tervezés |
| 2-3 | MT5API implementáció | `metatrader-mcp-server/MT5Connection` |
| 3-4 | TVAPI implementáció (CDP 9222) | `tradingview-mcp/` (84 eszköz) |
| 4-5 | MockAPI (szimuláció, teszt) | Implementálandó |

### Hét 2: Kereskedelmi Panel

| Nap | Feladat |
|---|---|
| 1-2 | Chart panel (LWC QtChart — már megvan) |
| 2-3 | Kezelő panel (gombok, csúszkák, pozíció lista) |
| 3-4 | Platform választó (MT5/TV/Mock) |
| 4-5 | Equity curve + drawdown + trade log |

### Hét 3: TV Asztali + MT5 Tálcán + Validáció

| Nap | Feladat |
|---|---|
| 1-2 | TV önálló asztali chart (teljes képernyő) |
| #-3 | MT5 minimalizálva a tálcán, API kapcsolat |
| 3-4 | Broker telemetria teszt (magic=0, nincs EA charton) |
| 4-5 | Éles próba: TV chart → API → MT5 → order → eredmény |

---

## 📐 Rendszerarchitektúra (Végleges)

```
┌──────────────────────────────────────────────────────────┐
│  ASZTALI COPILOT (Platform-Független)                     │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │  CHART PANEL                                       │   │
│  │  ├─ Lightweight Charts candlestick + volume        │   │
│  │  ├─ LGBM overlay (P_L/P_S/P_N sávok)             │   │
│  │  ├─ CNN overlay (P_CNN sáv + Grad-CAM)            │   │
│  │  └─ GAF image panel                                │   │
│  ├────────────────────────────────────────────────────┤   │
│  │  KEZELŐ PANEL                                     │   │
│  │  ├─ [BUY] [SELL] [CLOSE] [EMERGENCY STOP]         │   │
│ 9  ├─ Szimbólum, Timeframe, Lot méret                │   │
│  │  ├─ P_Noise / Signal küszöb csúszkák              │   │
│ % │  ├─ 4D aszimmetrikus küszöb                       │   │
│  │  ├─ Pozíció lista + equity curve                   │   │
│  │  └─ Platform: [MT5] [TV] [Mock]  Kapcsolat: ✅     │   │
│  └────────────────────────────────────────────────────┘   │
│                                                            │
│  ┌────────────────────────────────────────────────────┐   │
│  │  PYTHON EA (Háttérben)                             │   │
│  │  ├─ Dollar Bar Engine ($444k)                      │   │
│  │  ├─ Feature Engine (3MTF)                          │   │
│  │  ├─ LGBM Inference → P_Long/Short/Noise           │   │
│  │  ├─ CNN Inference → P_CNN_Long/Short/Noise        │   │
│  │  ├─ Döntés Fúzió (együtt vagy külön)              │   │
│  │  └─ API: order_send(magic=0)                      │   │
│  └────────────────────────────────────────────────────┘   │
│                         ↕                                 │
│  ┌────────────────────────────────────────────────────┐   │
│  │  API ABSZTRAKCIÓ                                   │   │
│  │  MT5API │ TVAPI │ IBKRAPI │ MockAPI               │   │
│  └────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────┘
                         ↕
┌──────────────────────────────────────────────────────────┐
│  PLATFORM (MT5 / TV / IBKR)                               │
│  ├─ MT5: tálcán, minimalizálva, magic=0                  │
│  ├─ TV: önálló asztali, CDP 9222                         │
│  └─ IBKR: TWS/Gateway                                     │
└──────────────────────────────────────────────────────────┘
```

---

## 🛡️ Broker Védelem Összefoglaló

| Réteg | Mit csinál | Broker látja |
|---|---|---|
| TV teljes képernyő | Kereskedő itt van, itt mozgat% az egeret | Semmit (más app) |
| MT5 a tálcán | Minimalizálva, Python API kapcsolat | Manuális order (magic=0) |
| Nincs EA a charton | Telemetria: üres | Nincs EA profilozás |
| API hívás | Python→MT5 order_send | Tiszta hálózati kérés |

**Broker számára:** Egy tálcán lévő MT5, amiben a kereskedő "manuálisan" ad le megbízásokat. Semmi gyanús.

---

## 📦 RAG Kódok Am!miket Használunk

| Lépcső | Kód | Forrás |
|---|---|---|
| 1 | `mt5_live_copilot_v2.00.py` | Meglévő LGBM_mlops |
| 1 | `dom_feature_engineer_mtf.py` | Meglévő |
| 1 | `dom_labeler_v5.py` | Meglévő |
| 1 | `train_lgbm_fusion_v5.py` | Meglévő |
| 1 | `hud_v1.16.py` | Meglévő HUD |
| 2 | `cnn_gaf-master/` | RAG — GAF pipeline |
| 2 | `scafe-master/` | RAG — 3-csatornás GAF + Grad-CAM |
| 2 | `Series2GAF-master/` | RAG — GAF paraméterezés |
| 2 | `Stock-Prediction-using-ANN-master/` | RAG — GAN +3GAF-CNN |
| 3 | `metatrader-mcp-server/` | RAG — MT5 API |
| 3 | `tradingview-mcp/` | RAG — TV CDP API |
| 3 | `lightweight-charts/` | RAG — Chart widget |

---

*Dokumentum: /data/Brain/_qwen_analysis/SCALPER_MASTER_PLAN_v2.0.md*  
*Készült: 2026.09.22. — v2.0: Meglévő váz +1 hibajavítás, platform-független, 3 lépcső*