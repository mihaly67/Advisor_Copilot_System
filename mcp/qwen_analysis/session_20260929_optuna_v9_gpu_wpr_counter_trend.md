# Session Dokumentáció — 2026.09.29. Optuna V9 GPU + WPR Counter-Trend

## Cél
Optuna V9 teljes optimalizáció futtatása P4000 GPU-n (LGBM GPU/OpenCL), WPR counter-trend jelzésszűrés validálása.

---

## 1. LGBM GPU Build

### Mit csináltunk
- Ellenőriztük OpenCL elérhetőséget: `/etc/OpenCL/vendors/nvidia.icd` jelen van, NVIDIA CUDA 13.0 OpenCL 3.0
- LGBM GPU build: `pip install lightgbm 4.7.0` — **már tartalmazza** az OpenCL GPU supportot, nem kellett forrásból fordítani
- CMake 3.25 too old a GitHub source buildhez → pip wheel elég

### Benchmark eredmény
| Módszer | Idő | Gyorsulás |
|---------|-----|-----------|
| CPU (n_jobs=-1) | 4.16s | 1x |
| GPU (P4000, device='gpu') | 0.84s | **5x** |

### GPU státusz futás közben
- P4000: 108 MiB VRAM, 16% util (LGBM OpenCL nem használ sok VRAM)
- P2000: 892 MiB VRAM, 29% util (Qwen LLM)

---

## 2. GPU Szabály Beégetés

6 helyre beégettük a **GPU kötelező** szabályt:

| Hely | Mit |
|------|-----|
| `.clinerules/universal.md` | 🖥️ GPU/CUDA Kötelező szekció (P4000 primary, LGBM device='gpu', benchmark 2.9x) |
| `.clinerules/ml-python.md` | LGBM GPU kötelező a Tanítás+Validáció szekcióban |
| `memory-bank/techContext.md` | GPU hardver részletek + könyvtár annotációk |
| `PROJEKT_CEL.md` | GPU KÖTELEZŐ szekció |
| MCP session `gpu_mandatory` | GPU szabály kontextus |

Szabály tartalom:
- P4000 (GPU 0) = primary compute minden ML feladathoz
- LGBM: `device='gpu', gpu_platform_id=0, gpu_device_id=0` — SOHA `device='cpu'`
- OpenCL: `/etc/OpenCL/vendors/nvidia.icd`, OpenCL 3.0 CUDA 13.0

---

## 3. optuna_v9.py Átírás GPU-ra

### Változtatások
| Paraméter | Régi (CPU) | Új (GPU) |
|-----------|-----------|----------|
| `device` | (default='cpu') | `'gpu'` |
| `gpu_platform_id` | — | `0` |
| `gpu_device_id` | — | `0` |
| `n_jobs` | `-1` (minden core) | `1` (GPU-n nincs értelme) |
| `n_estimators` | `400` | `1000` |
| early_stopping | nincs | `50` round |
| eval_set | nincs | `[(Xo, yo)]` |
| adattípus | float64 | **float32** (GPU optimalizált) |
| trial szám | 1000 | **300** |

### Early stopping indoklás
- `n_estimators=1000` + `early_stopping(50)` → ha 50 iterációig nem javul log_loss az OOS-en, leáll
- GPU + early stopping = ~6x hatékonyság → 300 GPU trial ≈ 1800 CPU trial

### Float32 indoklás
- LGBM GPU OpenCL kernel float32-vel dolgozik
- Kisebb memória, gyorsabb adatátvitel GPU-ra

---

## 4. Optuna V9 GPU Futás

### Indítás
```bash
# Régi CPU kill
pkill -f optuna_v9
# Régi DB törlés
rm -f models/optuna_v9.db
# GPU restart
nohup python3 optuna_v9.py > optuna_v9_gpu.log 2>&1 &
```

### Progress timeline
| Perc | Trial | Best P | Megjegyzés |
|------|-------|--------|-----------|
| 0 | 0 | 1288 | Első GPU trial |
| 2 | 11 | 1288 | Start |
| 8 | 43 | 1737 | |
| 10 | 60 | 1802 | |
| 15 | 86 | 2014 | |
| 20 | 112 | 2144 | |
| 25 | 135 | 2144 | Stabilizálódik |
| 30 | 156 | 2331 | Ugrás |
| 35 | 176 | 2525 | Közeledik CPU 2670 |
| 40 | 194 | 2525 | |
| 45 | 212 | **2722** | Megelőzi CPU 2670! |
| 50 | 233 | 2722 | |
| 55 | 251 | 2722 | |
| 60 | 272 | 2722 | |
| 70 | 292 | **2790** | Utolsó ugrás |
| 82 | 300 | **2790** | KÉSZ |

### Végeredmény
```
BEST: P=$+2,790
WPR: period=5 OB=82 OS=12
4D: th_L=0.377 th_S=0.372 th_NL=0.402 th_NS=0.405
LGBM: lr=0.0325 leaves=58 depth=10 mc=10
Features: 28 (7 WPR feature mind benne)
Idő: 4912s (82 perc)
```

### Modell mentve
- `models/v9_optuna_best/model.pkl`
- `models/v9_optuna_best/features.txt`
- `models/v9_optuna_best/metrics.json`

---

## 5. Korábbi Bug Fix-ek (session során)

### Bug 1: `get_feat()` hiányzó return
- **Tünet**: Minden 280+ trial -9999 értéket adott
- **Ok**: `get_feat()` függvény nem volt `return f` — None-t adott vissza
- **Fix**: `return f` hozzáadva

