# Simple TP Címkézés — Végeredmény (Jó + Rossz label)

## Konfiguráció
- TP = $30, max = 18 bar (~5 perc)
- EMA = 20, TF = 300s (5m)
- Numba gyorsítás

## Label variációk

### Long modell (label_long: 1=jó, 0=rossz)
- Jó (TP hit): 196,036 (58.9%)
- Rossz (miss): 136,588 (41.1%)
- Avg bars to TP: 5.9 (~100s)

### Short modell (label_short: 1=jó, 0=rossz)
- Jó (TP hit): 197,437 (59.4%)
- Rossz (miss): 135,187 (40.6%)
- Avg bars to TP: 5.8 (~99s)

### Egy modell (label_combo: 2=jó_long, 1=jó_short, 0=rossz)
- Jó Long (2): 151,948 (45.7%)
- Jó Short (1): 151,437 (45.5%)
- Rossz (0): 29,239 (8.8%)
- **Megjegyzés**: 8.8% rossz = egyik irányba sem éri el a $30-ot 5 percen belül

### EMA filter (label_ema: 1=jó, 0=rossz, EMA side alapján)
- Jó: 213,072 (64.1%)
- Rossz: 119,537 (35.9%)
- **Info vs 50%: +14.1%**
- Napi WR: min=16.7% med=65.8% max=81.9%

## Modell variációk összefoglalás

1. **Két modell (Long + Short)**: Long WR=58.9%, Short WR=59.4%
   - Long modell tanít: feature → jó_long(1) / rossz_long(0)
   - Short modell tanít: feature → jó_short(1) / rossz_short(0)

2. **Egy modell (combo)**: 3 osztály (2=jó_long, 1=jó_short, 0=rossz)
   - 45.7% jó long, 45.5% jó short, 8.8% rossz

3. **EMA filter modell**: bináris (1=jó, 0=rossz) EMA side alapján
   - WR=64.1%, Info=+14.1% vs random

## Fájlok
- Script: `/data/dev/LGB_copilot_system/src/02_label_simple_tp.py`
- Output: `/data/dev/LGB_copilot_system/output/labeled_BTCUSD.csv`
- Config: SIMPLE_TP_DIST=30, SIMPLE_TP_MAX_BARS=18, SIMPLE_TP_EMA_PERIOD=20, SIMPLE_TP_EMA_RS_SEC=300

## CSV oszlopok
label_long, bars_held_long, label_short, bars_held_short, 
label_combo, ema_side, label_ema, bars_held_ema, side, label, bars_held, 
tp_dist, entry_price
