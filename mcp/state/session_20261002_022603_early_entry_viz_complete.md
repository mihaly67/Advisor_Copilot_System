# Session: early_entry_viz_complete
*Időbélyeg: 2026-10-02T02:26:03.198918*

EARLY ENTRY TESZT + VIZUALIZÁCIÓ KÉSZ — 2026-10-01

## KORAI BELÉPÉS TESZT EREDMÉNYEK

### Út A: 3-periódusú indikátorok
- Feature lag tényleg -1 (Slope_Close_3: lagA r=0.71!)
- DE modell P(Long) lag=-8 marad — LightGBM lassú feature-öket preferál
- Profit: 10,441 ≈ baseline — NINCS javulás

### Út B: Label shift +N
| Shift | WR | Profit | P(L) Lag | Fwd1 | Fwd!5 |
|---|---|---|---|---|---|
| +0 | 61.0% | 10,446 | -8 | 48.1% | 48.2% |
| +2 | 54.4% | 8,060 | -6 | 49.1% | 48.6% |
| +4 | 48.1% | 5,674 | -4 | 50.6% | 48.8% |
| +6 | 41.9% | 3,295 | -3 | 50.7% | 50.2% |
| +8 | 36.0% | 1,020 | -2 | 52.8% | 50.9% |

### Kompromisszum: +2 = lag=-6 de WR=54% (még >50%)
### +4 már túl messze: WR=48% ≈ véletlen

### VIZUALIZÁCIÓ: Label shift +2
- /data/dev/projects/z-ai-copilot/docs/v106/viz_label_shift_plus2.html (353 KB)
- Szürke háromszög = baseline, Zöld/Piros = shift+2
- Sárga rombus = "korábban" belépések (89 Long + 89 Short)
- Panel 2: Base P(L) szürke vs Shift+2 P(L) zöld

### Fájlok:
- /data/dev/projects/z-ai-copilot/src/early_entry_test.py
- /data/dev/projects/z-ai-copilot/src/viz_label_shift.py
- /data/dev/projects/z-ai-copGopilot/models/v106/early_entry_results.json