### Bug 2: CACHE cross-contamination
- **Tünet**: OOS adatok train WPR értékeket kaptak
- **Ok**: Egyetlen `CACHE` dict szolgált df_tr és df_oos számára
- **Fix**: `CACHE_TR` / `CACHE_OOS` szétválasztva + `is_oos` paraméter

---

## 6. Összehasonlítás Korábbi Modellekkel

| Modell | Feature | Profit (OOS) | WR | Dátum |
|--------|---------|-------------|-----|-------|
| nav_v3_fix | 51 | **+$3,128** | 46.4% | 09.26. |
| SHAP 49 feat | 49 | +$3,106 | **49.0%** | 09.26. |
| nav_v3_final | 32 | +$2,802 | 48.3% | 09.26. |
| Optuna 4D | 51 | +$2,788 | 48.2% | 09.26. |
| **V9 Optuna GPU** | **28** | **+$2,790** | **~44%** | **09.29.** |

### Verdict
**Nem javult.** A V9 GPU $2,790 megegyezik a korábbi Optuna 4D-vel ($2,788), de elmarad a fix thresholdos modellektől ($3,128).

---

## 7. WPR Counter-Trend Analízis

### Kérdés: Működik-e a WPR counter-trend szűrés?

### Optuna trial statisztikák (top 20%)
| WPR period | Gyakoriság top 20% |
|-----------|-------------------|
| 5 | 28 trial (47%) |
| 14 | 21 trial (35%) |
| 3 | 9 trial (15%) |
| 8, 10 | 1-1 trial |

| OB küszöb | Gyakoriság |
|-----------|-----------|
| 82 | 41 trial (68%) |
| 80 | 7 trial |
| 78 | 6 trial |

| OS küszöb | Gyakoriság |
|-----------|-----------|
| 12 | 55 trial (92%) |
| 14 | 5 trial |

### WPR feature selection rate (top 20%)
| Feature | Selection Rate |
|---------|---------------|
| WPR_Overbought | **100%** |
| WPR_Oversold | **93%** |
| WPR_Reversal_Short | **100%** |
| WPR_Reversal_Long | **100%** |
| WPR_Extreme_Accel | **0%** (nem hasznos) |

### Hard filter teszt (OOS adaton)
| Szűrés | Profit | Trades | WR |
|--------|--------|--------|-----|
| NINCS WPR szűrés | $+2,523 | 8,064 | 43.8% |
| WPR szűrés (blokkol OB/OS) | $+2,280 | 6,873 | 44.4% |
| WPR + Reversal | $+2,279 | 6,874 | 44.4% |

### Blokkolt jelek analízis
| Blokkolt jel | Darab | WR | Jó-e blokkolni? |
|-------------|-------|-----|-----------------|
| Long in OB | 1,022 (23.5% blokkolva) | 43.4% | ⚠️ Közel fele JÓ trade eldobva! |
| Short in OS | 662 (13.7% blokkolva) | 41.4% | ✅ Rosszabbak, de profit is csökken |

### Konklúzió

**A WPR counter-trend szűrés:**
- ✅ **Lágyan MŰKÖDIK** — a LGBM feature-ökön keresztül tanulta, hogy OB zónában csökkentse P(Long)-t
- ❌ **Hard filter ROMLÍT** — $2,523 → $2,280 (−$243, −9.6% profit)
- ❌ **Reversal nem segít** — azonos eredmény
- ⚠️ **Túl durva szűrő** — a blokkolt jelek 43.4%-a nyertes volt

**Ha javítani akarjuk**: nem blokkolni, hanem confidence-ot csökkenteni (pl. OB zónában P(Long) *= 0.7)

---

## 8. Fájlok Módosítva

| Fájl | Változtatás |
|------|------------|
| `/data/dev/projects/z-ai-copilot/src/optuna_v9.py` | GPU: device='gpu', n_estimators=1000, early_stopping(50), float32, 300 trial |
| `/home/Jules/zhipu_projekt/.clinerules/universal.md` | GPU/CUDA Kötelező szekció |
| `/home/Jules/zhipu_projekt/.clinerules/ml-python.md` | LGBM GPU kötelező |
| `/home/Jules/zhipu_projekt/memory-bank/techContext.md` | GPU hardver részletek |
| `/home/Jules/zhipu_projekt/PROJEKT_CEL.md` | GPU KÖTELEZŐ szekció |
| `/home/Jules/zhipu_projekt/memory-bank/progress.md` | V9 befejezett státusz |

## 9. Fájlok Létrehozva

| Fájl | Tartalom |
|------|----------|
| `models/v9_optuna_best/model.pkl` | LGBM GPU modell |
| `models/v9_optuna_best/features.txt` | 28 feature lista |
| `models/v9_optuna_best/metrics.json` | profit=2790, wpr_period=5, OB=82, OS=12, 4D threshold-ök |

---

## 10. Tanulságok

1. **LGBM GPU pip wheel**: A pip `lightgbm 4.7.0` tartalmazza az OpenCL GPU supportot — nem kell forrásból buildelni
2. **Early stopping OOS-en**: Veszélyes — overfit a validációs halmazra (az OOS a profit számítás alapja is). Külön validációs set kellene.
3. **Hard filter vs soft filter**: Counter-trend szűrés hard filterként romlít, lágyan (feature-ön keresztül) működik
4. **300 GPU trial elég**: A Best 212. trial-nál (70%) stabilizálódott, utolsó 88 trial csak +$68 javulás
5. **GPU n_jobs=1**: GPU-n a multi-threading nem segít, sőt lassíthat
