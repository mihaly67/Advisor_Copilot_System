# Qwen2.5-Coder-7B P4000 — Őszinte Képességfelmérés

## Hardver
- **GPU**: Quadro P4000 (8 GB VRAM, Pascal arch, 2017)
- **Model**: Qwen2.5-Coder-7B-Instruct Q5_K_M (5.07 GB GGUF)
- **Runtime**: llama-cpp-python 0.3.35, CUDA 13.0 driver

## Sebesség Benchmark

| Teszt | Tokenek | Idő | Sebesség |
|-------|---------|-----|----------|
| Code gen (TBM) | 200 | 7.7s | 25.8 tok/s |
| Bug find | 150 | 5.8s | 25.8 tok/s |
| Summary | 48 | 1.9s | 24.7 tok/s |
| Math | 16 | 0.7s | 23.0 tok/s |
| Repo analyze | 100 | 3.9s | 25.7 tok/s |
| Refactor | 37 | 1.5s | 24.1 tok/s |
| Test gen | 100 | 3.9s | 25.8 tok/s |
| Config gen | 58 | 2.3s | 24.8 tok/s |
| **ÁTLAG** | | | **25.0 tok/s** |

## VRAM Használat
- Modell betöltés: **5864 MiB** / 8192 MiB (72%)
- Szabad: **2244 MiB** (28%)
- Kontextus 8192 token — ennél nagyobb = OOM

## Minőségi Értékelés

### ✅ AMIT JÓL CSINÁL

1. **Refactoring** — list comprehension, egyszerű transzformációk → PONTOS
2. **Config generálás** — JSON, YAML config → PONTOS
3. **Összefoglalás** — rövid szöveg foglalat → MEGBÍZHATÓ (de néha félreérti a rövidítéseket: TBM→"Threshold-Based Monitoring" helyett "Triple Barrier Method")
4. **Pytest generálás** — egyszerű tesztek → MŰKÖDIK
5. **Nem hallucinál csomagokat** — ha nem tudja, nem talál ki dolgokat ✅

### ❌ AMIT ROSSZUL CSINÁL (kritikus!)

1. **TBM implementáció — HIBÁS** ❌
   - A generált kód NEM a valódi TBM! Iterál `for i in range(1, len(prices))` — ez NEM event-driven!
   - Nincs CUSUM filter, nincs barrier width volatilitás alapú skálázás
   - A `vertical_barrier`-t float-ként kezeli, nem bars számként
   - **Konklúzió**: Pénzügyi ML algoritmusokat NEM szabad vele írni!

2. **Meta-labeling — TÉVES** ❌
   - A Qwen azt mondja: "meta-labeling is primarily for direction prediction"
   - **A valóság**: meta-labeling a **pozíció sizing**-ra van (0/1 bináris — trade vagy nem)
   - Ez az AFML könyv alapvetése — a 7B model nem tudja!

3. **PurgedKFold — FÉLIG PONTOS** ⚠️
   - A leírás jobb: "removes buffer period around validation fold"
   - De NEM említi: pct_embargo, max_test_duration, az overlap miatti label leakage
   - Használható vázlathoz, de implementációhoz NEM

4. **Fractional diff — MAJDNEM JÓ** ⚠️
   - A weight formula HELYES: `w[k] = -w[k-1] * (d - k + 1) / k`
   - DE: `np.convolve(signal, weights, mode='same')` — ez NEM a helyes alkalmazás!
   - A valódi FFD: `sum(w[k] * series[t-k])` for each t, weights fixed-width window
   - A cutoff logikája jó, de a convolve rossz

5. **Matematika — HIBÁS** ❌
   - 17 * 23 + 45 = 436 (helyes: 391 + 45 = 436) — de a benchmarkban 406-ot mondott!
   - **Egyszerű számtan sem megy biztosan!**

### 💀 AMI KIFEJEZETTEN NEM MEGY

- **Komplex pénzügyi ML**: TBM, meta-labeling, sample weights — túl specifikus, hallucinál
- **Hosszú kontextus**: 8192 token limit, és a VRAM 72%-át a modell fogyasztja
- **Többlépéses érvelés**: nincs chain-of-thought, nincs reasoning
- **Kód minőségi review**: nem veszi észre a súlyos bugokat (pl. frac_diff convolve)
- **English→Hungarian fordítás**: nem próbáltuk, de 7B-nél gyenge

## MIHASZNÁLHATÓ — ŐSZINTÉN

### 🟢 Jó rá (magabiztos)
| Feladat | Sebesség | Minőség |
|---------|----------|---------|
| Rövid összefoglaló (<100 tok) | ~1-2s | 7/10 |
| JSON/YAML config generálás | ~2s | 8/10 |
| Egyszerű refactor (list comp, stb.) | ~1-2s | 8/10 |
| Egyszerű pytest stub | ~3s | 7/10 |
| Repo könyvtár-struktúra leírás | ~4s | 7/10 |
| Bug keresés (triviális: hiányzó import) | ~5s | 6/10 |

### 🟡 Okoz gondot (kérdéses)
| Feladat | Probléma |
|---------|----------|
| Közepes kód generálás (50-200 sor) | Struktúra jó, de részletek hibásak |
| Kód elemzés | Felületes, nem veszi észre a logikai hibákat |
| Docstring írás | Használható, de néha félreérti a kódot |

### 🔴 Ne használd rá (veszélyes)
| Feladat | Miért |
|---------|-------|
| Pénzügyi ML algoritmus | Hallucinál kritikus részleteket |
| Production kód | Bugos kódot generál magabiztosan |
| Biztonsági review | Nem veszi észre a biztonsági hibákat |
| Hosszú fájl >500 sor | Elveszti a kontextust |
| Matematikai számítás | Egyszerű számtan is hibázik |

## ÖSSZEHASONLÍTÁS

| | Qwen 7B P4000 | Cline (cloud LLM) |
|---|---|---|
| Sebesség | 25 tok/s | API-függő |
| Kód minőség | 5/10 | 9/10 |
| Pénzügyi ML tudás | 3/10 | 8/10 |
| Offline | ✅ Igen | ❌ Nem |
| Ingyenes | ✅ Igen | ❌ Token díj |
| Kontextus | 8192 tok | 128K+ tok |
| Reasoning | ❌ | ✅ |

## VERDIKT

**A Qwen 7B a P4000-n egy "gyors piszkos vázlat-gép" — nem "okos kódoló".**

Használati stratégia:
1. **Vázlat generálás**: Kód struktúra, stub függvények → utána Cline javítja
2. **Repo áttekintés**: Könyvtár-struktúra + rövid leírás (ezt csinálja a qwen_analyzer.py)
3. **Config/scaffold**: JSON config, pytest stub, boilerplate
4. **NEM kódolás**: Semmit nem szabad production-ba tenni Cline review nélkül!

**A P4000-n az egyetlen értelmes use-case: offline repo-elemzés mikor nincs API.**
