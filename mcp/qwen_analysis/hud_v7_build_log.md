# V7 HUD — Teszteredmények (2026-10-11)

## Építés lépésről lépésre

### Lépés 1: Knowledge Base tanulmányozás
- `hud_v5_cfd.py` — működő előd, 1 subchart, P(Long)+P(Short)
- `lightweight-charts-python` API:
  - `create_line(name='', ...)` — name=oszlopnév a DataFrame-ben! Üres=alapértelmezett
  - `legend(text='...', lines=False)` — statikus szöveg
  - `create_subchart(width=1, height=0.17, sync=True)` — több subchart
  - `horizontal_line.update(float)` — float-ot vár
  - `Line.update(pd.Series)` — Series-t vár, NEM float-ot!

### Lépés 2: Adatfelderítés (ZMQ sniffer)
- `signal: -1` (SHORT) átmegy ✅
- `p_long: 0.158`, `mlp_prob: 0.149`, `lgbm_prob: 0.179` — mind átjön ✅
- `bar_complete: MISSING` — csak bar completion üzenetben van ✅
- `feature_importance: present(27)` — átjön ✅

### Lépés 3: V7 HUD megírása
- 3 subchart: MLP | LGBM | ENS+Conf
- Legend text (nem name=)
- horizontal_line bid/ask (nem create_line)
- NoiseTracker csak bar_complete=True-kor
- Log minden bar completion-nél

### Lépés 4: Teszt eredmények
| Bar | MLP | LGBM | ENS | conf | sig | MLP σ | LGBM σ | ENS σ |
|-----|------|------|------|------|-----|-------|--------|-------|
| 1 | 0.2409 | 0.2395 | 0.2405 | 0.519 | -1 | — | — | — |
| 2 | 0.1420 | 0.1600 | 0.1474 | 0.705 | -1 | 0.050 | 0.040 | 0.047 |
| 3 | 0.2165 | 0.3839 | 0.2667 | 0.467 | -1 | 0.042 | 0.093 | 0.051 |
| 4 | 0.3030 | 0.4397 | 0.3440 | 0.312 | -1 | 0.058 | 0.111 | 0.070 |
| 5 | 0.2342 | 0.4209 | 0.2902 | 0.420 | -1 | 0.052 | 0.110 | 0.065 |
| 6 | 0.3121 | 0.4377 | 0.3498 | 0.301 | -1 | 0.057 | 0.108 | 0.069 |
| 7 | 0.2825 | 0.2562 | 0.2746 | 0.451 | -1 | 0.055 | 0.105 | 0.063 |

### Diagnózis
- MLP tartomány: 0.14-0.31 (szűk, stabil, σ≈0.05)
- LGBM tartomány: 0.16-0.44 (szélesebb, σ≈0.11)
- ENS tartomány: 0.15-0.35 (kiegyenlített, σ≈0.06)
- Mindig < 0.5 → SHORT domináns
- Signal mindig -1 ✅
- Nincs crash, nincs error

### Bugfix-ek
1. `create_line(name='MLP P(Long)')` → `NameError: No column named "MLP P(Long)"`
   - Megoldás: `name=''` + `legend(text='MLP P(Long)')`
2. `bid_line = create_line()` → `Line.update(float)` crash: `'float' object has no attribute 'copy'`
   - Megoldás: `bid_line = horizontal_line()` (float.update() működik)
