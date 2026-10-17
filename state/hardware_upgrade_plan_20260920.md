# Hardver Fejlesztési Terv — 2026.09.20

**Státusz: 🔴 VÁRAKOZÓ — felhasználó jelzi ha rendelkezésre áll**

---

## Vásárlási lista

| Tétel | Mennyiség | Becsült ár (eFt) | Megjegyzés |
|-------|-----------|------------------|-----------|
| 32GB DDR4 ECC 2133 MT/s | **4 db** | 90-120 | Crucial/Samsung/Micron, RDIMM vagy UDIMM a lapka szerint |

**Összköltség: ~90-120 eFt**
**SSD: NEM KELL** — `/data` 188GB szabad, modellek oda mennek
**NVMe: NEM KELL**

---

## RAM elrendezés a frissítés után

```
Slot 1-4: 4×32GB = 128 GB  ← ÚJ (vásárolni)
Slot 5-8: 4×8GB  =  32 GB  ← MEGLEVŐ (bennt marad)
────────────────────────────
Összesen:          160 GB
Sávszélesség:      4-csatorna × 2 DIMM/csatorna = MAXIMÁLIS
```

A meglévő 4×8GB bent marad → 4-csatornás dual-rank = maximális memória sávszélesség.
A 4×8GB tartalék vagy eladható.

---

## Rendszer architektúra a frissítés után

### GPU-k

| GPU | VRAM | Funkció |
|-----|------|---------|
| **P4000** | 8 GB | CUDA compute — Qwen3-8B teljesen GPU-n (~100 tok/s) |
| **P2000** | 5 GB | Display only — X server, Heaven benchmark |

### CPU

| Paraméter | Érték |
|-----------|-------|
| Modell | Xeon (40 szál) |
| RAM | 160 GB DDR4 ECC 2133, 4-csatorna |
| SSE/AVX | AVX2 (llama.cpp optimalizált) |

---

## Modell architektúra — három modell, rétegzett inferencia

### 1. Qwen3-8B-Instruct — Gyors segéd (MINDIG memóriában)

| Paraméter | Érték |
|-----------|-------|
| Kvantálás | Q5_K_M GGUF |
| Méret | ~6 GB |
| Hol fut | **P4000 GPU — TELJESEN VRAM-ban** |
| Sebesség | **~80-120 tok/s** |
| Feladatok | Összefoglalás, tömörítés, formázás, egyszerű kód, fájllista, kontextus szűrés |
| Forrás | `https://huggingface.co/bartowski/Qwen3-8B-GGUF` |

### 2. Qwen3-32B-Instruct — Komoly segéd (MINDIG memóriában)

| Paraméter | Érték |
|-----------|-------|
| Kvantálás | Q4_K_M GGUF |
| Méret | ~20 GB |
| Hol fut | **GPU offload (15-20 réteg P4000) + CPU** |
| Sebesség | **~15-20 tok/s** |
| Feladatok | Kódrevízió, script generálás, RAG válasz, hibakeresés, repó-elemzés |
| Forrás | `https://huggingface.co/bartowski/Qwen3-32B-GGUF` |

### 3. Qwen3.8-Flash-Next — Nehéz tüzérség (ON-DEMAND)

| Paraméter | Érték |
|-----------|-------|
| Kvantálás | Q3_K_M GGUF |
| Méret | ~55 GB |
| Hol fut | **CPU only (160GB RAM-ból)** |
| Sebesség | **~12-20 tok/s** (4-csatorna DDR4) |
| Feladatok | Komplex elemzés, képelemzés (multimodális), nagy kontextus |
| Forrás | `https://huggingface.co/bartowski/Qwen3.8-Flash-Next-GGUF` (community) |

### RAM eloszlás

```
160 GB RAM
├── Rendszer + desktop              ~8 GB
├── Qwen3-8B  (GPU VRAM, nem RAM)   ~0 GB RAM (6GB VRAM)
├── Qwen3-32B (CPU rész + kontextus) ~20 GB
├── Kontextus cache                 ~30 GB
├── Szabad (alap)                   ~102 GB
└── Flash-Next betöltéskor          ~55 GB → marad ~47 GB ✅ BEFÉR!
```

---

## Token routing — feladat kiosztás

| Feladat típus | Ki végzi | Sebesség | Cloud token? |
|---------------|----------|----------|-------------|
| Összefoglalás, tömörítés | Qwen3-8B GPU | ~100 tok/s | ❌ |
| Formázás, egyszerű kód | Qwen3-8B GPU | ~100 tok/s | ❌ |
| Fájllista, struktúra | Qwen3-8B GPU | ~100 tok/s | ❌ |
| Kódrevízió, script | Qwen3-32B GPU+CPU | ~18 tok/s | ❌ |
| RAG válasz, hibakeresés | Qwen3-32B GPU+CPU | ~18 tok/s | ❌ |
| Repó-elemzés | Qwen3-32B GPU+CPU | ~18 tok/s | ❌ |
| Komplex elemzés, kép | Flash-Next CPU | ~15 tok/s | ❌ |
| Architektúra döntés | **Cline (Cloud)** | API | ✅ |
| Kritikus biztonsági kód | **Cline (Cloud)** | API | ✅ |

**Cloud token csökkentés: ~70-80%**
**Megtérülés: 4-10 hónap**

---

## Implementációs lépések (RAM megérkezése után)

### Fázis 1: Alap infrastruktúra
1. RAM beszerelés — BIOS ellenőrzés (160GB, 4-csatorna)
2. llama.cpp build — CPU AVX2 + CUDA backend
3. Modellek letöltése `/data/models/`:
   - `qwen3-8b-instruct-q5_k_m.gguf` (~6GB)
   - `qwen3-32b-instruct-q4_k_m.gguf` (~20GB)
4. llama.cpp server indítás — Qwen3-8B P4000-n, Qwen3-32B GPU+CPU

### Fázis 2: MCP integráció
5. MCP `qwen_analyzer.py` átírás — GPU Qwen2.5-7B → llama.cpp API hívás
6. Feladat routing logika — egyszerű→8B, közepes→32B
7. Qwen2.5-Coder-7B GPU modell eltávolítható (helyettesítve)

### Fázis 3: Flash-Next (ha kell)
8. `qwen3.8-flash-next-q3_k_m.gguf` letöltés (~55GB)
9. On-demand betöltés logika (RAM-ba ha kell, ki ha nem)

---

## Megjegyzések

- A P4000 NEM eladandó — CUDA compute-re kell a gyors inferenciához
- A P2000 NEM eladandó — display GPU, X server fut rajta
- A PRIME stutter csak grafikánál volt (Heaven) — CUDA compute-ra NINCS hatása
- A `/data` partíción 188GB szabad — modellek tárolásra bőven elég
- A Qwen2.5-Coder-7B (jelenlegi MCP modell) lecserélődik a rétegzett rendszerre
