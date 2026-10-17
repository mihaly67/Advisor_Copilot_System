# Session: hardware_upgrade_plan_20260920
*Időbélyeg: 2026-09-20T12:57:19.802665*

HARDVER FEJLESZTÉSI TERV rögzítve 2026.09.20

VÁSÁRLÁS: 4×32GB DDR4 ECC 2133 MT/s (~90-120 eFt)
CÉL: 32GB → 160GB RAM, 4-csatorna MAX sávszélesség
SSD/NVMe: NEM KELL (/data 188GB szabad)

ARCHITEKTÚRA a frissítés után:
- P4000 (8GB VRAM): CUDA compute — Qwen3-8B TELJESEN GPU-n (~100 tok/s)
- P2000 (5GB VRAM): Display only
- CPU 160GB RAM: Qwen3-32B GPU+CPU (~18 tok/s), Flash-Next Q3_K_M on-demand (~15 tok/s)

HÁROM MODELL:
1. Qwen3-8B Q5_K_M — gyors segéd (mindig GPU-n)
2. Qwen3-32B Q4_K_M — komoly segéd (GPU offload + CPU)
3. Qwen3.8-Flash-Next Q3_K_M — nehéz tüzérség (on-demand CPU)

TOKEN CSÖKKENÉS: ~70-80% cloud token → 4-10 hónap megtérülés
Qwen2.5-Coder-7B GPU → lecserélődik a rétegzett rendszerre

STÁTUSZ: VÁRAKOZÓ — felhasználó jelzi ha RAM rendelkezésre áll